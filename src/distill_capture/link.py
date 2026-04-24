"""Link artifacts across sources via deterministic Jira key extraction."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from distill_core.config import BLOBS_DIR, DB_PATH
from distill_core.db import connect, upsert_link

from ._common import extract_jira_keys, load_blob

LINK_TYPE = "references_jira"


def run_linking(*, db_path: Path = DB_PATH, blob_root: Path = BLOBS_DIR) -> dict[str, int]:
    created = 0
    with connect(db_path) as conn:
        conn.execute("DELETE FROM links WHERE link_type = ?", (LINK_TYPE,))
        jira_rows = conn.execute(
            """
            SELECT id, external_id, metadata
            FROM artifacts
            WHERE kind = 'jira_issue'
            """
        ).fetchall()
        jira_index = {
            (json.loads(row["metadata"]).get("key") or row["external_id"]): row["id"]
            for row in jira_rows
        }

        source_rows = conn.execute(
            """
            SELECT id, kind, metadata, blob_path
            FROM artifacts
            WHERE kind IN ('gitlab_mr', 'confluence_page')
            """
        ).fetchall()
        for row in source_rows:
            metadata = json.loads(row["metadata"])
            keys, confidence = _extract_links(
                kind=row["kind"],
                metadata=metadata,
                blob_path=row["blob_path"],
                blob_root=blob_root,
            )
            for key in keys:
                target_id = jira_index.get(key)
                if target_id is None:
                    continue
                upsert_link(
                    conn,
                    source_id=row["id"],
                    target_id=target_id,
                    link_type=LINK_TYPE,
                    confidence=confidence.get(key, 0.8),
                )
                created += 1
    return {"created": created}


def main() -> None:
    result = link_jira_references()
    print(f"Linking complete: {result} Jira links")


def _extract_links(
    *,
    kind: str,
    metadata: dict[str, Any],
    blob_path: str | None,
    blob_root: Path,
) -> tuple[list[str], dict[str, float]]:
    if kind == "gitlab_mr":
        field_map = {
            "title": metadata.get("title"),
            "source_branch": metadata.get("source_branch"),
            "description": metadata.get("description"),
        }
    else:
        field_map = {
            "title": metadata.get("title"),
            "body_text": metadata.get("body_text"),
        }

    if blob_path and not any(field_map.values()):
        field_map["blob"] = load_blob(blob_path, blob_root=blob_root)

    confidence_by_key: dict[str, float] = {}
    ordered_keys: list[str] = []
    for field, value in field_map.items():
        keys = extract_jira_keys(value)
        for key in keys:
            if key not in ordered_keys:
                ordered_keys.append(key)
            confidence_by_key[key] = max(confidence_by_key.get(key, 0.0), _field_confidence(field))
    return ordered_keys, confidence_by_key


def _field_confidence(field: str) -> float:
    if field in {"source_branch", "title"}:
        return 1.0
    if field == "body_text":
        return 0.95
    return 0.9


def link_jira_references(*, db_path: Path = DB_PATH) -> int:
    return run_linking(db_path=db_path)["created"]


if __name__ == "__main__":
    main()
