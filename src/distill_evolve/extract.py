"""Run LLM extraction over top-scored artifacts; persist JSON extractions."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Callable

from pydantic import ValidationError

from distill_core.blob import load_blob_text as core_load_blob_text
from distill_core.config import DATA_DIR, DB_PATH, llm_model
from distill_core.db import connect, insert_extraction
from distill_core.llm import complete, extract_json
from distill_core.prompts import load_role_prompt, render_role_prompt
from distill_core.roles import SUPPORTED_ROLES
from distill_core.schemas import Extraction

from .artifact_cards import build_artifact_card, render_supporting_artifacts_text
from .score import select_extraction_candidates


def _parse_json(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    try:
        data = json.loads(value)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _read_blob_text(blob_path: str | None, *, blobs_dir: Path | None = None) -> str:
    if not blob_path:
        return ""
    if blobs_dir is None:
        return core_load_blob_text(blob_path)
    return (blobs_dir / Path(blob_path)).read_text(encoding="utf-8")


def _load_supporting_artifacts(
    conn,
    *,
    artifact_id: int,
    blobs_dir: Path | None = None,
) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT a.*, l.link_type, l.confidence
        FROM links l
        JOIN artifacts a
          ON a.id = CASE
              WHEN l.source_id = ? THEN l.target_id
              ELSE l.source_id
            END
        WHERE l.source_id = ? OR l.target_id = ?
        ORDER BY l.confidence DESC, a.kind ASC, a.id ASC
        """,
        (artifact_id, artifact_id, artifact_id),
    ).fetchall()
    supporting: list[dict[str, Any]] = []
    for row in rows:
        supporting.append(
            {
                "artifact_id": row["id"],
                "kind": row["kind"],
                "external_id": row["external_id"],
                "link_type": row["link_type"],
                "confidence": row["confidence"],
                "updated_at": row["updated_at"],
                "metadata": _parse_json(row["metadata"]),
                "blob_text": _read_blob_text(row["blob_path"], blobs_dir=blobs_dir),
                "context": _load_artifact_context(
                    conn,
                    artifact_id=int(row["id"]),
                    kind=str(row["kind"]),
                ),
            }
        )
    return supporting


def _load_artifact_context(conn, *, artifact_id: int, kind: str) -> dict[str, Any]:
    if kind != "jira_issue":
        return {}
    rows = conn.execute(
        """
        SELECT event_kind, from_value, to_value, occurred_at
        FROM jira_events
        WHERE issue_id = ?
        ORDER BY occurred_at ASC, id ASC
        """,
        (artifact_id,),
    ).fetchall()
    return {"jira_events": [dict(row) for row in rows]}


def extract_one(
    *,
    role: str,
    artifact_row,
    artifact_card: str,
    supporting_artifacts: list[dict[str, Any]],
    llm_callable: Callable[..., str] = complete,
    model: str | None = None,
) -> Extraction:
    artifact_json = {
        "artifact_id": artifact_row["id"],
        "kind": artifact_row["kind"],
        "external_id": artifact_row["external_id"],
        "updated_at": artifact_row["updated_at"],
        "supporting_artifact_count": len(supporting_artifacts),
    }
    system_prompt = load_role_prompt(role, "extract.system.md")
    user_prompt = render_role_prompt(
        role,
        "extract.user.md",
        artifact_json=json.dumps(artifact_json, ensure_ascii=False, indent=2, sort_keys=True),
        artifact_card=artifact_card,
        supporting_artifacts_text=render_supporting_artifacts_text(supporting_artifacts),
    )
    raw = llm_callable(
        system=system_prompt,
        user=user_prompt,
        max_tokens=2000,
        temperature=0.0,
        model=model,
    )
    payload = extract_json(raw)
    if not isinstance(payload, dict):
        raise ValueError("LLM response did not decode to a JSON object.")
    payload["artifact_id"] = artifact_row["id"]
    return Extraction.model_validate(payload)


def _append_failure(failure_log_path: Path, payload: dict[str, Any]) -> None:
    failure_log_path.parent.mkdir(parents=True, exist_ok=True)
    with failure_log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def run_extraction(
    *,
    role: str,
    db_path: Path = DB_PATH,
    blobs_dir: Path | None = None,
    limit: int = 50,
    llm_callable: Callable[..., str] = complete,
    failure_log_path: Path | None = None,
    model: str | None = None,
) -> dict[str, int]:
    summary = {"processed": 0, "inserted": 0, "failed": 0, "skipped": 0}
    failure_path = failure_log_path or DATA_DIR / "extract_failures.jsonl"
    model_name = model or llm_model()

    with connect(db_path) as conn:
        candidates = select_extraction_candidates(conn, role=role)[:limit]
        for artifact_row in candidates:
            existing = conn.execute(
                "SELECT id FROM extractions WHERE artifact_id = ? AND role = ?",
                (artifact_row["id"], role),
            ).fetchone()
            if existing:
                summary["skipped"] += 1
                continue

            blob_text = _read_blob_text(artifact_row["blob_path"], blobs_dir=blobs_dir)
            supporting = _load_supporting_artifacts(
                conn,
                artifact_id=int(artifact_row["id"]),
                blobs_dir=blobs_dir,
            )
            summary["processed"] += 1
            artifact_card = ""
            try:
                metadata = _parse_json(artifact_row["metadata"])
                artifact_card = build_artifact_card(
                    artifact_id=int(artifact_row["id"]),
                    kind=str(artifact_row["kind"]),
                    external_id=str(artifact_row["external_id"]),
                    metadata=metadata,
                    blob_text=blob_text,
                    updated_at=artifact_row["updated_at"],
                    linked_artifacts=[item["external_id"] for item in supporting],
                    artifact_context=_load_artifact_context(
                        conn,
                        artifact_id=int(artifact_row["id"]),
                        kind=str(artifact_row["kind"]),
                    ),
                )
                extraction = extract_one(
                    role=role,
                    artifact_row=artifact_row,
                    artifact_card=artifact_card,
                    supporting_artifacts=supporting,
                    llm_callable=llm_callable,
                    model=model_name,
                )
            except (json.JSONDecodeError, ValidationError, TypeError, ValueError) as exc:
                summary["failed"] += 1
                _append_failure(
                    failure_path,
                    {
                        "artifact_id": artifact_row["id"],
                        "kind": artifact_row["kind"],
                        "external_id": artifact_row["external_id"],
                        "error": str(exc),
                        "artifact_card_preview": artifact_card[:400] if artifact_card else "",
                    },
                )
                continue

            insert_extraction(
                conn,
                artifact_id=int(artifact_row["id"]),
                role=role,
                payload=extraction.model_dump(),
                llm_model=model_name,
            )
            summary["inserted"] += 1
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--role", required=True, choices=list(SUPPORTED_ROLES))
    parser.add_argument("--limit", type=int, default=50, help="Max top-scored artifacts to process")
    args = parser.parse_args()

    summary = run_extraction(role=args.role, limit=args.limit)
    print(
        "Processed {processed} artifacts, inserted {inserted}, failed {failed}, skipped {skipped}.".format(
            **summary
        )
    )


if __name__ == "__main__":
    main()
