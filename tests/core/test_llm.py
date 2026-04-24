from distill_core import llm
from distill_core.llm import extract_json


def test_extract_json_reads_plain_json():
    assert extract_json('{"ok": true}') == {"ok": True}


def test_extract_json_reads_json_from_code_fence():
    assert extract_json('```json\n{"ok": true}\n```') == {"ok": True}


def test_complete_openai_uses_max_completion_tokens(monkeypatch):
    captured = {}

    class FakeCompletions:
        def create(self, **kwargs):
            captured.update(kwargs)
            return type(
                "Resp",
                (),
                {
                    "choices": [
                        type(
                            "Choice",
                            (),
                            {"message": type("Message", (), {"content": "ok"})()},
                        )()
                    ]
                },
            )()

    class FakeChat:
        completions = FakeCompletions()

    class FakeClient:
        chat = FakeChat()

    monkeypatch.setattr(llm, "_openai_client", lambda: FakeClient())
    monkeypatch.setenv("LLM_PROVIDER", "openai")

    result = llm.complete(
        system="You are helpful.",
        user="Say ok",
        max_tokens=321,
        model="gpt-4.1-mini",
    )

    assert result == "ok"
    assert captured["max_completion_tokens"] == 321
    assert "max_tokens" not in captured
