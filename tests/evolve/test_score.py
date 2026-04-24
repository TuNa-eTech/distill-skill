from __future__ import annotations

import pytest

from distill_evolve.score import (
    score_ba_artifact,
    score_mobile_mr,
    score_role,
    score_tester_manual_artifact,
    select_extraction_candidates,
)

from tests.support.seeds import seed_artifact, seed_jira_event, seed_link, seed_score


def test_score_mobile_mr_uses_linked_supporting_evidence(db_conn):
    mr_id = seed_artifact(
        db_conn,
        kind="gitlab_mr",
        external_id="101",
        metadata={
            "state": "merged",
            "title": "Add payment flow state handling",
            "changed_files": [
                "lib/features/payments/bloc/payment_cubit.dart",
                "test/features/payments/payment_cubit_test.dart",
            ],
            "discussion_count": 3,
            "resolved_discussion_count": 2,
        },
    )
    jira_id = seed_artifact(
        db_conn,
        kind="jira_issue",
        external_id="MOB-101",
        metadata={"status": "Done", "summary": "Payment flow update"},
    )
    confluence_id = seed_artifact(
        db_conn,
        kind="confluence_page",
        external_id="CONF-9",
        metadata={"title": "Payment flow ADR"},
    )
    seed_link(db_conn, source_id=mr_id, target_id=jira_id, link_type="references")
    seed_link(db_conn, source_id=mr_id, target_id=confluence_id, link_type="documents")

    score, breakdown = score_mobile_mr(db_conn, mr_id)

    assert score == pytest.approx(8.5)
    assert breakdown == {
        "merged": 3.0,
        "closed_without_merge": 0.0,
        "linked_jira_done": 1.5,
        "linked_confluence": 1.0,
        "flutter_app_code": 1.0,
        "test_coverage": 1.0,
        "resolved_review_discussion": 0.5,
        "target_module_area": 0.5,
        "jira_reopened": 0.0,
        "rollback_detected": 0.0,
    }


def test_score_mobile_mr_applies_negative_signals(db_conn):
    mr_id = seed_artifact(
        db_conn,
        kind="gitlab_mr",
        external_id="102",
        created_at="2026-02-01T00:00:00Z",
        metadata={
            "state": "closed",
            "title": "Refactor auth guard",
            "changed_files": ["README.md"],
        },
    )
    jira_id = seed_artifact(
        db_conn,
        kind="jira_issue",
        external_id="MOB-102",
        metadata={"status": "Reopened"},
    )
    seed_link(db_conn, source_id=mr_id, target_id=jira_id, link_type="references")
    seed_jira_event(
        db_conn,
        issue_id=jira_id,
        event_kind="status_changed",
        from_value="Done",
        to_value="Reopened",
        occurred_at="2026-02-03T00:00:00Z",
    )
    seed_artifact(
        db_conn,
        kind="gitlab_mr",
        external_id="103",
        created_at="2026-02-05T00:00:00Z",
        metadata={"title": "Revert !102 auth guard rollback"},
    )

    score, breakdown = score_mobile_mr(db_conn, mr_id)

    assert score == pytest.approx(-9.0)
    assert breakdown["closed_without_merge"] == -2.0
    assert breakdown["jira_reopened"] == -3.0
    assert breakdown["rollback_detected"] == -4.0


def test_select_extraction_candidates_clamps_to_minimum(db_conn):
    for index in range(40):
        artifact_id = seed_artifact(
            db_conn,
            kind="gitlab_mr",
            external_id=f"{index + 1}",
            metadata={"state": "merged", "changed_files": ["lib/app.dart"]},
        )
        seed_score(
            db_conn,
            artifact_id=artifact_id,
            role="mobile-dev",
            score=100.0 - index,
            breakdown={"merged": 3.0},
        )

    candidates = select_extraction_candidates(db_conn, role="mobile-dev")

    assert len(candidates) == 30
    assert candidates[0]["external_id"] == "1"
    assert candidates[-1]["external_id"] == "30"


def test_score_ba_artifact_uses_jira_and_confluence_signals(db_conn):
    issue_id = seed_artifact(
        db_conn,
        kind="jira_issue",
        external_id="BA-101",
        metadata={
            "status": "Done",
            "summary": "Checkout user story",
            "description": (
                "Acceptance Criteria:\n"
                "Given the user has items in cart\n"
                "When payment succeeds\n"
                "Then show confirmation and keep open questions explicit."
            ),
            "comment_count": 4,
        },
    )
    page_id = seed_artifact(
        db_conn,
        kind="confluence_page",
        external_id="page:101",
        metadata={
            "title": "Checkout PRD",
            "body_text": (
                "Problem: Checkout drop-off is high. Success metrics: improve conversion. "
                "Acceptance Criteria: Given a known customer, when payment succeeds, then "
                "show confirmation. Out of scope: loyalty redesign."
            ),
            "labels": ["spec"],
        },
    )
    seed_link(db_conn, source_id=issue_id, target_id=page_id, link_type="documents")
    seed_link(db_conn, source_id=page_id, target_id=issue_id, link_type="references_jira")

    issue_score, issue_breakdown = score_ba_artifact(db_conn, issue_id)
    page_score, page_breakdown = score_ba_artifact(db_conn, page_id)

    assert issue_score == pytest.approx(8.0)
    assert issue_breakdown["done_or_accepted"] == 2.5
    assert issue_breakdown["linked_confluence"] == 1.5
    assert issue_breakdown["acceptance_criteria"] == 1.5
    assert page_score == pytest.approx(7.0)
    assert page_breakdown["linked_jira"] == 1.5
    assert page_breakdown["linked_jira_done"] == 1.5
    assert page_breakdown["success_metrics"] == 1.0


