from __future__ import annotations

import json

from distill_core.db import connect
from distill_distribute import build_prompt, pack
from distill_evolve.cluster import cluster_extractions
from distill_evolve.extract import run_extraction
from distill_evolve.score import score_role
from distill_evolve.synthesize import synthesize_role
from distill_evolve.trace import trace_module
from distill_evolve.validate import validate_role_pack

from tests.support.seeds import seed_artifact, write_blob


def test_mobile_dev_pipeline_smoke(db_conn, temp_db, temp_blobs, temp_packs, monkeypatch):
    monkeypatch.setenv("INGEST_SINCE", "2026-01-01")
    monkeypatch.setenv("INGEST_UNTIL", "2026-04-24")

    blob_one = write_blob(
        temp_blobs,
        "gitlab_mr/601.json",
        {"title": "Payment flow state update", "description": "Cubit handles async UI states."},
    )
    mr_one = seed_artifact(
        db_conn,
        kind="gitlab_mr",
        external_id="601",
        blob_path=blob_one,
        metadata={
            "state": "merged",
            "title": "Payment flow state update",
            "changed_files": [
                "lib/features/payment/payment_cubit.dart",
                "test/features/payment/payment_cubit_test.dart",
            ],
            "discussion_count": 2,
            "resolved_discussion_count": 1,
            "author_username": "alice",
        },
    )
    blob_two = write_blob(
        temp_blobs,
        "gitlab_mr/602.json",
        {
            "title": "Invoice flow state cleanup",
            "description": "Keep transient state in the cubit.",
        },
    )
    mr_two = seed_artifact(
        db_conn,
        kind="gitlab_mr",
        external_id="602",
        blob_path=blob_two,
        metadata={
            "state": "merged",
            "title": "Invoice flow state cleanup",
            "changed_files": [
                "lib/features/invoice/invoice_cubit.dart",
                "test/features/invoice/invoice_cubit_test.dart",
            ],
            "discussion_count": 2,
            "resolved_discussion_count": 1,
            "author_username": "bob",
        },
    )

    score_summary = score_role(role="mobile-dev", db_path=temp_db)
    assert score_summary == {"role": "mobile-dev", "count": 2}

    extract_summary = run_extraction(
        role="mobile-dev",
        db_path=temp_db,
        blobs_dir=temp_blobs,
        llm_callable=lambda **_: json.dumps(
            {
                "artifact_id": 0,
                "task_type": "state-cleanup",
                "domain_tags": ["flutter", "state-management"],
                "patterns": [
                    {
                        "kind": "convention",
                        "summary": "Keep async state transitions inside the cubit.",
                        "evidence_excerpt": "Cubit handles async UI states.",
                        "confidence": 0.9,
                    }
                ],
                "files_touched": ["lib/features/payment/payment_cubit.dart"],
                "outcome_signal": "merged",
            }
        ),
        model="gpt-4o-mini",
    )
    assert extract_summary == {"processed": 2, "inserted": 2, "failed": 0, "skipped": 0}

    answers = iter(["new", "state-management", "state-management"])
    with connect(temp_db) as conn:
        cluster_summary = cluster_extractions(
            conn,
            role="mobile-dev",
            input_fn=lambda _: next(answers),
            output_fn=lambda _: None,
        )
    assert cluster_summary == {
        "processed": 2,
        "assigned": 2,
        "skipped": 0,
        "created_clusters": 1,
    }

    synthesize_summary = synthesize_role(
        role="mobile-dev",
        db_path=temp_db,
        packs_dir=temp_packs,
        llm_callable=lambda **_: (
            f"""# State Management

## When this applies
- Flutter flows that touch Cubit, Bloc, Riverpod, or controller state.

## Hard rules
- Keep async state transitions inside the cubit. [src: {mr_one}, {mr_two}]

## Pitfalls
- Do not duplicate widget-local state and cubit state. [src: {mr_one}, {mr_two}]
"""
        ),
        model="gpt-4o-mini",
    )
    module_path = temp_packs / "mobile-dev" / "v0.1" / "skills" / "state-management.md"
    assert synthesize_summary["written"] == [module_path]
    assert module_path.exists()

    validation = validate_role_pack(role="mobile-dev", packs_dir=temp_packs)
    assert validation["ok"] is True

    monkeypatch.setattr(pack, "PACKS_DIR", temp_packs)
    prompt = build_prompt.build_prompt_text(
        role="mobile-dev",
        version="v0.1",
        task="Implement payment schedule edit flow in Flutter",
    )
    assert "## Manifest" in prompt
    assert "## Skill Module: state-management" in prompt
    assert "Implement payment schedule edit flow in Flutter" in prompt

    trace = trace_module(module_path=module_path, db_path=temp_db)
    assert set(trace.keys()) == {mr_one, mr_two}


