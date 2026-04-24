import json

from distill_core import blob as blob_module


def test_save_redacted_json_blob_sanitizes_id_and_redacts(tmp_path, monkeypatch):
    monkeypatch.setattr(blob_module, "BLOBS_DIR", tmp_path)

    rel_path = blob_module.save_redacted_json_blob(
        "gitlab/mr",
        "MR: 12/34",
        {"email": "alice@example.com", "title": "Hello"},
    )

    assert rel_path == "gitlab/mr/MR___12__34.json"
    content = (tmp_path / rel_path).read_text(encoding="utf-8")
    payload = json.loads(content)
    assert payload["email"] == "[EMAIL]"
    assert payload["title"] == "Hello"


def test_load_blob_text_reads_saved_file(tmp_path, monkeypatch):
    monkeypatch.setattr(blob_module, "BLOBS_DIR", tmp_path)
    path = tmp_path / "jira/issue/PROJ-1.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{}", encoding="utf-8")

    assert blob_module.load_blob_text("jira/issue/PROJ-1.json") == "{}"
