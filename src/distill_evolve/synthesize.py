"""Synthesize one skill module per cluster; write packs/<role>/v0.1/skills/*.md."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import re
from typing import Any, Callable

import yaml

from distill_core.config import (
    DB_PATH,
    PACKS_DIR,
    default_ingest_since,
    default_ingest_until,
    llm_model,
)
from distill_core.db import connect
from distill_core.llm import complete
from distill_core.prompts import load_role_prompt
from distill_core.roles import SUPPORTED_ROLES, get_role_config, normalize_cluster_name


def _parse_json(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    try:
        data = json.loads(value)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return re.sub(r"-{2,}", "-", slug)


def _load_clusters(conn, *, role: str):
    return conn.execute(
        """
        SELECT c.*, COUNT(e.id) AS extraction_count
        FROM clusters c
        LEFT JOIN extractions e ON e.cluster_id = c.id AND e.role = c.role
        WHERE c.role = ?
        GROUP BY c.id
        ORDER BY extraction_count DESC, c.id ASC
        """,
        (role,),
    ).fetchall()


def _load_cluster_extractions(conn, *, cluster_id: int, role: str):
    return conn.execute(
        """
        SELECT e.*, a.external_id, a.metadata, s.score
        FROM extractions e
        JOIN artifacts a ON a.id = e.artifact_id
        JOIN scores s ON s.artifact_id = e.artifact_id
        WHERE e.cluster_id = ? AND e.role = ? AND s.role = ?
        ORDER BY s.score DESC, e.id ASC
        """,
        (cluster_id, role, role),
    ).fetchall()


def _cluster_payload(cluster_row, extraction_rows, *, module_slug: str) -> dict[str, Any]:
    role_config = get_role_config(cluster_row["role"])
    return {
        "role": cluster_row["role"],
        "writing_preferences": role_config.writing_preferences,
        "cluster": {
            "id": cluster_row["id"],
            "name": cluster_row["name"],
            "description": cluster_row["description"] or "",
            "module_slug": module_slug,
            "module_title": role_config.target_modules.get(module_slug, cluster_row["name"]),
        },
        "extractions": [
            {
                "extraction_id": row["id"],
                "artifact_id": row["artifact_id"],
                "score": row["score"],
                "artifact_external_id": row["external_id"],
                "artifact_metadata": _parse_json(row["metadata"]),
                "payload": _parse_json(row["payload"]),
            }
            for row in extraction_rows
        ],
    }


def _ensure_sentence(text: str) -> str:
    stripped = text.strip()
    if not stripped:
        return stripped
    if stripped.endswith((".", "!", "?")):
        return stripped
    return f"{stripped}."


def _collect_rule_candidates(module_rows: dict[str, list[Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for extraction_rows in module_rows.values():
        for row in extraction_rows:
            payload = _parse_json(row["payload"])
            artifact_id = int(row["artifact_id"])
            for pattern in payload.get("patterns", []):
                if not isinstance(pattern, dict):
                    continue
                summary = str(pattern.get("summary") or "").strip()
                if not summary:
                    continue
                key = _slugify(summary) or summary.lower()
                entry = grouped.setdefault(
                    key,
                    {
                        "summary": _ensure_sentence(summary),
                        "sources": set(),
                    },
                )
                entry["sources"].add(artifact_id)

    ordered = sorted(
        grouped.values(),
        key=lambda item: (-len(item["sources"]), item["summary"].lower()),
    )
    repeated = [item for item in ordered if len(item["sources"]) >= 2]
    return repeated[:8]


def _build_manifest(
    *,
    role: str,
    module_rows: dict[str, list[Any]],
    written_modules: list[Path],
) -> str:
    role_config = get_role_config(role)
    lines = [f"# {role} - Skill Pack Manifest (v0.1)", "", *role_config.manifest_intro, "", "## Hard rules"]

    rule_candidates = _collect_rule_candidates(module_rows)
    if rule_candidates:
        for candidate in rule_candidates:
            citations = ", ".join(str(source_id) for source_id in sorted(candidate["sources"])[:4])
            lines.append(f"- {candidate['summary']} [src: {citations}]")
    else:
        source_ids = {
            int(row["artifact_id"])
            for extraction_rows in module_rows.values()
            for row in extraction_rows
        }
        if source_ids:
            lines.append(
                "Chưa có đủ bằng chứng lặp lại để nâng thành hard rule cấp pack. "
                "Hãy dùng trực tiếp các module đã sinh cho guidance theo task."
            )
        else:
            lines.append("Chưa có bằng chứng đã tổng hợp cho role này.")

    lines.extend(["", "## Skill modules", "", "| Module | Load when |", "|---|---|"])
    for module_path in sorted(written_modules, key=lambda path: path.name):
        hint = role_config.module_hints.get(
            module_path.stem,
            "Nạp khi task khớp với tên hoặc intent của module này.",
        )
        lines.append(f"| skills/{module_path.name} | {hint} |")
    lines.append("")
    return "\n".join(lines)


def _count_contributors(conn, *, role: str) -> int:
    rows = conn.execute(
        """
        SELECT a.metadata
        FROM artifacts a
        JOIN scores s ON s.artifact_id = a.id
        WHERE s.role = ?
        """,
        (role,),
    ).fetchall()
    contributors: set[str] = set()
    keys = (
        "author_username",
        "author_email",
        "author_name",
        "merged_by_username",
        "merged_by",
        "reviewer_username",
        "updated_by",
        "assignee",
        "reporter",
    )
    for row in rows:
        metadata = _parse_json(row["metadata"])
        for key in keys:
            value = metadata.get(key)
            if value:
                contributors.add(str(value).strip().lower())
        author = metadata.get("author")
        if isinstance(author, str) and author.strip():
            contributors.add(author.strip().lower())
        if isinstance(author, dict):
            for key in ("username", "email", "name"):
                value = author.get(key)
                if value:
                    contributors.add(str(value).strip().lower())
    return len(contributors)


def _count_quality_signals(conn, *, role: str) -> dict[str, int]:
    source_artifacts = int(
        conn.execute(
            "SELECT COUNT(*) FROM scores WHERE role = ?",
            (role,),
        ).fetchone()[0]
    )
    filtered_in = int(
        conn.execute(
            """
            SELECT COUNT(DISTINCT e.artifact_id)
            FROM extractions e
            JOIN scores s ON s.artifact_id = e.artifact_id
            WHERE e.role = ? AND s.role = ?
            """,
            (role, role),
        ).fetchone()[0]
    )
    return {
        "source_artifacts": source_artifacts,
        "filtered_in": filtered_in,
        "filtered_out": max(0, source_artifacts - filtered_in),
    }


def _pack_checksum(manifest_text: str, module_paths: list[Path]) -> str:
    digest = hashlib.sha256()
    digest.update(manifest_text.encode("utf-8"))
    for module_path in sorted(module_paths, key=lambda path: path.name):
        digest.update(module_path.name.encode("utf-8"))
        digest.update(module_path.read_bytes())
    return f"sha256:{digest.hexdigest()}"


def _write_pack_files(
    *,
    conn,
    role: str,
    packs_dir: Path,
    written_modules: list[Path],
    module_rows: dict[str, list[Any]],
    model_name: str,
) -> tuple[Path, Path]:
    pack_root = packs_dir / role / "v0.1"
    pack_root.mkdir(parents=True, exist_ok=True)
    role_config = get_role_config(role)

    manifest_text = _build_manifest(
        role=role,
        module_rows=module_rows,
        written_modules=written_modules,
    )
    manifest_path = pack_root / "manifest.md"
    manifest_path.write_text(manifest_text, encoding="utf-8")

    quality_signals = _count_quality_signals(conn, role=role)
    quality_signals["modules_generated"] = len(written_modules)
    pack_yaml_path = pack_root / "pack.yaml"
    pack_yaml_path.write_text(
        yaml.safe_dump(
            {
                "role": role,
                "version": "v0.1",
                "language": role_config.writing_preferences["primary_language"],
                "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "source_window": f"{default_ingest_since()}..{default_ingest_until()}",
                "contributors": _count_contributors(conn, role=role),
                "quality_signals": quality_signals,
                "checksum": _pack_checksum(manifest_text, written_modules),
                "llm_model": model_name,
            },
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return manifest_path, pack_yaml_path


def synthesize_module(
    *,
    role: str,
    cluster_row,
    extraction_rows,
    module_slug: str,
    llm_callable: Callable[..., str] = complete,
    model: str | None = None,
) -> str | None:
    payload = _cluster_payload(cluster_row, extraction_rows, module_slug=module_slug)
    response = llm_callable(
        system=load_role_prompt(role, "synthesize.system.md"),
        user=json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
        max_tokens=4000,
        temperature=0.0,
        model=model,
    ).strip()
    if not response:
        return None
    if response.startswith("{"):
        try:
            parsed = json.loads(response)
        except json.JSONDecodeError:
            return response
        if parsed.get("error") == "insufficient_evidence":
            return None
    return response


def synthesize_role(
    *,
    role: str,
    db_path: Path = DB_PATH,
    packs_dir: Path = PACKS_DIR,
    llm_callable: Callable[..., str] = complete,
    model: str | None = None,
) -> dict[str, list[Any]]:
    written: list[Path] = []
    skipped: list[dict[str, Any]] = []
    module_rows: dict[str, list[Any]] = {}
    model_name = model or llm_model()

    with connect(db_path) as conn:
        for cluster_row in _load_clusters(conn, role=role):
            module_slug = normalize_cluster_name(
                role,
                cluster_row["name"],
                cluster_row["description"] or "",
            )
            if module_slug is None:
                skipped.append({"cluster": cluster_row["name"], "reason": "unsupported_cluster"})
                continue
            if module_slug in {path.stem for path in written}:
                skipped.append({"cluster": cluster_row["name"], "reason": "duplicate_module"})
                continue
            extraction_rows = _load_cluster_extractions(
                conn, cluster_id=int(cluster_row["id"]), role=role
            )
            if not extraction_rows:
                skipped.append({"cluster": cluster_row["name"], "reason": "no_extractions"})
                continue
            module_text = synthesize_module(
                role=role,
                cluster_row=cluster_row,
                extraction_rows=extraction_rows,
                module_slug=module_slug,
                llm_callable=llm_callable,
                model=model_name,
            )
            if not module_text:
                skipped.append({"cluster": cluster_row["name"], "reason": "insufficient_evidence"})
                continue
            module_path = packs_dir / role / "v0.1" / "skills" / f"{module_slug}.md"
            module_path.parent.mkdir(parents=True, exist_ok=True)
            module_path.write_text(module_text, encoding="utf-8")
            written.append(module_path)
            module_rows[module_slug] = extraction_rows

        manifest_path: Path | None = None
        pack_yaml_path: Path | None = None
        if written:
            manifest_path, pack_yaml_path = _write_pack_files(
                conn=conn,
                role=role,
                packs_dir=packs_dir,
                written_modules=written,
                module_rows=module_rows,
                model_name=model_name,
            )
    return {
        "written": written,
        "skipped": skipped,
        "manifest": manifest_path,
        "pack_yaml": pack_yaml_path,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--role", required=True, choices=list(SUPPORTED_ROLES))
    args = parser.parse_args()

    summary = synthesize_role(role=args.role)
    print(f"Wrote {len(summary['written'])} modules and skipped {len(summary['skipped'])}.")


if __name__ == "__main__":
    main()
