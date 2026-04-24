from datetime import date

from distill_core import blob as blob_module
from distill_core.db import connect, init_schema
from distill_capture.ingest_jira import build_session, extract_lifecycle_events, run_ingest

from tests.support.fakes import FakeResponse, FakeSession


def test_build_session_uses_bearer_for_non_email_username():
    session = build_session(username="tuna30", token="secret", auth_mode="auto")

    assert session.auth is None
    assert session.headers["Authorization"] == "Bearer secret"


def test_extract_lifecycle_events_derives_status_scope_and_reopened():
    issue = {
        "key": "APP-123",
        "changelog": {
            "histories": [
                {
                    "created": "2026-01-02T10:00:00Z",
                    "items": [
                        {"field": "status", "fromString": "To Do", "toString": "In Progress"}
                    ],
                },
                {
                    "created": "2026-01-03T10:00:00Z",
                    "items": [{"field": "summary", "fromString": "Old", "toString": "New"}],
                },
                {
                    "created": "2026-01-04T10:00:00Z",
                    "items": [{"field": "status", "fromString": "Done", "toString": "In Progress"}],
                },
            ]
        },
    }

    events = extract_lifecycle_events(issue)

    assert [event["event_kind"] for event in events] == [
        "status_change",
        "scope_change",
        "status_change",
        "reopened",
    ]


def test_ingest_jira_persists_issue_comments_and_events(tmp_path, monkeypatch):
    db_path = tmp_path / "distill.db"
    init_schema(db_path)
    monkeypatch.setattr(blob_module, "BLOBS_DIR", tmp_path / "blobs")

    session = FakeSession(
        responses={
            "/rest/api/2/search": [
                FakeResponse(
                    {
                        "issues": [
                            {
                                "id": "2001",
                                "key": "APP-123",
                                "fields": {
                                    "summary": "Edit payment schedule",
                                    "created": "2026-02-01T10:00:00Z",
                                    "updated": "2026-02-03T10:00:00Z",
                                    "status": {"name": "Done"},
                                    "labels": ["mobile"],
                                    "components": [{"name": "Flutter"}],
                                    "description": "Reach alice@example.com",
                                },
                                "changelog": {
                                    "histories": [
                                        {
                                            "created": "2026-02-02T10:00:00Z",
                                            "items": [
                                                {
                                                    "field": "status",
                                                    "fromString": "In Progress",
                                                    "toString": "Done",
                                                }
                                            ],
                                        }
                                    ]
                                },
                            }
                        ],
                        "startAt": 0,
                        "maxResults": 100,
                        "total": 1,
                    }
                ),
                FakeResponse({"issues": [], "startAt": 1, "maxResults": 100, "total": 1}),
            ],
            "/rest/api/2/issue/APP-123/comment": FakeResponse(
                {"comments": [{"body": "Ping bob@example.com"}]}
            ),
        }
    )

    result = run_ingest(
        session=session,
        base_url="https://jira.example",
        project_key="APP",
        username="user",
        token="token",
        api_version="2",
        db_path=db_path,
        blob_root=tmp_path / "blobs",
        since=date(2026, 1, 1),
        until=date(2026, 4, 24),
        max_items=20,
    )

    assert result["ingested"] == 1
    with connect(db_path) as conn:
        issue_count = conn.execute(
            "SELECT COUNT(*) FROM artifacts WHERE kind='jira_issue'"
        ).fetchone()[0]
        event_count = conn.execute("SELECT COUNT(*) FROM jira_events").fetchone()[0]

    assert issue_count == 1
    assert event_count >= 1
