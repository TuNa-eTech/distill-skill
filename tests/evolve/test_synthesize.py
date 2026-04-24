from __future__ import annotations

import json
import yaml

from distill_core.prompts import load_role_prompt
from distill_evolve.synthesize import synthesize_role

from tests.support.seeds import seed_artifact, seed_cluster, seed_extraction, seed_score


def test_synthesize_role_writes_target_module_files_and_pack_metadata(
    db_conn, temp_db, temp_packs, monkeypatch
):
    monkeypatch.setenv("INGEST_SINCE", "2026-01-01")
    monkeypatch.setenv("INGEST_UNTIL", "2026-04-24")
    artifact_id = seed_artifact(
        db_conn,
        kind="gitlab_mr",
        external_id="401",
        metadata={"title": "State module improvements", "author_username": "alice"},
    )
    seed_score(db_conn, artifact_id=artifact_id, role="mobile-dev", score=9.5)
    cluster_id = seed_cluster(db_conn, role="mobile-dev", name="state management")
    seed_extraction(
        db_conn,
        artifact_id=artifact_id,
        cluster_id=cluster_id,
        payload={
            "artifact_id": artifact_id,
            "task_type": "state-improvement",
            "domain_tags": ["flutter", "state-management"],
            "patterns": [
                {
                    "kind": "convention",
                    "summary": "Keep async state transitions inside the cubit.",
                    "evidence_excerpt": "Keep async state transitions inside the cubit.",
                    "confidence": 0.9,
                }
            ],
            "files_touched": ["lib/features/payment/payment_cubit.dart"],
            "outcome_signal": "merged",
        },
    )

    written = synthesize_role(
        role="mobile-dev",
        db_path=temp_db,
        packs_dir=temp_packs,
        llm_callable=lambda **_: (
            """# State Management

## When this applies
- Flutter flows that touch Cubit, Bloc, Riverpod, or controller state.

## Rules
- Keep async state transitions inside the cubit. [src: 1, 1]

## Anti-patterns
- Do not mutate widget-local state and cubit state for the same value. [src: 1, 1]
"""
        ),
    )

    module_path = temp_packs / "mobile-dev" / "v0.1" / "skills" / "state-management.md"
    manifest_path = temp_packs / "mobile-dev" / "v0.1" / "manifest.md"
    pack_yaml_path = temp_packs / "mobile-dev" / "v0.1" / "pack.yaml"
    assert module_path in written["written"]
    assert module_path.exists()
    assert "[src: 1, 1]" in module_path.read_text()
    assert written["manifest"] == manifest_path
    assert written["pack_yaml"] == pack_yaml_path
    assert "## Hard rules" in manifest_path.read_text()

    pack_metadata = yaml.safe_load(pack_yaml_path.read_text())
    assert pack_metadata["role"] == "mobile-dev"
    assert pack_metadata["language"] == "vi"
    assert pack_metadata["source_window"] == "2026-01-01..2026-04-24"
    assert pack_metadata["contributors"] == 1
    assert pack_metadata["quality_signals"] == {
        "source_artifacts": 1,
        "filtered_in": 1,
        "filtered_out": 0,
        "modules_generated": 1,
    }
    assert pack_metadata["checksum"].startswith("sha256:")


def test_synthesize_prompt_is_vietnamese_first_and_discourages_app_specific_overfit():
    prompt = load_role_prompt("mobile-dev", "synthesize.system.md")

    assert "Vietnamese-first" in prompt
    assert "Keep code identifiers, file paths, route names, package names, env keys," in prompt
    assert "Do not turn app-specific feature names, internal class names, helper names," in prompt
    assert "at least **2 distinct** internal `artifact_id` values" in prompt
    assert "cite `extraction_id`" in prompt
    assert "multiple distinct artifacts" in prompt


