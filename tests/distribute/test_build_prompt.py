from pathlib import Path

import pytest

from distill_distribute import build_prompt, pack


def _write_pack(root: Path, role: str = "mobile-dev", version: str = "v0.1") -> None:
    pack_root = root / role / version
    skills_root = pack_root / "skills"
    skills_root.mkdir(parents=True)

    (pack_root / "manifest.md").write_text("Manifest hard rules", encoding="utf-8")
    (skills_root / "widget-testing.md").write_text("Widget testing guidance", encoding="utf-8")
    (skills_root / "code-review-conventions.md").write_text(
        "Code review conventions",
        encoding="utf-8",
    )


def test_build_prompt_composes_manifest_modules_and_task_deterministically(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    packs_root = tmp_path / "packs"
    _write_pack(packs_root)
    monkeypatch.setattr(pack, "PACKS_DIR", packs_root)

    prompt = build_prompt.build_prompt_text(
        role="mobile-dev",
        version="v0.1",
        task="Implement payment schedule edit flow in Flutter",
    )

    assert prompt == (
        "# Distill Skill Pack\n"
        "Role: mobile-dev\n"
        "Version: v0.1\n\n"
        "## Manifest\n"
        "Manifest hard rules\n\n"
        "## Skill Module: code-review-conventions\n"
        "Code review conventions\n\n"
        "## Skill Module: widget-testing\n"
        "Widget testing guidance\n\n"
        "## Task\n"
        "Implement payment schedule edit flow in Flutter\n"
    )


def test_build_prompt_main_exits_with_missing_pack_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(pack, "PACKS_DIR", tmp_path / "packs")
    monkeypatch.setattr(
        "sys.argv",
        [
            "distill-build-prompt",
            "--role",
            "mobile-dev",
            "--task",
            "Implement payment schedule edit flow in Flutter",
        ],
    )

    with pytest.raises(SystemExit) as exc_info:
        build_prompt.main()

    captured = capsys.readouterr()
    assert exc_info.value.code == 2
    assert "Pack not found" in captured.err


def test_build_prompt_supports_business_analyst_pack(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    packs_root = tmp_path / "packs"
    _write_pack(packs_root, role="business-analyst")
    monkeypatch.setattr(pack, "PACKS_DIR", packs_root)

    prompt = build_prompt.build_prompt_text(
        role="business-analyst",
        version="v0.1",
        task="Draft acceptance criteria for checkout retry flow",
    )

    assert "Role: business-analyst" in prompt
    assert "Draft acceptance criteria for checkout retry flow" in prompt


def test_build_prompt_supports_tester_manual_pack(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    packs_root = tmp_path / "packs"
    _write_pack(packs_root, role="tester-manual")
    monkeypatch.setattr(pack, "PACKS_DIR", packs_root)

    prompt = build_prompt.build_prompt_text(
        role="tester-manual",
        version="v0.1",
        task="Viết regression checklist cho release checkout retry",
    )

    assert "Role: tester-manual" in prompt
    assert "Viết regression checklist cho release checkout retry" in prompt
