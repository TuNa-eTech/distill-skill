from datetime import date
from pathlib import Path

from distill_capture import ingest_gitlab as ingest_gitlab_module
from distill_core import blob as blob_module
from distill_core.db import connect, init_schema
from distill_capture.ingest_gitlab import run_ingest

from tests.support.fakes import FakeResponse, FakeSession


def test_ingest_gitlab_persists_artifact_and_redacted_blob(tmp_path, monkeypatch):
    db_path = tmp_path / "distill.db"
    init_schema(db_path)
    monkeypatch.setattr(blob_module, "BLOBS_DIR", tmp_path / "blobs")

    session = FakeSession(
        responses={
            "/api/v4/projects/42/merge_requests": [
                FakeResponse(
                    [
                        {
                            "iid": 101,
                            "title": "APP-123 add payment edit flow",
                            "description": "Contact alice@example.com",
                            "state": "merged",
                            "source_branch": "feature/APP-123-payment-edit",
                            "target_branch": "main",
                            "merged_at": "2026-02-15T10:00:00Z",
                            "updated_at": "2026-02-15T10:00:00Z",
                            "created_at": "2026-02-10T10:00:00Z",
                            "labels": ["mobile"],
                            "web_url": "https://gitlab.example/mr/101",
                            "author": {"username": "alice"},
                        }
                    ]
                ),
                FakeResponse([]),
            ],
            "/api/v4/projects/42/merge_requests/101/discussions": FakeResponse(
                [{"notes": [{"body": "Reviewed by bob@example.com"}]}]
            ),
            "/api/v4/projects/42/merge_requests/101/commits": FakeResponse([{"id": "abc123"}]),
            "/api/v4/projects/42/merge_requests/101/changes": FakeResponse(
                {
                    "changes": [
                        {"new_path": "lib/features/payments/edit_flow.dart"},
                        {"new_path": "test/edit_flow_test.dart"},
                    ]
                }
            ),
        }
    )

    result = run_ingest(
        session=session,
        base_url="https://gitlab.example",
        project_id="42",
        db_path=db_path,
        blob_root=tmp_path / "blobs",
        since=date(2026, 1, 1),
        until=date(2026, 4, 24),
        max_items=10,
    )

    assert result["ingested"] == 1

    with connect(db_path) as conn:
        artifact = conn.execute("SELECT * FROM artifacts WHERE kind='gitlab_mr'").fetchone()

    assert artifact is not None
    assert artifact["external_id"] == "42!101"
    blob_text = (tmp_path / "blobs" / Path(artifact["blob_path"])).read_text(encoding="utf-8")
    assert "[EMAIL]" in blob_text
    assert "lib/features/payments/edit_flow.dart" in blob_text


def test_ingest_gitlab_is_idempotent(tmp_path, monkeypatch):
    db_path = tmp_path / "distill.db"
    init_schema(db_path)
    monkeypatch.setattr(blob_module, "BLOBS_DIR", tmp_path / "blobs")

    responses = {
        "/api/v4/projects/42/merge_requests": [
            FakeResponse(
                [
                    {
                        "iid": 101,
                        "title": "APP-123 add payment edit flow",
                        "description": "",
                        "state": "merged",
                        "source_branch": "feature/APP-123-payment-edit",
                        "target_branch": "main",
                        "merged_at": "2026-02-15T10:00:00Z",
                        "updated_at": "2026-02-15T10:00:00Z",
                        "created_at": "2026-02-10T10:00:00Z",
                        "labels": [],
                        "web_url": "https://gitlab.example/mr/101",
                        "author": {"username": "alice"},
                    }
                ]
            ),
            FakeResponse([]),
            FakeResponse(
                [
                    {
                        "iid": 101,
                        "title": "APP-123 add payment edit flow",
                        "description": "",
                        "state": "merged",
                        "source_branch": "feature/APP-123-payment-edit",
                        "target_branch": "main",
                        "merged_at": "2026-02-15T10:00:00Z",
                        "updated_at": "2026-02-15T10:00:00Z",
                        "created_at": "2026-02-10T10:00:00Z",
                        "labels": [],
                        "web_url": "https://gitlab.example/mr/101",
                        "author": {"username": "alice"},
                    }
                ]
            ),
            FakeResponse([]),
        ],
        "/api/v4/projects/42/merge_requests/101/discussions": [
            FakeResponse([]),
            FakeResponse([]),
        ],
        "/api/v4/projects/42/merge_requests/101/commits": [
            FakeResponse([]),
            FakeResponse([]),
        ],
        "/api/v4/projects/42/merge_requests/101/changes": [
            FakeResponse({"changes": []}),
            FakeResponse({"changes": []}),
        ],
    }
    session = FakeSession(responses=responses)

    run_ingest(
        session=session,
        base_url="https://gitlab.example",
        project_id="42",
        db_path=db_path,
        blob_root=tmp_path / "blobs",
        since=date(2026, 1, 1),
        until=date(2026, 4, 24),
        max_items=10,
    )
    run_ingest(
        session=session,
        base_url="https://gitlab.example",
        project_id="42",
        db_path=db_path,
        blob_root=tmp_path / "blobs",
        since=date(2026, 1, 1),
        until=date(2026, 4, 24),
        max_items=10,
    )

    with connect(db_path) as conn:
        count = conn.execute("SELECT COUNT(*) FROM artifacts WHERE kind='gitlab_mr'").fetchone()[0]

    assert count == 1