def test_business_analyst_synthesize_writes_ba_pack_metadata(
    db_conn, temp_db, temp_packs, monkeypatch
):
    monkeypatch.setenv("INGEST_SINCE", "2026-01-01")
    monkeypatch.setenv("INGEST_UNTIL", "2026-04-24")
    artifact_id = seed_artifact(
        db_conn,
        kind="confluence_page",
        external_id="page:701",
        metadata={"title": "Checkout PRD", "updated_by": "alice"},
    )
    seed_score(db_conn, artifact_id=artifact_id, role="business-analyst", score=8.5)
    cluster_id = seed_cluster(db_conn, role="business-analyst", name="spec writing")
    seed_extraction(
        db_conn,
        artifact_id=artifact_id,
        cluster_id=cluster_id,
        payload={
            "artifact_id": artifact_id,
            "task_type": "write-spec",
            "domain_tags": ["spec-writing"],
            "patterns": [
                {
                    "kind": "template",
                    "summary": "State the problem and success metrics before proposing the solution.",
                    "evidence_excerpt": "Problem first.",
                    "confidence": 0.9,
                }
            ],
            "files_touched": [],
            "outcome_signal": "accepted",
        },
    )

    written = synthesize_role(
        role="business-analyst",
        db_path=temp_db,
        packs_dir=temp_packs,
        llm_callable=lambda **_: (
            """# Spec Writing

## When this applies
- Khi viết hoặc chỉnh PRD, spec, hoặc solution note.

## Rules
- Nêu rõ problem và success metrics trước khi chốt solution. [src: 1, 1]

## Templates
- Dùng skeleton gồm Problem, Success Metrics, Solution, Open Questions. [src: 1, 1]

## Pitfalls
- Đừng viết solution trước khi khóa problem. [src: 1, 1]
"""
        ),
    )

    module_path = temp_packs / "business-analyst" / "v0.1" / "skills" / "spec-writing.md"
    manifest_path = temp_packs / "business-analyst" / "v0.1" / "manifest.md"
    pack_yaml_path = temp_packs / "business-analyst" / "v0.1" / "pack.yaml"
    assert module_path in written["written"]
    assert "business analyst" in manifest_path.read_text(encoding="utf-8").lower()

    pack_metadata = yaml.safe_load(pack_yaml_path.read_text())
    assert pack_metadata["role"] == "business-analyst"
    assert pack_metadata["language"] == "vi"
    assert pack_metadata["contributors"] == 1


def test_tester_manual_synthesize_writes_tester_pack_metadata(
    db_conn, temp_db, temp_packs, monkeypatch
):
    monkeypatch.setenv("INGEST_SINCE", "2026-01-01")
    monkeypatch.setenv("INGEST_UNTIL", "2026-04-24")
    artifact_id = seed_artifact(
        db_conn,
        kind="jira_issue",
        external_id="QA-701",
        metadata={
            "summary": "Retry bug report",
            "reporter": "alice",
            "issue_type": "Bug",
        },
    )
    seed_score(db_conn, artifact_id=artifact_id, role="tester-manual", score=8.0)
    cluster_id = seed_cluster(db_conn, role="tester-manual", name="bug report quality")
    seed_extraction(
        db_conn,
        artifact_id=artifact_id,
        cluster_id=cluster_id,
        payload={
            "artifact_id": artifact_id,
            "task_type": "report-bug",
            "domain_tags": ["bug-report-quality"],
            "patterns": [
                {
                    "kind": "template",
                    "summary": "Ghi rõ steps to reproduce, actual result, và expected result.",
                    "evidence_excerpt": "Steps to reproduce.",
                    "confidence": 0.9,
                }
            ],
            "files_touched": [],
            "outcome_signal": "resolved",
        },
    )

    written = synthesize_role(
        role="tester-manual",
        db_path=temp_db,
        packs_dir=temp_packs,
        llm_callable=lambda **_: (
            """# Bug Report Quality

## When this applies
- Khi viết bug report hoặc refine defect ticket cho team dev xử lý.

## Rules
- Luôn ghi rõ steps to reproduce, actual result, và expected result. [src: 1, 1]

## Templates
- Dùng skeleton gồm Steps, Actual, Expected, Environment, Severity. [src: 1, 1]

## Pitfalls
- Đừng mở bug chỉ với một câu mơ hồ kiểu "không chạy". [src: 1, 1]
"""
        ),
    )

    module_path = temp_packs / "tester-manual" / "v0.1" / "skills" / "bug-report-quality.md"
    manifest_path = temp_packs / "tester-manual" / "v0.1" / "manifest.md"
    pack_yaml_path = temp_packs / "tester-manual" / "v0.1" / "pack.yaml"
    assert module_path in written["written"]
    assert "manual tester" in manifest_path.read_text(encoding="utf-8").lower()

    pack_metadata = yaml.safe_load(pack_yaml_path.read_text())
    assert pack_metadata["role"] == "tester-manual"
    assert pack_metadata["language"] == "vi"
    assert pack_metadata["contributors"] == 1


def test_synthesize_payload_uses_extraction_id_key_not_ambiguous_id(
    db_conn, temp_db, temp_packs, monkeypatch
):
    monkeypatch.setenv("INGEST_SINCE", "2026-01-01")
    monkeypatch.setenv("INGEST_UNTIL", "2026-04-24")
    artifact_id = seed_artifact(
        db_conn,
        kind="jira_issue",
        external_id="QA-702",
        metadata={"summary": "Retry bug", "reporter": "alice"},
    )
    seed_score(db_conn, artifact_id=artifact_id, role="tester-manual", score=7.0)
    cluster_id = seed_cluster(db_conn, role="tester-manual", name="bug report quality")
    seed_extraction(
        db_conn,
        artifact_id=artifact_id,
        role="tester-manual",
        cluster_id=cluster_id,
        payload={
            "artifact_id": artifact_id,
            "task_type": "report-bug",
            "domain_tags": ["bug-report-quality"],
            "patterns": [],
            "files_touched": [],
            "outcome_signal": "resolved",
        },
    )
    seen_payload: dict[str, object] = {}

    def llm_callable(**kwargs):
        seen_payload["value"] = json.loads(kwargs["user"])
        return """# Bug Report Quality

## When this applies
- Khi viết bug report.

## Rules
- Ghi rõ steps và expected/actual. [src: 1, 1]
"""

    synthesize_role(
        role="tester-manual",
        db_path=temp_db,
        packs_dir=temp_packs,
        llm_callable=llm_callable,
    )

    extraction_payload = seen_payload["value"]["extractions"][0]
    assert "id" not in extraction_payload
    assert extraction_payload["extraction_id"] >= 1


