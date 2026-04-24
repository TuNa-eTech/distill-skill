from distill_core.db import (
    assign_extraction_cluster,
    connect,
    fetch_artifact_by_ref,
    init_schema,
    insert_extraction,
    insert_jira_event,
    upsert_artifact,
    upsert_cluster,
    upsert_link,
    upsert_score,
)


def test_init_schema_creates_expected_tables(tmp_path):
    db_path = tmp_path / "distill.db"

    init_schema(db_path)

    with connect(db_path) as conn:
        tables = {
            row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }

    assert {"artifacts", "links", "jira_events", "scores", "extractions", "clusters"} <= tables


def test_init_schema_backfills_legacy_extractions_role(tmp_path):
    db_path = tmp_path / "legacy.db"
    with connect(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE artifacts (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              kind TEXT NOT NULL,
              external_id TEXT NOT NULL,
              created_at TEXT,
              updated_at TEXT,
              metadata TEXT,
              blob_path TEXT
            );
            CREATE TABLE extractions (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              artifact_id INTEGER,
              cluster_id INTEGER,
              payload TEXT,
              llm_model TEXT,
              extracted_at TEXT DEFAULT (datetime('now'))
            );
            INSERT INTO artifacts (id, kind, external_id, metadata) VALUES
              (1, 'gitlab_mr', '901', '{}'),
              (2, 'jira_issue', 'QA-1', '{}');
            INSERT INTO extractions (artifact_id, cluster_id, payload, llm_model) VALUES
              (1, NULL, '{"artifact_id":1,"task_type":"refactor-checks","domain_tags":["flutter"],"patterns":[]}', 'gpt-4o'),
              (2, NULL, '{"artifact_id":2,"task_type":"report-bug","domain_tags":["bug-report-quality"],"patterns":[]}', 'gpt-4o');
            """
        )

    init_schema(db_path)

    with connect(db_path) as conn:
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(extractions)").fetchall()}
        roles = conn.execute("SELECT role FROM extractions ORDER BY id").fetchall()

    assert "role" in columns
    assert [row["role"] for row in roles] == ["mobile-dev", "tester-manual"]


def test_upsert_artifact_is_idempotent_and_fetchable(tmp_path):
    db_path = tmp_path / "distill.db"
    init_schema(db_path)

    with connect(db_path) as conn:
        first_id = upsert_artifact(
            conn,
            kind="gitlab_mr",
            external_id="123",
            created_at="2026-01-01T00:00:00Z",
            updated_at="2026-01-02T00:00:00Z",
            metadata={"title": "Initial"},
            blob_path="gitlab/mr/123.json",
        )
        second_id = upsert_artifact(
            conn,
            kind="gitlab_mr",
            external_id="123",
            created_at="2026-01-01T00:00:00Z",
            updated_at="2026-01-03T00:00:00Z",
            metadata={"title": "Updated"},
            blob_path="gitlab/mr/123.json",
        )
        fetched = fetch_artifact_by_ref(conn, kind="gitlab_mr", external_id="123")

    assert first_id == second_id
    assert fetched is not None
    assert fetched["updated_at"] == "2026-01-03T00:00:00Z"


def test_link_score_event_and_cluster_helpers_work(tmp_path):
    db_path = tmp_path / "distill.db"
    init_schema(db_path)

    with connect(db_path) as conn:
        source_id = upsert_artifact(
            conn,
            kind="gitlab_mr",
            external_id="123",
            created_at=None,
            updated_at=None,
            metadata={},
            blob_path=None,
        )
        target_id = upsert_artifact(
            conn,
            kind="jira_issue",
            external_id="PROJ-1",
            created_at=None,
            updated_at=None,
            metadata={},
            blob_path=None,
        )

        upsert_link(
            conn,
            source_id=source_id,
            target_id=target_id,
            link_type="references",
            confidence=0.9,
        )
        insert_jira_event(
            conn,
            issue_id=target_id,
            event_kind="status_change",
            from_value="To Do",
            to_value="Done",
            occurred_at="2026-01-05T10:00:00Z",
        )
        upsert_score(
            conn,
            artifact_id=source_id,
            role="mobile-dev",
            score=4.5,
            breakdown={"merged": 3.0, "tests": 1.5},
        )
        extraction_id = insert_extraction(
            conn,
            artifact_id=source_id,
            role="mobile-dev",
            payload={"artifact_id": source_id, "patterns": []},
            llm_model="gpt-4o",
        )
        cluster_id = upsert_cluster(conn, role="mobile-dev", name="state-management")
        assign_extraction_cluster(conn, extraction_id=extraction_id, cluster_id=cluster_id)

        link_row = conn.execute("SELECT * FROM links").fetchone()
        event_row = conn.execute("SELECT * FROM jira_events").fetchone()
        score_row = conn.execute("SELECT * FROM scores").fetchone()
        extraction_row = conn.execute("SELECT * FROM extractions").fetchone()
        cluster_row = conn.execute("SELECT * FROM clusters").fetchone()

    assert link_row["confidence"] == 0.9
    assert event_row["event_kind"] == "status_change"
    assert score_row["role"] == "mobile-dev"
    assert extraction_row["role"] == "mobile-dev"
    assert extraction_row["cluster_id"] == cluster_id
    assert cluster_row["name"] == "state-management"
