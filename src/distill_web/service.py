"""Read-only query and view-model layer for the Distill dashboard."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import sqlite3
from typing import Any

import yaml

from distill_core.db import connect
from distill_core.roles import SUPPORTED_ROLES, get_role_config
from distill_evolve.validate import validate_role_pack

SOURCE_LABELS = {
    "gitlab_mr": "GitLab",
    "jira_issue": "Jira",
    "confluence_page": "Confluence",
}

METRIC_ACCENTS = (
    "#0f6d6d",
    "#b86835",
    "#284c7f",
    "#b8504f",
)

STAGE_LABELS = {
    "ingest": "Ingest",
    "link": "Link",
    "score": "Score",
    "extract": "Extract",
    "cluster": "Cluster",
    "synthesize": "Synthesize",
    "validate": "Validate",
}

STAGE_DESCRIPTIONS = {
    "ingest": "Source artifacts currently persisted in SQLite.",
    "link": "Deterministic links across the current artifact graph.",
    "score": "Role-scoped scoring results available for candidate selection.",
    "extract": "Persisted LLM extractions for the current role.",
    "cluster": "Current assignment coverage from extractions into clusters.",
    "synthesize": "Pack files written under packs/<role>/v0.1/.",
    "validate": "Latest pack validity as computed from the real validation rules.",
}

STATE_LABELS = {
    "ready": "Ready",
    "partial": "Partial",
    "empty": "Empty",
    "missing": "Missing",
}

STATE_TONES = {
    "ready": "ok",
    "partial": "warn",
    "empty": "muted",
    "missing": "critical",
}


@dataclass(frozen=True)
class DashboardConfig:
    db_path: Path
    packs_dir: Path


class DashboardError(RuntimeError):
    """Base error for dashboard queries."""


class NotFoundError(DashboardError):
    """Raised when a requested record does not exist."""


def _parse_json(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    try:
        payload = json.loads(value)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _parse_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _role_label(role: str) -> str:
    return role.replace("-", " ").title()


def _source_label(kind: str) -> str:
    return SOURCE_LABELS.get(kind, kind)


def _default_config(
    db_path: Path | None = None,
    packs_dir: Path | None = None,
) -> DashboardConfig:
    from distill_core.config import DB_PATH, PACKS_DIR

    return DashboardConfig(
        db_path=db_path or DB_PATH,
        packs_dir=packs_dir or PACKS_DIR,
    )


def _ensure_role(role: str) -> None:
    if role not in SUPPORTED_ROLES:
        raise ValueError(f"Unsupported role: {role}")


def _count(conn: sqlite3.Connection, query: str, params: tuple[Any, ...] = ()) -> int:
    row = conn.execute(query, params).fetchone()
    return int(row[0] or 0) if row is not None else 0


def _load_global_source_health(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT kind, COUNT(*) AS item_count,
               MAX(COALESCE(ingested_at, updated_at, created_at)) AS latest_timestamp
        FROM artifacts
        GROUP BY kind
        ORDER BY kind
        """
    ).fetchall()
    by_kind = {
        str(row["kind"]): {
            "kind": str(row["kind"]),
            "label": _source_label(str(row["kind"])),
            "count": int(row["item_count"] or 0),
            "latestTimestamp": row["latest_timestamp"],
        }
        for row in rows
    }
    result: list[dict[str, Any]] = []
    for kind in ("gitlab_mr", "jira_issue", "confluence_page"):
        result.append(
            by_kind.get(
                kind,
                {
                    "kind": kind,
                    "label": _source_label(kind),
                    "count": 0,
                    "latestTimestamp": None,
                },
            )
        )
    return result


def _count_primary_artifacts(conn: sqlite3.Connection, role: str) -> int:
    config = get_role_config(role)
    placeholders = ", ".join("?" for _ in config.primary_artifact_kinds)
    return _count(
        conn,
        f"SELECT COUNT(*) FROM artifacts WHERE kind IN ({placeholders})",
        config.primary_artifact_kinds,
    )


def _count_role_scores(conn: sqlite3.Connection, role: str) -> int:
    return _count(conn, "SELECT COUNT(*) FROM scores WHERE role = ?", (role,))


def _count_positive_scores(conn: sqlite3.Connection, role: str) -> int:
    return _count(conn, "SELECT COUNT(*) FROM scores WHERE role = ? AND score > 0", (role,))


