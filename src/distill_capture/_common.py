from __future__ import annotations

import json
import re
from datetime import date, datetime, timedelta, timezone
from html import unescape
from pathlib import Path
from typing import Any, Iterable, Mapping

from distill_capture.redact import redact
from distill_core.blob import load_blob_text, save_redacted_json_blob
from distill_core.config import BLOBS_DIR, default_ingest_since, default_ingest_until

DEFAULT_TIMEOUT = 30
JIRA_KEY_RE = re.compile(r"\b[A-Z][A-Z0-9]+-\d+\b")

_TODO_STATUSES = {
    "backlog",
    "open",
    "ready",
    "selected for development",
    "to do",
    "todo",
}
_DONE_STATUSES = {"closed", "done", "resolved"}
_MOBILE_PREFIXES = (
    "android/",
    "integration_test/",
    "ios/",
    "lib/",
    "macos/",
    "test/",
)
_MOBILE_FILES = {"pubspec.lock", "pubspec.yaml"}


def parse_date_arg(value: str | None) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value)


def resolve_date_window(
    *, since: str | None = None, until: str | None = None, window: int | None = None
) -> tuple[date, date]:
    explicit_since = parse_date_arg(since)
    explicit_until = parse_date_arg(until)

    if explicit_since or explicit_until:
        resolved_since = explicit_since or date.fromisoformat(default_ingest_since())
        resolved_until = explicit_until or date.fromisoformat(default_ingest_until())
    elif window is not None:
        resolved_until = date.fromisoformat(default_ingest_until())
        resolved_since = resolved_until - timedelta(days=window)
    else:
        resolved_since = date.fromisoformat(default_ingest_since())
        resolved_until = date.fromisoformat(default_ingest_until())

    if resolved_until < resolved_since:
        raise ValueError(
            f"Invalid ingest range: since={resolved_since.isoformat()} > until={resolved_until.isoformat()}"
        )
    return resolved_since, resolved_until


def parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None

    raw = value.strip()
    if not raw:
        return None

    if raw.endswith("Z"):
        raw = f"{raw[:-1]}+00:00"

    if re.search(r"[+-]\d{4}$", raw):
        raw = f"{raw[:-5]}{raw[-5:-2]}:{raw[-2:]}"

    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        for pattern in (
            "%Y-%m-%dT%H:%M:%S.%f%z",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%d",
        ):
            try:
                parsed = datetime.strptime(raw, pattern)
                break
            except ValueError:
                continue
        else:
            raise

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def within_date_range(value: str | None, *, since: date, until: date) -> bool:
    parsed = parse_datetime(value)
    if not parsed:
        return False
    return since <= parsed.date() <= until


def join_url(base_url: str, *parts: str) -> str:
    cleaned = [base_url.rstrip("/")]
    cleaned.extend(part.strip("/") for part in parts if part)
    return "/".join(cleaned)


def safe_blob_external_id(external_id: str) -> str:
    return external_id.replace("/", "__").replace(":", "__").replace(" ", "_")


def save_json_blob(
    kind: str,
    external_id: str,
    payload: Mapping[str, Any],
    *,
    blob_root: Path = BLOBS_DIR,
) -> str:
    if Path(blob_root) == BLOBS_DIR:
        return save_redacted_json_blob(kind, external_id, payload)

    rel_path = Path(kind) / f"{safe_blob_external_id(external_id)}.json"
    full_path = Path(blob_root) / rel_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    redacted = redact(json.dumps(payload, ensure_ascii=False, default=str))
    full_path.write_text(redacted, encoding="utf-8")
    return rel_path.as_posix()


def load_blob(blob_path: str, *, blob_root: Path = BLOBS_DIR) -> str:
    if Path(blob_root) == BLOBS_DIR:
        return load_blob_text(blob_path)
    return (Path(blob_root) / blob_path).read_text(encoding="utf-8")


def strip_html(value: str | None) -> str:
    if not value:
        return ""
    text = re.sub(r"<[^>]+>", " ", value)
    text = unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def extract_jira_keys(*texts: str | None) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for text in texts:
        if not text:
            continue
        for match in JIRA_KEY_RE.findall(text.upper()):
            if match not in seen:
                seen.add(match)
                ordered.append(match)
    return ordered


def is_started_status(value: str | None) -> bool:
    normalized = normalize_status(value)
    return bool(normalized) and normalized not in _TODO_STATUSES


def is_done_status(value: str | None) -> bool:
    return normalize_status(value) in _DONE_STATUSES


def normalize_status(value: str | None) -> str:
    return (value or "").strip().casefold()


def is_mobile_path(path: str | None) -> bool:
    if not path:
        return False
    normalized = path.strip().lstrip("./")
    return normalized in _MOBILE_FILES or normalized.startswith(_MOBILE_PREFIXES)


def has_test_path(paths: Iterable[str]) -> bool:
    return any(path.startswith(("integration_test/", "test/")) for path in paths)