def test_ingest_gitlab_supports_group_targets_and_unique_mr_ids(tmp_path, monkeypatch):
    db_path = tmp_path / "distill.db"
    init_schema(db_path)
    monkeypatch.setattr(blob_module, "BLOBS_DIR", tmp_path / "blobs")

    session = FakeSession(
        responses={
            "/api/v4/projects/100": FakeResponse(
                {"message": "404 Project Not Found"}, status_code=404
            ),
            "/api/v4/groups/100/projects": FakeResponse(
                [
                    {
                        "id": 42,
                        "path_with_namespace": "mobile-team/repo-a",
                        "web_url": "https://gitlab.example/mobile-team/repo-a",
                        "last_activity_at": "2026-04-24T10:00:00Z",
                    },
                    {
                        "id": 43,
                        "path_with_namespace": "mobile-team/repo-b",
                        "web_url": "https://gitlab.example/mobile-team/repo-b",
                        "last_activity_at": "2026-04-24T09:00:00Z",
                    },
                ]
            ),
            "/api/v4/projects/42/merge_requests": FakeResponse(
                [
                    {
                        "iid": 101,
                        "title": "APP-123 repo a change",
                        "description": "",
                        "state": "merged",
                        "source_branch": "feature/APP-123-a",
                        "target_branch": "main",
                        "merged_at": "2026-02-15T10:00:00Z",
                        "updated_at": "2026-02-15T10:00:00Z",
                        "created_at": "2026-02-10T10:00:00Z",
                        "labels": ["mobile"],
                        "web_url": "https://gitlab.example/repo-a/mr/101",
                        "author": {"username": "alice"},
                    }
                ]
            ),
            "/api/v4/projects/43/merge_requests": FakeResponse(
                [
                    {
                        "iid": 101,
                        "title": "APP-123 repo b change",
                        "description": "",
                        "state": "merged",
                        "source_branch": "feature/APP-123-b",
                        "target_branch": "main",
                        "merged_at": "2026-02-16T10:00:00Z",
                        "updated_at": "2026-02-16T10:00:00Z",
                        "created_at": "2026-02-11T10:00:00Z",
                        "labels": ["mobile"],
                        "web_url": "https://gitlab.example/repo-b/mr/101",
                        "author": {"username": "bob"},
                    }
                ]
            ),
            "/api/v4/projects/42/merge_requests/101/discussions": FakeResponse([]),
            "/api/v4/projects/42/merge_requests/101/commits": FakeResponse([]),
            "/api/v4/projects/42/merge_requests/101/changes": FakeResponse(
                {"changes": [{"new_path": "lib/repo_a.dart"}]}
            ),
            "/api/v4/projects/43/merge_requests/101/discussions": FakeResponse([]),
            "/api/v4/projects/43/merge_requests/101/commits": FakeResponse([]),
            "/api/v4/projects/43/merge_requests/101/changes": FakeResponse(
                {"changes": [{"new_path": "lib/repo_b.dart"}]}
            ),
        }
    )

    result = ingest_gitlab_module.ingest_gitlab(
        since="2026-01-01",
        until="2026-04-24",
        limit=10,
        session=session,
        db_path=db_path,
        base_url="https://gitlab.example",
        project_id="100",
    )

    assert result == 2
    with connect(db_path) as conn:
        rows = conn.execute(
            "SELECT external_id, metadata, blob_path FROM artifacts WHERE kind='gitlab_mr' ORDER BY external_id"
        ).fetchall()

    assert [row["external_id"] for row in rows] == ["42!101", "43!101"]
    assert [Path(row["blob_path"]).as_posix() for row in rows] == [
        "gitlab/mr/42/101.json",
        "gitlab/mr/43/101.json",
    ]