def _count_role_extractions(conn: sqlite3.Connection, role: str) -> int:
    return _count(conn, "SELECT COUNT(*) FROM extractions WHERE role = ?", (role,))


def _count_assigned_extractions(conn: sqlite3.Connection, role: str) -> int:
    return _count(
        conn,
        """
        SELECT COUNT(*)
        FROM extractions
        WHERE role = ? AND cluster_id IS NOT NULL
        """,
        (role,),
    )


def _count_role_clusters(conn: sqlite3.Connection, role: str) -> int:
    return _count(conn, "SELECT COUNT(*) FROM clusters WHERE role = ?", (role,))


def _count_linked_primary_artifacts(conn: sqlite3.Connection, role: str) -> int:
    config = get_role_config(role)
    placeholders = ", ".join("?" for _ in config.primary_artifact_kinds)
    return _count(
        conn,
        f"""
        WITH linked_artifacts AS (
          SELECT source_id AS artifact_id FROM links
          UNION
          SELECT target_id AS artifact_id FROM links
        )
        SELECT COUNT(DISTINCT linked_artifacts.artifact_id)
        FROM linked_artifacts
        JOIN artifacts a ON a.id = linked_artifacts.artifact_id
        WHERE a.kind IN ({placeholders})
        """,
        config.primary_artifact_kinds,
    )


def _latest_role_timestamp(
    conn: sqlite3.Connection,
    *,
    table: str,
    column: str,
    role: str,
) -> str | None:
    row = conn.execute(
        f"SELECT MAX({column}) AS latest_value FROM {table} WHERE role = ?",
        (role,),
    ).fetchone()
    return str(row["latest_value"]) if row and row["latest_value"] else None


def _load_cluster_names(conn: sqlite3.Connection, role: str) -> list[str]:
    return [
        str(row["name"])
        for row in conn.execute(
            "SELECT name FROM clusters WHERE role = ? ORDER BY name COLLATE NOCASE ASC",
            (role,),
        ).fetchall()
    ]


def _load_pack_summary(role: str, packs_dir: Path) -> dict[str, Any]:
    pack_root = packs_dir / role / "v0.1"
    manifest_path = pack_root / "manifest.md"
    metadata_path = pack_root / "pack.yaml"
    skills_dir = pack_root / "skills"
    module_paths = sorted(skills_dir.glob("*.md")) if skills_dir.exists() else []
    metadata = _parse_yaml(metadata_path)
    quality_signals = metadata.get("quality_signals")
    quality_signals = quality_signals if isinstance(quality_signals, dict) else {}

    return {
        "available": manifest_path.exists() and metadata_path.exists(),
        "role": role,
        "label": _role_label(role),
        "version": str(metadata.get("version") or "v0.1"),
        "language": metadata.get("language"),
        "generatedAt": metadata.get("generated_at"),
        "sourceWindow": metadata.get("source_window"),
        "contributors": int(metadata.get("contributors") or 0),
        "sourceArtifacts": int(quality_signals.get("source_artifacts") or 0),
        "filteredIn": int(quality_signals.get("filtered_in") or 0),
        "filteredOut": int(quality_signals.get("filtered_out") or 0),
        "modulesGenerated": int(quality_signals.get("modules_generated") or len(module_paths)),
        "moduleCount": len(module_paths),
        "moduleNames": [path.stem for path in module_paths],
        "llmModel": metadata.get("llm_model"),
    }


def _load_validation_summary(role: str, packs_dir: Path) -> dict[str, Any]:
    result = validate_role_pack(role=role, packs_dir=packs_dir)
    errors = [str(item) for item in result["errors"]]
    return {
        "ok": bool(result["ok"]),
        "errorCount": len(errors),
        "errors": errors,
        "moduleCount": len(result["modules"]),
        "totalTokens": int(result["total_tokens"]),
    }


def _stage_payload(
    key: str,
    *,
    state: str,
    summary: str,
    facts: list[str],
) -> dict[str, Any]:
    return {
        "key": key,
        "label": STAGE_LABELS[key],
        "description": STAGE_DESCRIPTIONS[key],
        "state": state,
        "stateLabel": STATE_LABELS[state],
        "tone": STATE_TONES[state],
        "summary": summary,
        "facts": facts,
    }


