from __future__ import annotations

import json
from pathlib import Path

from distill_core.db import upsert_artifact


def seed_artifact(
    conn,
    *,
    kind: str,
    external_id: str,
    metadata: dict | None = None,
    created_at: str = "2026-01-10T00:00:00Z",
    updated_at: str | None = None,
    blob_path: str | None = None,
) -> int:
    artifact_id = upsert_artifact(
        conn,
        kind=kind,
        external_id=external_id,
        created_at=created_at,
        updated_at=updated_at or created_at,
        metadata=metadata or {},
        blob_path=blob_path,
    )
    conn.commit()
    return artifact_id


def seed_link(
    conn,
    *,
    source_id: int,
    target_id: int,
    link_type: str = "related",
    confidence: float = 0.9,
) -> None:
    conn.execute(
        """
        INSERT INTO links (source_id, target_id, link_type, confidence)
        VALUES (?, ?, ?, ?)
        """,
        (source_id, target_id, link_type, confidence),
    )
    conn.commit()


def seed_jira_event(
    conn,
    *,
    issue_id: int,
    event_kind: str,
    from_value: str | None,
    to_value: str | None,
    occurred_at: str,
) -> None:
    conn.execute(
        """
        INSERT INTO jira_events (issue_id, event_kind, from_value, to_value, occurred_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (issue_id, event_kind, from_value, to_value, occurred_at),
    )
    conn.commit()


def seed_score(
    conn, *, artifact_id: int, role: str, score: float, breakdown: dict | None = None
) -> None:
    conn.execute(
        """
        INSERT INTO scores (artifact_id, role, score, breakdown)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(artifact_id, role) DO UPDATE SET
          score = excluded.score,
          breakdown = excluded.breakdown
        """,
        (artifact_id, role, score, json.dumps(breakdown or {})),
    )
    conn.commit()


def seed_extraction(
    conn,
    *,
    artifact_id: int,
    payload: dict,
    cluster_id: int | None = None,
    role: str | None = None,
    llm_model: str = "gpt-4o",
) -> int:
    resolved_role = role
    if resolved_role is None and cluster_id is not None:
        cluster_row = conn.execute(
            "SELECT role FROM clusters WHERE id = ?", (cluster_id,)
        ).fetchone()
        if cluster_row is not None:
            resolved_role = cluster_row["role"]
    if resolved_role is None:
        score_row = conn.execute(
            "SELECT role FROM scores WHERE artifact_id = ? ORDER BY scored_at DESC, role ASC LIMIT 1",
            (artifact_id,),
        ).fetchone()
        if score_row is not None:
            resolved_role = score_row["role"]
    if resolved_role is None:
        artifact_row = conn.execute(
            "SELECT kind FROM artifacts WHERE id = ?", (artifact_id,)
        ).fetchone()
        if artifact_row is not None:
            if artifact_row["kind"] == "gitlab_mr":
                resolved_role = "mobile-dev"
            elif artifact_row["kind"] == "confluence_page":
                resolved_role = "business-analyst"
    if resolved_role is None:
        raise ValueError(f"Unable to infer role for extraction artifact_id={artifact_id}")

    cur = conn.execute(
        """
        INSERT INTO extractions (artifact_id, role, cluster_id, payload, llm_model)
        VALUES (?, ?, ?, ?, ?)
        RETURNING id
        """,
        (artifact_id, resolved_role, cluster_id, json.dumps(payload), llm_model),
    )
    extraction_id = int(cur.fetchone()[0])
    conn.commit()
    return extraction_id


def seed_cluster(
    conn,
    *,
    role: str,
    name: str,
    description: str = "",
) -> int:
    cur = conn.execute(
        """
        INSERT INTO clusters (role, name, description)
        VALUES (?, ?, ?)
        RETURNING id
        """,
        (role, name, description),
    )
    cluster_id = int(cur.fetchone()[0])
    conn.commit()
    return cluster_id


def write_blob(blobs_dir: Path, relative_path: str, payload: dict) -> str:
    path = blobs_dir / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2))
    return relative_path
