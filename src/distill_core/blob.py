"""Helpers for redacted blob persistence under data/blobs/."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from distill_capture.redact import redact

from .config import BLOBS_DIR


def _safe_part(value: str) -> str:
    return value.replace("/", "__").replace(":", "__").replace(" ", "_")


def save_redacted_json_blob(kind: str, external_id: str, payload: Mapping[str, Any]) -> str:
    """Persist a redacted JSON blob and return its path relative to data/blobs."""
    rel_path = Path(kind) / f"{_safe_part(external_id)}.json"
    full_path = BLOBS_DIR / rel_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    redacted = redact(json.dumps(payload, ensure_ascii=False))
    full_path.write_text(redacted, encoding="utf-8")
    return rel_path.as_posix()


def load_blob_text(blob_path: str | Path) -> str:
    path = BLOBS_DIR / Path(blob_path)
    return path.read_text(encoding="utf-8")
