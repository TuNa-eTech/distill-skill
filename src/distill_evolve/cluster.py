"""Interactive clustering — show extraction, prompt for cluster name, save."""

from __future__ import annotations

import argparse
import json
from typing import Any, Callable

from distill_core.config import DB_PATH
from distill_core.db import assign_extraction_cluster, connect, upsert_cluster
from distill_core.roles import SUPPORTED_ROLES


def _parse_json(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    try:
        data = json.loads(value)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _load_unclustered_extractions(conn, *, role: str):
    return conn.execute(
        """
        SELECT e.id, e.artifact_id, e.payload, a.metadata, a.external_id, s.score
        FROM extractions e
        JOIN artifacts a ON a.id = e.artifact_id
        JOIN scores s ON s.artifact_id = e.artifact_id
        WHERE s.role = ? AND e.role = ? AND e.cluster_id IS NULL
        ORDER BY s.score DESC, e.id ASC
        """,
        (role, role),
    ).fetchall()


def _load_existing_clusters(conn, *, role: str) -> list[dict[str, Any]]:
    return [
        {"id": int(row["id"]), "name": row["name"], "description": row["description"] or ""}
        for row in conn.execute(
            "SELECT id, name, description FROM clusters WHERE role = ? ORDER BY id",
            (role,),
        ).fetchall()
    ]


def _preview_extraction(row) -> list[str]:
    metadata = _parse_json(row["metadata"])
    payload = _parse_json(row["payload"])
    patterns = payload.get("patterns", [])
    lines = [
        f"Extraction #{row['id']} (artifact {row['artifact_id']}, score={row['score']:.2f})",
        f"Title: {metadata.get('title') or row['external_id']}",
        f"Task: {payload.get('task_type', 'n/a')}",
    ]
    for pattern in patterns[:5]:
        if isinstance(pattern, dict):
            lines.append(f"  - [{pattern.get('kind', 'pattern')}] {pattern.get('summary', '')}")
    return lines


def cluster_extractions(
    conn,
    *,
    role: str,
    input_fn: Callable[[str], str] = input,
    output_fn: Callable[[str], None] = print,
) -> dict[str, int]:
    pending = _load_unclustered_extractions(conn, role=role)
    clusters = _load_existing_clusters(conn, role=role)
    by_name = {cluster["name"].lower(): cluster["id"] for cluster in clusters}
    by_id = {cluster["id"]: cluster["name"] for cluster in clusters}
    summary = {"processed": len(pending), "assigned": 0, "skipped": 0, "created_clusters": 0}

    for row in pending:
        for line in _preview_extraction(row):
            output_fn(line)
        if clusters:
            output_fn("Existing clusters:")
            for cluster in clusters:
                output_fn(f"  {cluster['id']}: {cluster['name']}")
        choice = input_fn("Cluster id/name (or 'new'/'skip'): ").strip()
        if not choice or choice.lower() == "skip":
            summary["skipped"] += 1
            continue
        if choice.lower() == "new":
            name = input_fn("New cluster name: ").strip()
            if not name:
                summary["skipped"] += 1
                continue
            cluster_id = upsert_cluster(conn, role=role, name=name, description=None)
            if cluster_id not in by_id:
                clusters.append({"id": cluster_id, "name": name, "description": ""})
                by_id[cluster_id] = name
                by_name[name.lower()] = cluster_id
                summary["created_clusters"] += 1
        elif choice.isdigit():
            cluster_id = int(choice)
            if cluster_id not in by_id:
                output_fn(f"Unknown cluster id: {cluster_id}")
                summary["skipped"] += 1
                continue
        else:
            cluster_id = by_name.get(choice.lower())
            if cluster_id is None:
                output_fn(f"Unknown cluster name: {choice}")
                summary["skipped"] += 1
                continue
        assign_extraction_cluster(conn, extraction_id=int(row["id"]), cluster_id=cluster_id)
        summary["assigned"] += 1
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--role", required=True, choices=list(SUPPORTED_ROLES))
    args = parser.parse_args()

    with connect(DB_PATH) as conn:
        summary = cluster_extractions(conn, role=args.role)
    print(
        "Processed {processed} extractions, assigned {assigned}, skipped {skipped}, "
        "created {created_clusters} clusters.".format(**summary)
    )


if __name__ == "__main__":
    main()
