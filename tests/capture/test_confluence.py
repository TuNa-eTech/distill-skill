import json
import sqlite3
from datetime import date

from distill_capture import ingest_confluence


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


def _page(page_id: str, *, updated: str, body: str):
    return {
        "id": page_id,
        "title": f"APP-101 ADR {page_id}",
        "status": "current",
        "history": {
            "createdDate": "2026-01-01T09:00:00.000Z",
            "createdBy": {"displayName": "Alice"},
        },
        "version": {
            "number": 3,
            "when": updated,
            "by": {"displayName": "Bob"},
        },
        "body": {"storage": {"value": body}},
        "metadata": {"labels": {"results": [{"name": "spec"}]}},
        "_links": {"webui": f"/wiki/spaces/MOB/pages/{page_id}"},
    }


def test_fetch_pages_respects_date_range_and_cap():
    page_in_range = _page(
        "2001",
        updated="2026-02-10T11:00:00.000Z",
        body="<p>APP-101 body</p>",
    )
    page_old = _page(
        "2002",
        updated="2025-12-31T11:00:00.000Z",
        body="<p>APP-102 body</p>",
    )
    session = FakeSession(
        [
            {"results": [page_in_range, page_old], "size": 2},
            {"results": [], "size": 0},
        ]
    )

    pages = ingest_confluence.fetch_pages(
        session=session,
        base_url="https://company.atlassian.net/wiki",
        space="MOB",
        since=date(2026, 1, 1),
        until=date(2026, 3, 31),
        cap=1,
    )

    assert [page["id"] for page in pages] == ["2001"]
    assert 'space = "MOB"' in session.calls[0][1]["cql"]


def test_run_ingest_persists_page_blob_and_metadata(temp_db, temp_blobs):
    page = _page(
        "2001",
        updated="2026-02-10T11:00:00.000Z",
        body="<p>APP-101 body and alice@company.com</p>",
    )
    session = FakeSession(
        [
            {"results": [page], "size": 1},
            {"results": [], "size": 0},
        ]
    )

    result = ingest_confluence.run_ingest(
        session=session,
        base_url="https://company.atlassian.net/wiki",
        space="MOB",
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
        row = conn.execute(
            "SELECT kind, external_id, metadata, blob_path FROM artifacts WHERE kind = 'confluence_page'"
        ).fetchone()

    assert row[0] == "confluence_page"
    assert row[1] == "page:2001"
    metadata = json.loads(row[2])
    assert metadata["space"] == "MOB"
    assert metadata["version_number"] == 3
    assert "APP-101" in metadata["body_text"]

    blob_text = (temp_blobs / row[3]).read_text()
    assert "[EMAIL]" in blob_text
    assert "alice@company.com" not in blob_text
