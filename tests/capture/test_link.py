from distill_core.db import connect, init_schema, upsert_artifact
from distill_capture.link import run_linking


def test_link_jira_references_uses_mr_and_page_metadata(tmp_path):
    db_path = tmp_path / "distill.db"
    init_schema(db_path)

    with connect(db_path) as conn:
        jira_id = upsert_artifact(
            conn,
            kind="jira_issue",
            external_id="APP-123",
            created_at=None,
            updated_at=None,
            metadata={"summary": "Payment schedule"},
            blob_path=None,
        )
        mr_id = upsert_artifact(
            conn,
            kind="gitlab_mr",
            external_id="101",
            created_at=None,
            updated_at=None,
            metadata={
                "title": "APP-123 add payment schedule flow",
                "source_branch": "feature/APP-123-flow",
                "description": "",
            },
            blob_path=None,
        )
        page_id = upsert_artifact(
            conn,
            kind="confluence_page",
            external_id="9001",
            created_at=None,
            updated_at=None,
            metadata={
                "title": "ADR for APP-123",
                "body_text": "This page references APP-123",
            },
            blob_path=None,
        )

    result = run_linking(db_path=db_path)

    assert result["created"] == 2
    with connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT source_id, target_id, link_type, confidence
            FROM links
            ORDER BY source_id
            """
        ).fetchall()

    assert [(row["source_id"], row["target_id"], row["link_type"]) for row in rows] == [
        (mr_id, jira_id, "references_jira"),
        (page_id, jira_id, "references_jira"),
    ]
    assert rows[0]["confidence"] >= 0.9
