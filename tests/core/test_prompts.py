from pathlib import Path

import pytest

from distill_core import prompts


def test_load_role_prompt_reads_existing_role_template():
    content = prompts.load_role_prompt("mobile-dev", "extract.system.md")

    assert "mobile engineering patterns" in content


def test_load_role_prompt_reads_tester_manual_role_template():
    content = prompts.load_role_prompt("tester-manual", "extract.system.md")

    assert "manual testing patterns" in content


def test_load_role_prompt_falls_back_to_shared_template():
    content = prompts.load_role_prompt("business-analyst", "extract.user.md")

    assert "Primary artifact metadata:" in content


def test_load_role_prompt_reports_attempted_paths(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    monkeypatch.setattr(prompts, "PROMPTS_DIR", tmp_path)

    with pytest.raises(FileNotFoundError) as exc_info:
        prompts.load_role_prompt("mobile-dev", "missing.md")

    assert "mobile-dev" in str(exc_info.value)
    assert "shared" in str(exc_info.value)


def test_render_role_prompt_substitutes_values():
    rendered = prompts.render_role_prompt(
        "mobile-dev",
        "extract.user.md",
        artifact_json='{"id": 1}',
        artifact_card="# Summary\nhello",
        supporting_artifacts_text="None.",
    )

    assert '{"id": 1}' in rendered
    assert "# Summary" in rendered
    assert "hello" in rendered
    assert "None." in rendered
