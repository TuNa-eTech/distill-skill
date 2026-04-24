from datetime import date

from distill_core import blob as blob_module
from distill_core.db import connect, init_schema
from distill_capture.ingest_confluence import build_session, run_ingest

from tests.support.fakes import FakeResponse, FakeSession


def test_build_session_uses_bearer_for_non_email_username():
    session = build_session(username="tuna30", token="secret", auth_mode="auto")

    assert session.auth == ("tuna30", "secret")
    assert "Authorization" not in session.headers


def test_ingest_confluence_persists_page_metadata_and_blob(tmp_path, monkeypatch):
    db_path = tmp_path / "distill.db"
    init_schema(db_path)
    monkeypatch.setattr(blob_module, "BLOBS_DIR", tmp_path / "blobs")

    session = FakeSession(
        responses={
            "/rest/api/content/search": [
                FakeResponse(
                    {
                        "results": [
                            {
                                "id": "9001",
                                "title": "APP-123 ADR payment schedule flow",
                                "status": "current",
                                "version": {"number": 3, "when": "2026-03-10T10:00:00Z"},
                                "history": {"createdDate": "2026-03-01T10:00:00Z"},
                                "body": {"storage": {"value": "Owner alice@example.com"}},
                            }
                        ],
                        "size": 1,
                        "limit": 50,
                    }
                ),
                FakeResponse({"results": [], "size": 0, "limit": 50}),
            ]
        }
    )

    result = run_ingest(
        session=session,
        base_url="https://confluence.example/wiki",
        space="MOBILE",
        username="user",
        token="token",
        db_path=db_path,
        blob_root=tmp_path / "blobs",
        since=date(2026, 1, 1),
        until=date(2026, 4, 24),
        max_items=20,
    )

    assert result["ingested"] == 1
    with connect(db_path) as conn:
        artifact = conn.execute("SELECT * FROM artifacts WHERE kind='confluence_page'").fetchone()

    assert artifact is not None
    blob_text = (tmp_path / "blobs" / artifact["blob_path"]).read_text(encoding="utf-8")
    assert "[EMAIL]" in blob_text