def list_roles(
    *,
    db_path: Path | None = None,
    packs_dir: Path | None = None,
) -> list[dict[str, Any]]:
    config = _default_config(db_path, packs_dir)
    with connect(config.db_path) as conn:
        roles: list[dict[str, Any]] = []
        for role in SUPPORTED_ROLES:
            pack_summary = _load_pack_summary(role, config.packs_dir)
            score_count = _count_role_scores(conn, role)
            extraction_count = _count_role_extractions(conn, role)
            cluster_count = _count_role_clusters(conn, role)
            positive_score_count = _count_positive_scores(conn, role)
            primary_artifact_count = _count_primary_artifacts(conn, role)
            if (
                score_count == 0
                and extraction_count == 0
                and cluster_count == 0
                and primary_artifact_count == 0
                and not pack_summary["available"]
            ):
                continue
            roles.append(
                {
                    "role": role,
                    "label": _role_label(role),
                    "primarySources": [
                        _source_label(kind) for kind in get_role_config(role).primary_artifact_kinds
                    ],
                    "primaryArtifactCount": primary_artifact_count,
                    "scoreCount": score_count,
                    "positiveScoreCount": positive_score_count,
                    "extractionCount": extraction_count,
                    "clusterCount": cluster_count,
                    "packAvailable": pack_summary["available"],
                    "moduleCount": pack_summary["moduleCount"],
                }
            )
        return roles


def get_health(
    *,
    db_path: Path | None = None,
    packs_dir: Path | None = None,
) -> dict[str, Any]:
    config = _default_config(db_path, packs_dir)
    source_counts: dict[str, int] = {}
    with connect(config.db_path) as conn:
        for item in _load_global_source_health(conn):
            source_counts[item["kind"]] = item["count"]
    return {
        "ok": True,
        "dbExists": config.db_path.exists(),
        "packsExists": config.packs_dir.exists(),
        "availableRoles": [
            item["role"] for item in list_roles(db_path=config.db_path, packs_dir=config.packs_dir)
        ],
        "sourceCounts": source_counts,
    }


