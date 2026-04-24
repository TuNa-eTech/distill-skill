from __future__ import annotations

import pytest
import yaml

from distill_evolve.validate import validate_module_text, validate_role_pack


def test_validate_module_reports_missing_citations():
    errors = validate_module_text(
        """
# State Management

## Rules
- Keep all state in one place.
""",
        module_name="state-management.md",
    )

    assert any("Missing citation" in error for error in errors)


@pytest.mark.parametrize(
    "section",
    ["Rules", "Templates", "Anti-patterns", "Pitfalls", "Hard rules"],
)
def test_validate_module_requires_two_distinct_sources_for_required_sections(section):
    errors = validate_module_text(
        f"""
# Module

## {section}
- Keep guidance grounded in evidence. [src: 1]
""",
        module_name="module.md",
    )

    assert any("at least 2 distinct source IDs" in error for error in errors)


def test_validate_module_rejects_duplicate_source_ids():
    errors = validate_module_text(
        """
# State Management

## Rules
- Keep async state transitions inside the cubit. [src: 1, 1]
""",
        module_name="state-management.md",
    )

    assert any("at least 2 distinct source IDs" in error for error in errors)


@pytest.mark.parametrize(
    "section",
    ["Rules", "Templates", "Anti-patterns", "Pitfalls", "Hard rules"],
)
def test_validate_module_accepts_two_distinct_sources_for_required_sections(section):
    errors = validate_module_text(
        f"""
# Module

## {section}
- Keep guidance grounded in evidence. [src: 1, 2]
""",
        module_name="module.md",
    )

    assert errors == []


def test_validate_pack_reports_total_token_budget_overflow(temp_packs):
    pack_root = temp_packs / "mobile-dev" / "v0.1"
    skills_dir = pack_root / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)
    (pack_root / "manifest.md").write_text("# Manifest\n", encoding="utf-8")
    (pack_root / "pack.yaml").write_text(
        yaml.safe_dump({"role": "mobile-dev", "version": "v0.1"}),
        encoding="utf-8",
    )
    huge_line = "- " + ("token " * 8000) + "[src: 1, 2]\n"
    (skills_dir / "state-management.md").write_text("# State Management\n\n## Rules\n" + huge_line)

    result = validate_role_pack(role="mobile-dev", packs_dir=temp_packs)

    assert result["ok"] is False
    assert any("exceeds the 3000-token cap" in error for error in result["errors"])


def test_validate_pack_checks_manifest_hard_rules_for_distinct_sources(temp_packs):
    pack_root = temp_packs / "mobile-dev" / "v0.1"
    skills_dir = pack_root / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)
    (pack_root / "manifest.md").write_text(
        "# Manifest\n\n## Hard rules\n- Keep reusable guidance generic. [src: 1]\n",
        encoding="utf-8",
    )
    (pack_root / "pack.yaml").write_text(
        yaml.safe_dump({"role": "mobile-dev", "version": "v0.1"}),
        encoding="utf-8",
    )
    (skills_dir / "state-management.md").write_text(
        "# State Management\n\n## Rules\n- Keep async state transitions inside the cubit. [src: 1, 2]\n",
        encoding="utf-8",
    )

    result = validate_role_pack(role="mobile-dev", packs_dir=temp_packs)

    assert result["ok"] is False
    assert any("manifest.md" in error for error in result["errors"])
    assert any("at least 2 distinct source IDs" in error for error in result["errors"])


def test_validate_pack_reports_missing_required_pack_files(temp_packs):
    result = validate_role_pack(role="mobile-dev", packs_dir=temp_packs)

    assert result["ok"] is False
    assert any("Missing manifest" in error for error in result["errors"])
    assert any("Missing pack metadata" in error for error in result["errors"])