def test_score_role_supports_business_analyst_primary_artifacts(db_conn, temp_db):
    seed_artifact(
        db_conn,
        kind="jira_issue",
        external_id="BA-201",
        metadata={
            "status": "Done",
            "summary": "Story",
            "description": "Acceptance Criteria: Given x when y then z",
        },
    )
    seed_artifact(
        db_conn,
        kind="confluence_page",
        external_id="page:201",
        metadata={"title": "Pricing PRD", "body_text": "Problem. Success metrics. Out of scope."},
    )
    seed_artifact(
        db_conn,
        kind="gitlab_mr",
        external_id="901",
        metadata={"state": "merged", "changed_files": ["lib/app.dart"]},
    )

    summary = score_role(role="business-analyst", db_path=temp_db)

    assert summary == {"role": "business-analyst", "count": 2}


def test_score_tester_manual_artifact_uses_bug_report_and_regression_signals(db_conn):
    issue_id = seed_artifact(
        db_conn,
        kind="jira_issue",
        external_id="QA-101",
        metadata={
            "status": "Resolved",
            "issue_type": "Bug",
            "summary": "Checkout retry shows stale error banner",
            "description": (
                "Steps to reproduce: 1. Open checkout. 2. Retry failed payment. "
                "Actual result: stale error banner remains visible. "
                "Expected result: banner clears after successful retry. "
                "Environment: iOS 17, app 1.2.3. Regression after payment retry refactor."
            ),
            "comment_count": 4,
            "labels": ["regression"],
            "components": ["Checkout"],
        },
    )

    score, breakdown = score_tester_manual_artifact(db_conn, issue_id)

    assert score == pytest.approx(8.5)
    assert breakdown == {
        "bug_or_defect": 1.5,
        "done_or_resolved": 1.5,
        "reproduction_steps": 1.0,
        "expected_vs_actual": 1.0,
        "environment_details": 0.5,
        "regression_signal": 1.0,
        "test_design_signal": 1.0,
        "discussion_signal": 0.5,
        "module_area_match": 0.5,
        "jira_reopened": 0.0,
        "scope_churn": 0.0,
        "thin_description": 0.0,
        "low_relevance_issue": 0.0,
    }


def test_score_tester_manual_artifact_penalizes_reopened_low_signal_issues(db_conn):
    issue_id = seed_artifact(
        db_conn,
        kind="jira_issue",
        external_id="QA-102",
        metadata={
            "status": "Reopened",
            "issue_type": "Task",
            "summary": "Need retest",
            "description": "Please check again.",
            "comment_count": 0,
        },
    )
    seed_jira_event(
        db_conn,
        issue_id=issue_id,
        event_kind="status_change",
        from_value="Done",
        to_value="Reopened",
        occurred_at="2026-02-11T00:00:00Z",
    )

    score, breakdown = score_tester_manual_artifact(db_conn, issue_id)

    assert score == pytest.approx(-5.5)
    assert breakdown["jira_reopened"] == -3.0
    assert breakdown["thin_description"] == -1.0
    assert breakdown["low_relevance_issue"] == -1.5


def test_score_role_supports_tester_manual_primary_artifacts(db_conn, temp_db):
    seed_artifact(
        db_conn,
        kind="jira_issue",
        external_id="QA-201",
        metadata={
            "status": "Resolved",
            "issue_type": "Bug",
            "summary": "Banner overlaps CTA",
            "description": "Steps to reproduce. Actual result. Expected result. Environment: Android 14.",
        },
    )
    seed_artifact(
        db_conn,
        kind="jira_issue",
        external_id="QA-202",
        metadata={
            "status": "Done",
            "issue_type": "Story",
            "summary": "Regression checklist for checkout",
            "description": "Test cases: main flow, retry flow, declined card, offline mode.",
        },
    )
    seed_artifact(
        db_conn,
        kind="confluence_page",
        external_id="page:999",
        metadata={"title": "Should not be scored for tester-manual"},
    )

    summary = score_role(role="tester-manual", db_path=temp_db)

    assert summary == {"role": "tester-manual", "count": 2}