def get_overview(
    role: str,
    *,
    db_path: Path | None = None,
    packs_dir: Path | None = None,
) -> dict[str, Any]:
    _ensure_role(role)
    config = _default_config(db_path, packs_dir)
    with connect(config.db_path) as conn:
        source_health = _load_global_source_health(conn)
        pack_summary = _load_pack_summary(role, config.packs_dir)
        validation = _load_validation_summary(role, config.packs_dir)
        primary_artifact_count = _count_primary_artifacts(conn, role)
        positive_score_count = _count_positive_scores(conn, role)
        score_count = _count_role_scores(conn, role)
        extraction_count = _count_role_extractions(conn, role)
        assigned_extractions = _count_assigned_extractions(conn, role)
        cluster_count = _count_role_clusters(conn, role)
        linked_primary_count = _count_linked_primary_artifacts(conn, role)
        total_link_count = _count(conn, "SELECT COUNT(*) FROM links")

    metrics = [
        {
            "label": "Primary artifacts",
            "value": str(primary_artifact_count),
            "meta": ", ".join(
                _source_label(kind) for kind in get_role_config(role).primary_artifact_kinds
            ),
            "accent": METRIC_ACCENTS[0],
        },
        {
            "label": "Positive-score queue",
            "value": str(positive_score_count),
            "meta": f"{score_count} scored artifacts for {role}",
            "accent": METRIC_ACCENTS[1],
        },
        {
            "label": "Live extractions",
            "value": str(extraction_count),
            "meta": f"{assigned_extractions} assigned into clusters",
            "accent": METRIC_ACCENTS[2],
        },
        {
            "label": "Pack modules",
            "value": str(pack_summary["moduleCount"]),
            "meta": f"Validation {'pass' if validation['ok'] else 'needs attention'}",
            "accent": METRIC_ACCENTS[3],
        },
    ]

    alerts: list[dict[str, Any]] = []
    if primary_artifact_count > 0 and linked_primary_count < primary_artifact_count:
        alerts.append(
            {
                "title": "Link coverage is still partial",
                "summary": f"{linked_primary_count}/{primary_artifact_count} primary artifacts are linked across sources ({total_link_count} total links).",
                "tone": "warn",
            }
        )
    if extraction_count > 0 and assigned_extractions < extraction_count:
        alerts.append(
            {
                "title": "Some extractions remain unclustered",
                "summary": f"{assigned_extractions}/{extraction_count} extractions are assigned to a cluster for {role}.",
                "tone": "warn",
            }
        )
    if not pack_summary["available"]:
        alerts.append(
            {
                "title": "Pack output is missing",
                "summary": f"No pack files were found under packs/{role}/v0.1.",
                "tone": "critical",
            }
        )
    elif not validation["ok"]:
        alerts.append(
            {
                "title": "Pack validation needs attention",
                "summary": validation["errors"][0],
                "tone": "critical",
            }
        )
    if not alerts:
        alerts.append(
            {
                "title": "Read-only snapshot is consistent",
                "summary": "Current web data is derived directly from SQLite and the generated pack files.",
                "tone": "info",
            }
        )

    source_items = [
        {
            "source": item["label"],
            "items": str(item["count"]),
            "freshness": item["latestTimestamp"] or "No artifacts yet",
            "note": (
                "Primary source for the selected role."
                if item["kind"] in get_role_config(role).primary_artifact_kinds
                else "Supporting source in the shared snapshot."
            ),
            "tone": "ok" if item["count"] > 0 else "muted",
        }
        for item in source_health
    ]

    snapshot_facts = [
        {"label": "Role", "value": _role_label(role)},
        {
            "label": "Primary sources",
            "value": ", ".join(
                _source_label(kind) for kind in get_role_config(role).primary_artifact_kinds
            ),
        },
        {"label": "Clusters", "value": str(cluster_count)},
        {"label": "Assigned extractions", "value": f"{assigned_extractions}/{extraction_count}"},
        {"label": "Source window", "value": str(pack_summary["sourceWindow"] or "Unknown")},
        {"label": "Generated at", "value": str(pack_summary["generatedAt"] or "Unknown")},
        {"label": "Contributors", "value": str(pack_summary["contributors"])},
        {"label": "LLM model", "value": str(pack_summary["llmModel"] or "Unknown")},
    ]

    validation_facts = [
        {"label": "Modules checked", "value": str(validation["moduleCount"])},
        {"label": "Token estimate", "value": str(validation["totalTokens"])},
        {"label": "Filtered in", "value": str(pack_summary["filteredIn"])},
        {"label": "Filtered out", "value": str(pack_summary["filteredOut"])},
    ]

    return {
        "role": role,
        "roleLabel": _role_label(role),
        "metrics": metrics,
        "alerts": alerts,
        "sourceHealth": source_items,
        "snapshotFacts": snapshot_facts,
        "validation": {
            **validation,
            "tone": "ok" if validation["ok"] else "critical",
            "label": "Validation pass" if validation["ok"] else "Validation errors",
            "facts": validation_facts,
        },
        "packSummary": pack_summary,
    }


