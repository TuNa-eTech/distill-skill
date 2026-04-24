"""Debug: given a module, dump the source artifacts/extractions it cites."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from distill_core.config import DB_PATH
from distill_core.db import connect

SOURCE_RE = re.compile(r"\[src:\s*([^\]]+)\]")
INTEGER_RE = re.compile(r"\d+")


def _parse_json(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    try:
        data = json.loads(value)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def parse_source_ids(text: str) -> list[int]:
    ordered: list[int] = []
    seen: set[int] = set()
    for match in SOURCE_RE.finditer(text):
        for token in INTEGER_RE.findall(match.group(1)):
            source_id = int(token)
            if source_id not in seen:
                ordered.append(source_id)
                seen.add(source_id)
    return ordered


def trace_module(*, module_path: Path | str, db_path: Path = DB_PATH) -> dict[int, dict[str, Any]]:
    path = Path(module_path)
    text = path.read_text(encoding="utf-8")
    source_ids = parse_source_ids(text)
    trace: dict[int, dict[str, Any]] = {}
    role: str | None = None
    parts = path.parts
    if "packs" in parts:
        packs_index = parts.index("packs")
        if packs_index + 1 < len(parts):
            role = parts[packs_index + 1]

    with connect(db_path) as conn:
        for source_id in source_ids:
            artifact = conn.execute(
                "SELECT * FROM artifacts WHERE id = ?",
                (source_id,),
            ).fetchone()
            if role:
                extraction_rows = conn.execute(
                    "SELECT * FROM extractions WHERE artifact_id = ? AND role = ? ORDER BY id",
                    (source_id, role),
                ).fetchall()
            else:
                extraction_rows = conn.execute(
                    "SELECT * FROM extractions WHERE artifact_id = ? ORDER BY id",
                    (source_id,),
                ).fetchall()
            artifact_payload = None
            if artifact is not None:
                artifact_payload = {
                    "id": artifact["id"],
                    "kind": artifact["kind"],
                    "external_id": artifact["external_id"],
                    "created_at": artifact["created_at"],
                    "updated_at": artifact["updated_at"],
                    "metadata": _parse_json(artifact["metadata"]),
                    "blob_path": artifact["blob_path"],
                }
            trace[source_id] = {
                "artifact": artifact_payload,
                "extractions": [
                    {
                        "id": row["id"],
                        "role": row["role"],
                        "cluster_id": row["cluster_id"],
                        "llm_model": row["llm_model"],
                        "payload": _parse_json(row["payload"]),
                        "extracted_at": row["extracted_at"],
                    }
                    for row in extraction_rows
                ],
            }
    return trace


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--module", required=True, help="Path to skills/<name>.md")
    args = parser.parse_args()

    print(json.dumps(trace_module(module_path=args.module), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
