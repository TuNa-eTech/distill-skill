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
  role          TEXT,
  cluster_id    INTEGER,
  payload       TEXT,
  llm_model     TEXT,
  extracted_at  TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_extractions_role_artifact ON extractions(role, artifact_id);

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
    _migrate_extractions_schema(conn)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_schema(db_path: Path = DB_PATH) -> None:
    with connect(db_path) as conn:
        conn.executescript(SCHEMA)
        _migrate_extractions_schema(conn)


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table,),
    ).fetchone()
    return row is not None


def _table_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    return {str(row["name"]) for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}


def _parse_payload(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _infer_legacy_extraction_role(
    conn: sqlite3.Connection,
    *,
    artifact_id: int,
    artifact_kind: str,
    cluster_id: int | None,
    payload: str | None,
) -> str | None:
    if cluster_id is not None:
        row = conn.execute("SELECT role FROM clusters WHERE id = ?", (cluster_id,)).fetchone()
        if row and row["role"]:
            return str(row["role"])

    if artifact_kind == "gitlab_mr":
        return "mobile-dev"
    if artifact_kind == "confluence_page":
        return "business-analyst"

    payload_map = _parse_payload(payload)
    task_type = str(payload_map.get("task_type") or "").strip().lower()
    tags = " ".join(str(item).strip().lower() for item in payload_map.get("domain_tags") or [])
    haystack = f"{task_type} {tags}".strip()

    if any(
        keyword in haystack
        for keyword in (
            "report-bug",
            "plan-regression",
            "design-test",
            "triage-defect",
            "bug-report-quality",
            "regression-strategy",
            "test-case-design",
            "manual-testing",
            "regression-testing",
        )
    ):
        return "tester-manual"

    if any(
        keyword in haystack
        for keyword in (
            "write-spec",
            "draft-spec",
            "draft-ac",
            "acceptance-criteria",
            "spec-writing",
            "discovery",
            "stakeholder",
            "stakeholder-comms",
        )
    ):
        return "business-analyst"

    roles = {
        str(row["role"])
        for row in conn.execute(
            "SELECT role FROM scores WHERE artifact_id = ?",
            (artifact_id,),
        ).fetchall()
        if row["role"]
    }
    if len(roles) == 1:
        return next(iter(roles))
    return None


def _migrate_extractions_schema(conn: sqlite3.Connection) -> None:
    if not _table_exists(conn, "extractions"):
        return

    columns = _table_columns(conn, "extractions")
    if "role" not in columns:
        conn.execute("ALTER TABLE extractions ADD COLUMN role TEXT")
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_extractions_role_artifact ON extractions(role, artifact_id)"
    )

    rows = conn.execute(
        """
        SELECT e.id, e.artifact_id, e.cluster_id, e.payload, a.kind AS artifact_kind
        FROM extractions e
        JOIN artifacts a ON a.id = e.artifact_id
        WHERE e.role IS NULL OR TRIM(e.role) = ''
        """
    ).fetchall()
    for row in rows:
        inferred_role = _infer_legacy_extraction_role(
            conn,
            artifact_id=int(row["artifact_id"]),
            artifact_kind=str(row["artifact_kind"]),
            cluster_id=row["cluster_id"],
            payload=row["payload"],
        )
        if inferred_role:
            conn.execute(
                "UPDATE extractions SET role = ? WHERE id = ?",
                (inferred_role, int(row["id"])),
            )


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


def fetch_artifact_by_ref(
    conn: sqlite3.Connection, *, kind: str, external_id: str
) -> sqlite3.Row | None:
    return conn.execute(
        """
        SELECT *
        FROM artifacts
        WHERE kind = ? AND external_id = ?
        """,
        (kind, external_id),
    ).fetchone()


def upsert_link(
    conn: sqlite3.Connection,
    *,
    source_id: int,
    target_id: int,
    link_type: str,
    confidence: float = 1.0,
) -> None:
    conn.execute(
        """
        INSERT INTO links (source_id, target_id, link_type, confidence)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(source_id, target_id, link_type) DO UPDATE SET
          confidence = excluded.confidence
        """,
        (source_id, target_id, link_type, confidence),
    )


def insert_jira_event(
    conn: sqlite3.Connection,
    *,
    issue_id: int,
    event_kind: str,
    from_value: str | None,
    to_value: str | None,
    occurred_at: str | None,
) -> None:
    conn.execute(
        """
        INSERT INTO jira_events (issue_id, event_kind, from_value, to_value, occurred_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (issue_id, event_kind, from_value, to_value, occurred_at),
    )


def upsert_score(
    conn: sqlite3.Connection,
    *,
    artifact_id: int,
    role: str,
    score: float,
    breakdown: dict[str, Any],
) -> None:
    conn.execute(
        """
        INSERT INTO scores (artifact_id, role, score, breakdown)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(artifact_id, role) DO UPDATE SET
          score = excluded.score,
          breakdown = excluded.breakdown,
          scored_at = datetime('now')
        """,
        (artifact_id, role, score, json.dumps(breakdown)),
    )


def insert_extraction(
    conn: sqlite3.Connection,
    *,
    artifact_id: int,
    role: str,
    payload: dict[str, Any],
    llm_model: str,
    cluster_id: int | None = None,
) -> int:
    cur = conn.execute(
        """
        INSERT INTO extractions (artifact_id, role, cluster_id, payload, llm_model)
        VALUES (?, ?, ?, ?, ?)
        RETURNING id
        """,
        (artifact_id, role, cluster_id, json.dumps(payload), llm_model),
    )
    return cur.fetchone()[0]


def upsert_cluster(
    conn: sqlite3.Connection,
    *,
    role: str,
    name: str,
    description: str | None = None,
) -> int:
    existing = conn.execute(
        """
        SELECT id
        FROM clusters
        WHERE role = ? AND name = ?
        """,
        (role, name),
    ).fetchone()
    if existing:
        conn.execute(
            """
            UPDATE clusters
            SET description = COALESCE(?, description)
            WHERE id = ?
            """,
            (description, existing["id"]),
        )
        return int(existing["id"])

    cur = conn.execute(
        """
        INSERT INTO clusters (role, name, description)
        VALUES (?, ?, ?)
        RETURNING id
        """,
        (role, name, description),
    )
    return cur.fetchone()[0]


def assign_extraction_cluster(
    conn: sqlite3.Connection, *, extraction_id: int, cluster_id: int
) -> None:
    extraction = conn.execute(
        "SELECT role FROM extractions WHERE id = ?",
        (extraction_id,),
    ).fetchone()
    cluster = conn.execute(
        "SELECT role FROM clusters WHERE id = ?",
        (cluster_id,),
    ).fetchone()
    if extraction is None:
        raise ValueError(f"Unknown extraction id: {extraction_id}")
    if cluster is None:
        raise ValueError(f"Unknown cluster id: {cluster_id}")
    extraction_role = extraction["role"]
    cluster_role = cluster["role"]
    if extraction_role and cluster_role and extraction_role != cluster_role:
        raise ValueError(
            f"Cannot assign extraction role={extraction_role!r} to cluster role={cluster_role!r}"
        )
    conn.execute(
        """
        UPDATE extractions
        SET cluster_id = ?
        WHERE id = ?
        """,
        (cluster_id, extraction_id),
    )