def get_pipeline(
    role: str,
    *,
    db_path: Path | None = None,
    packs_dir: Path | None = None,
) -> dict[str, Any]:
    _ensure_role(role)
    config = _default_config(db_path, packs_dir)
    with connect(config.db_path) as conn:
        source_health = _load_global_source_health(conn)
        primary_artifact_count = _count_primary_artifacts(conn, role)
        linked_primary_count = _count_linked_primary_artifacts(conn, role)
        total_link_count = _count(conn, "SELECT COUNT(*) FROM links")
        score_count = _count_role_scores(conn, role)
        positive_score_count = _count_positive_scores(conn, role)
        extraction_count = _count_role_extractions(conn, role)
        assigned_extractions = _count_assigned_extractions(conn, role)
        cluster_count = _count_role_clusters(conn, role)
        cluster_names = _load_cluster_names(conn, role)
        latest_score_at = _latest_role_timestamp(
            conn, table="scores", column="scored_at", role=role
        )
        latest_extract_at = _latest_role_timestamp(
            conn, table="extractions", column="extracted_at", role=role
        )
        latest_cluster_at = _latest_role_timestamp(
            conn, table="clusters", column="created_at", role=role
        )
    pack_summary = _load_pack_summary(role, config.packs_dir)
    validation = _load_validation_summary(role, config.packs_dir)

    total_artifacts = sum(item["count"] for item in source_health)
    ingest_state = "ready" if total_artifacts > 0 else "empty"
    link_state = (
        "missing"
        if primary_artifact_count == 0
        else "empty"
        if linked_primary_count == 0
        else "partial"
        if linked_primary_count < primary_artifact_count
        else "ready"
    )
    score_state = "ready" if score_count > 0 else "empty"
    extract_state = "ready" if extraction_count > 0 else "empty"
    cluster_state = (
        "empty"
        if extraction_count == 0 and cluster_count == 0
        else "partial"
        if cluster_count == 0
        else "partial"
        if assigned_extractions < extraction_count
        else "ready"
    )
    synthesize_state = (
        "missing"
        if not pack_summary["available"]
        else "empty"
        if pack_summary["moduleCount"] == 0
        else "ready"
    )
    validate_state = (
        "missing" if not pack_summary["available"] else "ready" if validation["ok"] else "partial"
    )

    stages = [
        _stage_payload(
            "ingest",
            state=ingest_state,
            summary=f"{total_artifacts} artifacts are available in the current SQLite snapshot.",
            facts=[f"{item['label']} {item['count']}" for item in source_health],
        ),
        _stage_payload(
            "link",
            state=link_state,
            summary=f"{linked_primary_count}/{primary_artifact_count} primary artifacts are linked ({total_link_count} total links).",
            facts=[
                f"Primary artifacts {primary_artifact_count}",
                f"Linked primary {linked_primary_count}",
                f"Total links {total_link_count}",
            ],
        ),
        _stage_payload(
            "score",
            state=score_state,
            summary=f"{score_count} scored artifacts and {positive_score_count} positive-score candidates for {role}.",
            facts=[
                f"Positive queue {positive_score_count}",
                f"Latest score {latest_score_at or 'Unknown'}",
            ],
        ),
        _stage_payload(
            "extract",
            state=extract_state,
            summary=f"{extraction_count} persisted extractions are available for {role}.",
            facts=[
                f"Assigned {assigned_extractions}",
                f"Latest extract {latest_extract_at or 'Unknown'}",
            ],
        ),
        _stage_payload(
            "cluster",
            state=cluster_state,
            summary=f"{cluster_count} clusters with {assigned_extractions}/{extraction_count} assigned extractions.",
            facts=(
                [f"Latest cluster {latest_cluster_at or 'Unknown'}"]
                + [f"Cluster {name}" for name in cluster_names[:3]]
            ),
        ),
        _stage_payload(
            "synthesize",
            state=synthesize_state,
            summary=f"{pack_summary['moduleCount']} modules present under packs/{role}/v0.1.",
            facts=[
                f"Generated at {pack_summary['generatedAt'] or 'Unknown'}",
                f"Version {pack_summary['version']}",
                f"Filtered in {pack_summary['filteredIn']}",
            ],
        ),
        _stage_payload(
            "validate",
            state=validate_state,
            summary=(
                f"Validation passed at ~{validation['totalTokens']} tokens."
                if validation["ok"]
                else f"{validation['errorCount']} validation errors detected."
            ),
            facts=(
                [
                    f"Modules checked {validation['moduleCount']}",
                    f"Tokens {validation['totalTokens']}",
                ]
                if validation["ok"]
                else validation["errors"][:3]
            ),
        ),
    ]

    return {
        "role": role,
        "roleLabel": _role_label(role),
        "filters": [
            {"label": "Role", "value": _role_label(role)},
            {
                "label": "Primary sources",
                "value": ", ".join(
                    _source_label(kind) for kind in get_role_config(role).primary_artifact_kinds
                ),
            },
            {"label": "Scores", "value": str(score_count)},
            {"label": "Extractions", "value": str(extraction_count)},
            {"label": "Pack version", "value": str(pack_summary["version"])},
        ],
        "badges": [
            {"label": "Derived snapshot", "tone": "info"},
            {"label": "Read-only", "tone": "muted"},
        ],
        "stages": stages,
        "packSummary": pack_summary,
        "validation": validation,
        "commands": [
            "make web-api",
            "make web-dev",
            "",
            "make ingest",
            "make link",
            f"make score ROLE={role}",
            f"make extract ROLE={role}",
            f"make cluster ROLE={role}",
            f"make synthesize ROLE={role}",
            f"make validate ROLE={role}",
        ],
    }


def _review_title(kind: str, external_id: str, metadata: dict[str, Any]) -> str:
    if kind == "gitlab_mr":
        return str(metadata.get("title") or external_id)
    if kind == "jira_issue":
        return str(metadata.get("summary") or external_id)
    if kind == "confluence_page":
        return str(metadata.get("title") or external_id)
    return external_id