def test_business_analyst_pipeline_smoke(db_conn, temp_db, temp_blobs, temp_packs, monkeypatch):
    monkeypatch.setenv("INGEST_SINCE", "2026-01-01")
    monkeypatch.setenv("INGEST_UNTIL", "2026-04-24")

    jira_blob = write_blob(
        temp_blobs,
        "jira/issue/801.json",
        {
            "fields": {
                "summary": "Checkout story",
                "description": (
                    "Acceptance Criteria:\n"
                    "Given a returning customer\n"
                    "When payment succeeds\n"
                    "Then show confirmation."
                ),
            }
        },
    )
    issue_id = seed_artifact(
        db_conn,
        kind="jira_issue",
        external_id="BA-801",
        blob_path=jira_blob,
        metadata={
            "status": "Done",
            "summary": "Checkout story",
            "description": (
                "Acceptance Criteria: Given a returning customer, when payment succeeds, then "
                "show confirmation and keep open questions explicit."
            ),
            "comment_count": 3,
            "reporter": "alice",
        },
    )
    page_blob = write_blob(
        temp_blobs,
        "confluence/page/802.json",
        {
            "title": "Checkout PRD",
            "body": {
                "storage": {
                    "value": (
                        "<h1>Problem</h1><p>Checkout drop-off is high.</p>"
                        "<h2>Success metrics</h2><p>Improve conversion.</p>"
                    )
                }
            },
        },
    )
    page_id = seed_artifact(
        db_conn,
        kind="confluence_page",
        external_id="page:802",
        blob_path=page_blob,
        metadata={
            "title": "Checkout PRD",
            "body_text": (
                "Problem: Checkout drop-off is high. Success metrics: improve conversion. "
                "Out of scope: loyalty redesign. Open questions: fallback path."
            ),
            "labels": ["spec"],
            "updated_by": "bob",
        },
    )
    db_conn.execute(
        """
        INSERT INTO links (source_id, target_id, link_type, confidence)
        VALUES (?, ?, ?, ?)
        """,
        (page_id, issue_id, "references_jira", 1.0),
    )
    db_conn.commit()

    score_summary = score_role(role="business-analyst", db_path=temp_db)
    assert score_summary == {"role": "business-analyst", "count": 2}

    llm_outputs = iter(
        [
            json.dumps(
                {
                    "artifact_id": 0,
                    "task_type": "draft-ac",
                    "domain_tags": ["acceptance-criteria", "checkout"],
                    "patterns": [
                        {
                            "kind": "template",
                            "summary": "Write acceptance criteria in observable Given/When/Then form.",
                            "evidence_excerpt": "Acceptance Criteria:",
                            "confidence": 0.9,
                        }
                    ],
                    "files_touched": [],
                    "outcome_signal": "done",
                }
            ),
            json.dumps(
                {
                    "artifact_id": 0,
                    "task_type": "write-spec",
                    "domain_tags": ["spec-writing", "checkout"],
                    "patterns": [
                        {
                            "kind": "convention",
                            "summary": "State the problem, success metrics, and open questions before locking solution scope.",
                            "evidence_excerpt": "Problem: Checkout drop-off is high.",
                            "confidence": 0.9,
                        }
                    ],
                    "files_touched": [],
                    "outcome_signal": "accepted",
                }
            ),
        ]
    )
    extract_summary = run_extraction(
        role="business-analyst",
        db_path=temp_db,
        blobs_dir=temp_blobs,
        llm_callable=lambda **_: next(llm_outputs),
        model="gpt-4o-mini",
    )
    assert extract_summary == {"processed": 2, "inserted": 2, "failed": 0, "skipped": 0}

    answers = iter(["new", "spec-writing", "new", "acceptance-criteria"])
    with connect(temp_db) as conn:
        cluster_summary = cluster_extractions(
            conn,
            role="business-analyst",
            input_fn=lambda _: next(answers),
            output_fn=lambda _: None,
        )
    assert cluster_summary == {
        "processed": 2,
        "assigned": 2,
        "skipped": 0,
        "created_clusters": 2,
    }

    def ba_synthesizer(**kwargs):
        payload = json.loads(kwargs["user"])
        module_slug = payload["cluster"]["module_slug"]
        if module_slug == "spec-writing":
            return f"""# Spec Writing

## When this applies
- Khi viết hoặc chỉnh PRD, spec, hoặc solution note.

## Rules
- Nêu rõ problem, success metrics, và open questions trước khi chốt solution. [src: {issue_id}, {page_id}]

## Templates
- Dùng skeleton gồm Problem, Success Metrics, Out of Scope, và Open Questions. [src: {issue_id}, {page_id}]

## Pitfalls
- Đừng để solution đi trước problem framing và scope clarity. [src: {issue_id}, {page_id}]
"""
        return f"""# Acceptance Criteria

## When this applies
- Khi viết user story, AC, hoặc mô tả behavior cần verify.

## Rules
- Viết AC theo Given/When/Then với outcome quan sát được. [src: {issue_id}, {page_id}]

## Templates
- Dùng format GIVEN / WHEN / THEN cho từng scenario chính và edge case. [src: {issue_id}, {page_id}]

## Pitfalls
- Tránh câu chữ mơ hồ kiểu "should support" mà không mô tả behavior cụ thể. [src: {issue_id}, {page_id}]
"""

    synthesize_summary = synthesize_role(
        role="business-analyst",
        db_path=temp_db,
        packs_dir=temp_packs,
        llm_callable=ba_synthesizer,
        model="gpt-4o-mini",
    )
    spec_module = temp_packs / "business-analyst" / "v0.1" / "skills" / "spec-writing.md"
    ac_module = temp_packs / "business-analyst" / "v0.1" / "skills" / "acceptance-criteria.md"
    assert synthesize_summary["written"] == [ac_module, spec_module] or synthesize_summary[
        "written"
    ] == [spec_module, ac_module]
    assert spec_module.exists()
    assert ac_module.exists()

    validation = validate_role_pack(role="business-analyst", packs_dir=temp_packs)
    assert validation["ok"] is True

    monkeypatch.setattr(pack, "PACKS_DIR", temp_packs)
    prompt = build_prompt.build_prompt_text(
        role="business-analyst",
        version="v0.1",
        task="Draft acceptance criteria for checkout retry flow",
    )
    assert "## Skill Module: acceptance-criteria" in prompt
    assert "## Skill Module: spec-writing" in prompt
    assert "Draft acceptance criteria for checkout retry flow" in prompt


