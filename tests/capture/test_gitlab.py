import json
import sqlite3
from datetime import date

from distill_capture import ingest_gitlab


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


def test_fetch_mrs_respects_date_range_and_cap():
    session = FakeSession(
        [
            [
                {
                    "iid": 101,
                    "title": "APP-101 navigation flow",
                    "updated_at": "2026-02-03T10:00:00Z",
                    "created_at": "2026-02-01T10:00:00Z",
                },
                {
                    "iid": 102,
                    "title": "Too old",
                    "updated_at": "2025-12-30T10:00:00Z",
                    "created_at": "2025-12-29T10:00:00Z",
                },
                {
                    "iid": 103,
                    "title": "Too new",
                    "updated_at": "2026-05-03T10:00:00Z",
                    "created_at": "2026-05-01T10:00:00Z",
                },
            ],
            [],
        ]
    )

    items = ingest_gitlab.fetch_mrs(
        session=session,
        base_url="https://gitlab.example.com",
        project_id="42",
        since=date(2026, 1, 1),
        until=date(2026, 3, 31),
        cap=1,
    )

    assert [item["iid"] for item in items] == [101]
    assert session.calls[0][1]["updated_after"].startswith("2026-01-01")
    assert session.calls[0][1]["updated_before"].startswith("2026-03-31")


def test_run_ingest_persists_artifact_and_redacted_blob(temp_db, temp_blobs):
    session = FakeSession(
        [
            [
                {
                    "iid": 101,
                    "title": "APP-101 add payment editor",
                    "description": "Implements APP-101 with review from alice@company.com",
                    "state": "merged",
                    "web_url": "https://gitlab.example.com/group/repo/-/merge_requests/101",
                    "source_branch": "feature/APP-101-payment-editor",
                    "target_branch": "main",
                    "labels": ["mobile", "flutter"],
                    "author": {"username": "alice"},
                    "created_at": "2026-02-01T10:00:00Z",
                    "updated_at": "2026-02-03T10:00:00Z",
                    "merged_at": "2026-02-03T11:00:00Z",
                }
            ],
            [
                {
                    "id": "discussion-1",
                    "resolved": True,
                    "notes": [
                        {
                            "body": "Looks good. Contact alice@company.com if you need more context.",
                        }
                    ],
                }
            ],
            [{"id": "commit-1", "message": "feat: add editor"}],
            {
                "changes": [
                    {"new_path": "lib/features/schedule/editor.dart"},
                    {"new_path": "test/features/schedule/editor_test.dart"},
                ]
            },
        ]
    )

    result = ingest_gitlab.run_ingest(
        session=session,
        base_url="https://gitlab.example.com",
        project_id="42",
        db_path=temp_db,
        blob_root=temp_blobs,
        since=date(2026, 1, 1),
        until=date(2026, 12, 31),
        max_items=10,
    )

    assert result["ingested"] == 1
    with sqlite3.connect(temp_db) as conn:
        row = conn.execute(
            "SELECT kind, external_id, metadata, blob_path FROM artifacts"
        ).fetchone()

    assert row[0] == "gitlab_mr"
    assert row[1] == "42!101"
    metadata = json.loads(row[2])
    assert metadata["changed_files"] == [
        "lib/features/schedule/editor.dart",
        "test/features/schedule/editor_test.dart",
    ]
    assert metadata["mobile_touch"] is True
    assert metadata["test_touch"] is True
    assert metadata["discussion_count"] == 1
    assert metadata["resolved_discussions"] == 1
    assert metadata["project_id"] == "42"
    assert metadata["project_path_with_namespace"] == "42"

    blob_text = (temp_blobs / row[3]).read_text()
    assert "[EMAIL]" in blob_text
    assert "alice@company.com" not in blob_text