def _pattern_list(payload: dict[str, Any]) -> list[dict[str, Any]]:
    patterns = payload.get("patterns")
    if not isinstance(patterns, list):
        return []
    normalized: list[dict[str, Any]] = []
    for item in patterns:
        if not isinstance(item, dict):
            continue
        normalized.append(
            {
                "kind": str(item.get("kind") or "unknown"),
                "summary": str(item.get("summary") or ""),
                "evidenceExcerpt": str(item.get("evidence_excerpt") or ""),
                "confidence": float(item.get("confidence") or 0.0),
            }
        )
    return normalized


def _files_touched(payload: dict[str, Any]) -> list[str]:
    files = payload.get("files_touched")
    if not isinstance(files, list):
        return []
    return [str(item) for item in files if str(item).strip()]


def _domain_tags(payload: dict[str, Any]) -> list[str]:
    tags = payload.get("domain_tags")
    if not isinstance(tags, list):
        return []
    return [str(item) for item in tags if str(item).strip()]


def _linked_artifacts(conn: sqlite3.Connection, artifact_id: int) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        WITH related AS (
          SELECT target_id AS artifact_id, link_type, confidence
          FROM links
          WHERE source_id = ?
          UNION ALL
          SELECT source_id AS artifact_id, link_type, confidence
          FROM links
          WHERE target_id = ?
        )
        SELECT a.kind, a.external_id, a.metadata, related.link_type, related.confidence
        FROM related
        JOIN artifacts a ON a.id = related.artifact_id
        ORDER BY a.kind, a.external_id
        """,
        (artifact_id, artifact_id),
    ).fetchall()
    return [
        {
            "kind": str(row["kind"]),
            "label": _source_label(str(row["kind"])),
            "externalId": str(row["external_id"]),
            "title": _review_title(
                str(row["kind"]),
                str(row["external_id"]),
                _parse_json(row["metadata"]),
            ),
            "linkType": str(row["link_type"]),
            "confidence": float(row["confidence"] or 0.0),
        }
        for row in rows
    ]


def list_review_entries(
    role: str,
    *,
    query: str = "",
    source: str = "all",
    cluster: str = "all",
    limit: int = 50,
    offset: int = 0,
    db_path: Path | None = None,
    packs_dir: Path | None = None,
) -> dict[str, Any]:
    _ensure_role(role)
    config = _default_config(db_path, packs_dir)
    limit = max(1, min(limit, 200))
    offset = max(0, offset)
    normalized_query = query.strip().lower()
    source_filter = source.strip()
    cluster_filter = cluster.strip()

    sql_parts = [
        """
        SELECT e.id, e.artifact_id, e.role, e.payload, e.extracted_at,
               a.kind, a.external_id, a.metadata, a.updated_at,
               s.score, s.breakdown,
               c.name AS cluster_name
        FROM extractions e
        JOIN artifacts a ON a.id = e.artifact_id
        LEFT JOIN scores s ON s.artifact_id = e.artifact_id AND s.role = e.role
        LEFT JOIN clusters c ON c.id = e.cluster_id
        WHERE e.role = ?
        """
    ]
    params: list[Any] = [role]
    if normalized_query:
        sql_parts.append(
            """
            AND (
              LOWER(a.external_id) LIKE ?
              OR LOWER(a.kind) LIKE ?
              OR LOWER(COALESCE(c.name, '')) LIKE ?
              OR LOWER(e.payload) LIKE ?
            )
            """
        )
        search = f"%{normalized_query}%"
        params.extend([search, search, search, search])
    if source_filter and source_filter != "all":
        sql_parts.append("AND a.kind = ?")
        params.append(source_filter)
    if cluster_filter and cluster_filter != "all":
        sql_parts.append("AND COALESCE(c.name, '') = ?")
        params.append(cluster_filter)

    sql_parts.append("ORDER BY COALESCE(s.score, -999.0) DESC, e.id DESC")
    query_sql = "\n".join(sql_parts)
    with connect(config.db_path) as conn:
        rows = conn.execute(query_sql, tuple(params)).fetchall()
        visible_rows = rows[offset : offset + limit]
        cluster_names = _load_cluster_names(conn, role)
        total = len(rows)
        clustered_total = _count_assigned_extractions(conn, role)
        role_total = _count_role_extractions(conn, role)

    items: list[dict[str, Any]] = []
    for row in visible_rows:
        payload = _parse_json(row["payload"])
        metadata = _parse_json(row["metadata"])
        patterns = _pattern_list(payload)
        items.append(
            {
                "extractionId": int(row["id"]),
                "artifactId": int(row["artifact_id"]),
                "artifactExternalId": str(row["external_id"]),
                "title": _review_title(str(row["kind"]), str(row["external_id"]), metadata),
                "sourceKind": str(row["kind"]),
                "sourceLabel": _source_label(str(row["kind"])),
                "score": float(row["score"] or 0.0),
                "clusterName": str(row["cluster_name"]) if row["cluster_name"] else None,
                "taskType": str(payload.get("task_type") or "unknown"),
                "domainTags": _domain_tags(payload),
                "patternCount": len(patterns),
                "topPatternSummary": patterns[0]["summary"]
                if patterns
                else "No extracted patterns.",
                "outcomeSignal": str(payload.get("outcome_signal") or "unknown"),
                "extractedAt": row["extracted_at"],
                "artifactUpdatedAt": row["updated_at"],
            }
        )

    return {
        "role": role,
        "roleLabel": _role_label(role),
        "filters": {
            "sources": [
                {"value": "all", "label": "All sources"},
                *[
                    {"value": kind, "label": _source_label(kind)}
                    for kind in ("gitlab_mr", "jira_issue", "confluence_page")
                ],
            ],
            "clusters": [{"value": "all", "label": "All clusters"}]
            + [{"value": name, "label": name} for name in cluster_names],
        },
        "summary": {
            "visible": len(items),
            "total": total,
            "clustered": clustered_total,
            "unclustered": max(0, role_total - clustered_total),
        },
        "pagination": {
            "limit": limit,
            "offset": offset,
            "total": total,
        },
        "items": items,
    }


def get_review_entry(
    role: str,
    extraction_id: int,
    *,
    db_path: Path | None = None,
    packs_dir: Path | None = None,
) -> dict[str, Any]:
    _ensure_role(role)
    config = _default_config(db_path, packs_dir)
    with connect(config.db_path) as conn:
        row = conn.execute(
            """
            SELECT e.id, e.artifact_id, e.role, e.payload, e.extracted_at, e.llm_model,
                   a.kind, a.external_id, a.metadata, a.updated_at,
                   s.score, s.breakdown,
                   c.name AS cluster_name
            FROM extractions e
            JOIN artifacts a ON a.id = e.artifact_id
            LEFT JOIN scores s ON s.artifact_id = e.artifact_id AND s.role = e.role
            LEFT JOIN clusters c ON c.id = e.cluster_id
            WHERE e.id = ? AND e.role = ?
            """,
            (extraction_id, role),
        ).fetchone()
        if row is None:
            raise NotFoundError(f"Extraction {extraction_id} not found for role {role}.")
        payload = _parse_json(row["payload"])
        metadata = _parse_json(row["metadata"])
        patterns = _pattern_list(payload)
        linked_artifacts = _linked_artifacts(conn, int(row["artifact_id"]))

    return {
        "extractionId": int(row["id"]),
        "artifactId": int(row["artifact_id"]),
        "artifactExternalId": str(row["external_id"]),
        "title": _review_title(str(row["kind"]), str(row["external_id"]), metadata),
        "sourceKind": str(row["kind"]),
        "sourceLabel": _source_label(str(row["kind"])),
        "clusterName": str(row["cluster_name"]) if row["cluster_name"] else None,
        "score": float(row["score"] or 0.0),
        "scoreBreakdown": _parse_json(row["breakdown"]),
        "taskType": str(payload.get("task_type") or "unknown"),
        "domainTags": _domain_tags(payload),
        "outcomeSignal": str(payload.get("outcome_signal") or "unknown"),
        "patterns": patterns,
        "filesTouched": _files_touched(payload),
        "linkedArtifacts": linked_artifacts,
        "artifactMetadata": metadata,
        "artifactUpdatedAt": row["updated_at"],
        "extractedAt": row["extracted_at"],
        "llmModel": row["llm_model"],
        "artifactWebUrl": metadata.get("web_url"),
    }