def test_tester_manual_pipeline_smoke(db_conn, temp_db, temp_blobs, temp_packs, monkeypatch):
    monkeypatch.setenv("INGEST_SINCE", "2026-01-01")
    monkeypatch.setenv("INGEST_UNTIL", "2026-04-24")

    bug_blob = write_blob(
        temp_blobs,
        "jira/issue/901.json",
        {
            "fields": {
                "summary": "Checkout retry keeps stale error banner",
                "description": (
                    "Steps to reproduce: retry failed payment. "
                    "Actual result: stale error remains. "
                    "Expected result: error clears."
                ),
            }
        },
    )
    bug_id = seed_artifact(
        db_conn,
        kind="jira_issue",
        external_id="QA-901",
        blob_path=bug_blob,
        metadata={
            "status": "Resolved",
            "issue_type": "Bug",
            "summary": "Checkout retry keeps stale error banner",
            "description": (
                "Steps to reproduce: retry failed payment. "
                "Actual result: stale error remains. "
                "Expected result: error clears. "
                "Environment: iOS 17."
            ),
            "comment_count": 2,
            "reporter": "alice",
        },
    )
    checklist_blob = write_blob(
        temp_blobs,
        "jira/issue/902.json",
        {
            "fields": {
                "summary": "Regression checklist for checkout retry",
                "description": (
                    "Regression checklist: main flow, declined card, offline retry, duplicate tap. "
                    "Test cases cover happy path and edge cases."
                ),
            }
        },
    )
    checklist_id = seed_artifact(
        db_conn,
        kind="jira_issue",
        external_id="QA-902",
        blob_path=checklist_blob,
        metadata={
            "status": "Done",
            "issue_type": "Story",
            "summary": "Regression checklist for checkout retry",
            "description": (
                "Regression checklist: main flow, declined card, offline retry, duplicate tap. "
                "Test cases cover happy path and edge cases."
            ),
            "comment_count": 1,
            "reporter": "bob",
        },
    )

    score_summary = score_role(role="tester-manual", db_path=temp_db)
    assert score_summary == {"role": "tester-manual", "count": 2}

    llm_outputs = iter(
        [
            json.dumps(
                {
                    "artifact_id": 0,
                    "task_type": "report-bug",
                    "domain_tags": ["bug-report-quality", "checkout"],
                    "patterns": [
                        {
                            "kind": "template",
                            "summary": "Ghi rõ steps to reproduce, actual result, expected result, và environment.",
                            "evidence_excerpt": "Steps to reproduce: retry failed payment.",
                            "confidence": 0.9,
                        }
                    ],
                    "files_touched": [],
                    "outcome_signal": "resolved",
                }
            ),
            json.dumps(
                {
                    "artifact_id": 0,
                    "task_type": "plan-regression",
                    "domain_tags": ["regression-strategy", "checkout"],
                    "patterns": [
                        {
                            "kind": "template",
                            "summary": "Lập regression checklist theo main flow, failure path, và edge case trước release.",
                            "evidence_excerpt": "Regression checklist: main flow, declined card, offline retry, duplicate tap.",
                            "confidence": 0.9,
                        }
                    ],
                    "files_touched": [],
                    "outcome_signal": "done",
                }
            ),
        ]
    )
    extract_summary = run_extraction(
        role="tester-manual",
        db_path=temp_db,
        blobs_dir=temp_blobs,
        llm_callable=lambda **_: next(llm_outputs),
        model="gpt-4o-mini",
    )
    assert extract_summary == {"processed": 2, "inserted": 2, "failed": 0, "skipped": 0}

    answers = iter(["new", "bug-report-quality", "new", "regression-strategy"])
    with connect(temp_db) as conn:
        cluster_summary = cluster_extractions(
            conn,
            role="tester-manual",
            input_fn=lambda _: next(answers),
            output_fn=lambda _: None,
        )
    assert cluster_summary == {
        "processed": 2,
        "assigned": 2,
        "skipped": 0,
        "created_clusters": 2,
    }

    def tester_synthesizer(**kwargs):
        payload = json.loads(kwargs["user"])
        module_slug = payload["cluster"]["module_slug"]
        if module_slug == "bug-report-quality":
            return f"""# Bug Report Quality

## When this applies
- Khi viết hoặc refine defect ticket cho team dev xử lý.

## Rules
- Luôn ghi rõ steps to reproduce, actual result, expected result, và environment. [src: {bug_id}, {checklist_id}]

## Templates
- Dùng skeleton gồm Steps, Actual, Expected, Environment, Severity. [src: {bug_id}, {checklist_id}]

## Pitfalls
- Đừng dùng bug title mơ hồ hoặc mô tả chỉ có một câu. [src: {bug_id}, {checklist_id}]
"""
        return f"""# Regression Strategy

## When this applies
- Khi lên checklist regression cho bugfix, release, hoặc hotfix.

## Rules
- Chốt regression scope theo main flow, failure path, và edge case có rủi ro cao nhất. [src: {bug_id}, {checklist_id}]

## Templates
- Dùng checklist gồm happy path, retry path, negative path, và environment matrix tối thiểu. [src: {bug_id}, {checklist_id}]

## Pitfalls
- Đừng chỉ retest bug fix mà bỏ qua các flow kề bên có shared state hoặc shared API. [src: {bug_id}, {checklist_id}]
"""

    synthesize_summary = synthesize_role(
        role="tester-manual",
        db_path=temp_db,
        packs_dir=temp_packs,
        llm_callable=tester_synthesizer,
        model="gpt-4o-mini",
    )
    bug_module = temp_packs / "tester-manual" / "v0.1" / "skills" / "bug-report-quality.md"
    regression_module = temp_packs / "tester-manual" / "v0.1" / "skills" / "regression-strategy.md"
    assert synthesize_summary["written"] == [bug_module, regression_module] or synthesize_summary[
        "written"
    ] == [regression_module, bug_module]
    assert bug_module.exists()
    assert regression_module.exists()

    validation = validate_role_pack(role="tester-manual", packs_dir=temp_packs)
    assert validation["ok"] is True

    monkeypatch.setattr(pack, "PACKS_DIR", temp_packs)
    prompt = build_prompt.build_prompt_text(
        role="tester-manual",
        version="v0.1",
        task="Viết regression checklist cho release checkout retry",
    )
    assert "## Skill Module: bug-report-quality" in prompt
    assert "## Skill Module: regression-strategy" in prompt
    assert "Viết regression checklist cho release checkout retry" in prompt
