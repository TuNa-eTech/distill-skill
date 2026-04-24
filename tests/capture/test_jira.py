import json
import sqlite3
from datetime import date

from distill_capture import ingest_jira


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []

    def get(self, url, *, params=None, timeout=None):
        self.calls.append((url, params))
        if not self._responses:
            raise AssertionError(f"Unexpected request: {url}")
        return FakeResponse(self._responses.pop(0))


def _issue(
    key: str,
    *,
    updated: str,
    changelog: list[dict],
    description: str = "User can edit schedules. Contact alice@company.com",
):
    return {
        "id": key.replace("-", ""),
        "key": key,
        "fields": {
            "summary": f"{key} Payment editor",
            "description": description,
            "status": {"name": "Done"},
            "issuetype": {"name": "Story"},
            "labels": ["mobile", "flutter"],
            "components": [{"name": "Payments"}],
            "created": "2026-01-01T09:00:00.000+0000",
            "updated": updated,
        },
        "changelog": {"histories": changelog},
    }


def test_fetch_issues_respects_date_range_and_cap():
    issue_in_range = _issue(
        "APP-101",
        updated="2026-02-03T10:00:00.000+0000",
        changelog=[],
    )
    issue_too_old = _issue(
        "APP-102",
        updated="2025-12-31T23:00:00.000+0000",
        changelog=[],
    )
    session = FakeSession(
        [
            {
                "issues": [issue_in_range, issue_too_old],
                "startAt": 0,
                "maxResults": 100,
                "total": 2,
            },
            {"issues": [], "startAt": 100, "maxResults": 100, "total": 2},
        ]
    )

    issues = ingest_jira.fetch_issues(
        session=session,
        base_url="https://company.atlassian.net",
        project_key="APP",
        since=date(2026, 1, 1),
        until=date(2026, 3, 31),
        cap=1,
    )

    assert [issue["key"] for issue in issues] == ["APP-101"]
    assert 'project = "APP"' in session.calls[0][1]["jql"]


def test_extract_lifecycle_events_derives_scope_change_and_reopen():
    issue = _issue(
        "APP-101",
        updated="2026-02-03T10:00:00.000+0000",
        changelog=[
            {
                "created": "2026-01-02T10:00:00.000+0000",
                "items": [
                    {
                        "field": "status",
                        "fromString": "To Do",
                        "toString": "In Progress",
                    }
                ],
            },
            {
                "created": "2026-01-03T10:00:00.000+0000",
                "items": [
                    {
                        "field": "description",
                        "fromString": "old scope",
                        "toString": "new scope",
                    }
                ],
            },
            {
                "created": "2026-01-04T10:00:00.000+0000",
                "items": [
                    {
                        "field": "status",
                        "fromString": "Done",
                        "toString": "In Progress",
                    }
                ],
            },
        ],
    )

    events = ingest_jira.extract_lifecycle_events(issue)

    assert [event["event_kind"] for event in events] == [
        "status_change",
        "scope_change",
        "status_change",
        "reopened",
    ]


def test_run_ingest_persists_events_and_redacted_blob(temp_db, temp_blobs):
    issue = _issue(
        "APP-101",
        updated="2026-02-03T10:00:00.000+0000",
        changelog=[
            {
                "created": "2026-01-02T10:00:00.000+0000",
                "items": [
                    {
                        "field": "status",
                        "fromString": "To Do",
                        "toString": "In Progress",
                    }
                ],
            }
        ],
    )
    session = FakeSession(
        [
            {"issues": [issue], "startAt": 0, "maxResults": 100, "total": 1},
            {"comments": [{"body": "Ping alice@company.com"}]},
        ]
    )

    result = ingest_jira.run_ingest(
        session=session,
        base_url="https://company.atlassian.net",
        project_key="APP",
        username="bot@example.com",
        token="secret",
        db_path=temp_db,
        blob_root=temp_blobs,
        since=date(2026, 1, 1),
        until=date(2026, 12, 31),
        max_items=10,
    )

    assert result["ingested"] == 1
    with sqlite3.connect(temp_db) as conn:
        artifact = conn.execute(
            "SELECT external_id, metadata, blob_path FROM artifacts WHERE kind = 'jira_issue'"
        ).fetchone()
        events = conn.execute(
            "SELECT event_kind, from_value, to_value FROM jira_events ORDER BY id"
        ).fetchall()

    assert artifact[0] == "APP-101"
    metadata = json.loads(artifact[1])
    assert metadata["status"] == "Done"
    assert metadata["issue_type"] == "Story"
    assert metadata["components"] == ["Payments"]
    assert events == [("status_change", "To Do", "In Progress")]

    blob_text = (temp_blobs / artifact[2]).read_text()
    assert "[EMAIL]" in blob_text
    assert "alice@company.com" not in blob_text