def test_synthesize_role_counts_plain_string_author_in_pack_metadata(
    db_conn, temp_db, temp_packs, monkeypatch
):
    monkeypatch.setenv("INGEST_SINCE", "2026-01-01")
    monkeypatch.setenv("INGEST_UNTIL", "2026-04-24")
    artifact_id = seed_artifact(
        db_conn,
        kind="gitlab_mr",
        external_id="402",
        metadata={"title": "Navigation cleanup", "author": "alice"},
    )
    seed_score(db_conn, artifact_id=artifact_id, role="mobile-dev", score=8.0)
    cluster_id = seed_cluster(db_conn, role="mobile-dev", name="navigation")
    seed_extraction(
        db_conn,
        artifact_id=artifact_id,
        cluster_id=cluster_id,
        payload={
            "artifact_id": artifact_id,
            "task_type": "navigation-cleanup",
            "domain_tags": ["flutter", "navigation"],
            "patterns": [
                {
                    "kind": "convention",
                    "summary": "Keep route decisions in one coordinator.",
                    "evidence_excerpt": "Centralize route decisions.",
                    "confidence": 0.9,
                }
            ],
            "files_touched": ["lib/navigation/app_router.dart"],
            "outcome_signal": "merged",
        },
    )

    synthesize_role(
        role="mobile-dev",
        db_path=temp_db,
        packs_dir=temp_packs,
        llm_callable=lambda **_: (
            """# Navigation

## When this applies
- Flutter flows that change routes or screen hand-off behavior.

## Rules
- Keep route decisions in one coordinator. [src: 1, 1]
"""
        ),
    )

    pack_yaml_path = temp_packs / "mobile-dev" / "v0.1" / "pack.yaml"
    pack_metadata = yaml.safe_load(pack_yaml_path.read_text())

    assert pack_metadata["contributors"] == 1


def test_synthesize_role_only_promotes_repeated_patterns_into_manifest_hard_rules(
    db_conn, temp_db, temp_packs, monkeypatch
):
    monkeypatch.setenv("INGEST_SINCE", "2026-01-01")
    monkeypatch.setenv("INGEST_UNTIL", "2026-04-24")
    cluster_id = seed_cluster(db_conn, role="mobile-dev", name="state management")

    first_artifact_id = seed_artifact(
        db_conn,
        kind="gitlab_mr",
        external_id="501",
        metadata={"title": "Flow cleanup", "author_username": "alice"},
    )
    second_artifact_id = seed_artifact(
        db_conn,
        kind="gitlab_mr",
        external_id="502",
        metadata={"title": "Flow cleanup follow-up", "author_username": "bob"},
    )
    seed_score(db_conn, artifact_id=first_artifact_id, role="mobile-dev", score=9.0)
    seed_score(db_conn, artifact_id=second_artifact_id, role="mobile-dev", score=8.8)
    for artifact_id in (first_artifact_id, second_artifact_id):
        seed_extraction(
            db_conn,
            artifact_id=artifact_id,
            cluster_id=cluster_id,
            payload={
                "artifact_id": artifact_id,
                "task_type": "state-cleanup",
                "domain_tags": ["flutter", "state-management"],
                "patterns": [
                    {
                        "kind": "convention",
                        "summary": "Keep async state transitions inside the cubit.",
                        "evidence_excerpt": "Keep async state transitions inside the cubit.",
                        "confidence": 0.9,
                    }
                ],
                "files_touched": ["lib/features/payment/payment_cubit.dart"],
                "outcome_signal": "merged",
            },
        )

    synthesize_role(
        role="mobile-dev",
        db_path=temp_db,
        packs_dir=temp_packs,
        llm_callable=lambda **_: (
            """# State Management

## When this applies
- Flutter flows that touch Cubit or Bloc state.

## Rules
- Keep async state transitions inside the cubit. [src: 1, 2]
"""
        ),
    )

    manifest_text = (temp_packs / "mobile-dev" / "v0.1" / "manifest.md").read_text(encoding="utf-8")

    assert "## Hard rules" in manifest_text
    assert "[src: 1, 2]" in manifest_text
