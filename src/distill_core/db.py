import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from .config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS artifacts (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  kind         TEXT NOT NULL,
  external_id  TEXT NOT NULL,
  created_at   TEXT,
  updated_at   TEXT,
  metadata     TEXT,
  blob_path    TEXT,
  ingested_at  TEXT DEFAULT (datetime('now')),
  UNIQUE (kind, external_id)
);
CREATE INDEX IF NOT EXISTS idx_artifacts_kind ON artifacts(kind);

CREATE TABLE IF NOT EXISTS links (
  source_id   INTEGER NOT NULL,
  target_id   INTEGER NOT NULL,
  link_type   TEXT NOT NULL,
  confidence  REAL DEFAULT 1.0,
  PRIMARY KEY (source_id, target_id, link_type),
  FOREIGN KEY (source_id) REFERENCES artifacts(id),
  FOREIGN KEY (target_id) REFERENCES artifacts(id)
);

CREATE TABLE IF NOT EXISTS jira_events (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  issue_id     INTEGER REFERENCES artifacts(id),
  event_kind   TEXT,
  from_value   TEXT,
  to_value     TEXT,
  occurred_at  TEXT
);

CREATE TABLE IF NOT EXISTS scores (
  artifact_id  INTEGER REFERENCES artifacts(id),
  role         TEXT,
  score        REAL,
  breakdown    TEXT,
  scored_at    TEXT DEFAULT (datetime('now')),
  PRIMARY KEY (artifact_id, role)
);

CREATE TABLE IF NOT EXISTS extractions (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  artifact_id   INTEGER REFERENCES artifacts(id),
  cluster_id    INTEGER,
  payload       TEXT,
  llm_model     TEXT,
  extracted_at  TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS clusters (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  role         TEXT,
  name         TEXT,
  description  TEXT,
  created_at   TEXT DEFAULT (datetime('now'))
);
"""


@contextmanager
def connect(db_path: Path = DB_PATH) -> Iterator[sqlite3.Connection]:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_schema(db_path: Path = DB_PATH) -> None:
    with connect(db_path) as conn:
        conn.executescript(SCHEMA)


def upsert_artifact(
    conn: sqlite3.Connection,
    *,
    kind: str,
    external_id: str,
    created_at: str | None,
    updated_at: str | None,
    metadata: dict[str, Any],
    blob_path: str | None,
) -> int:
    cur = conn.execute(
        """
        INSERT INTO artifacts (kind, external_id, created_at, updated_at, metadata, blob_path)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(kind, external_id) DO UPDATE SET
          updated_at = excluded.updated_at,
          metadata   = excluded.metadata,
          blob_path  = excluded.blob_path
        RETURNING id
        """,
        (kind, external_id, created_at, updated_at, json.dumps(metadata), blob_path),
    )
    return cur.fetchone()[0]
