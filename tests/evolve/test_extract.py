from __future__ import annotations

import json

from distill_evolve.extract import extract_one, run_extraction

from tests.support.seeds import seed_artifact, seed_extraction, seed_score, write_blob


def test_extract_one_parses_and_validates_llm_json(db_conn, temp_blobs):
    blob_path = write_blob(
        temp_blobs,
        "gitlab_mr/101.json",
        {
            "title": "Add payment cubit",
            "description": "Implements mobile payment state flow.",
        },
    )
    artifact_id = seed_artifact(
        db_conn,
        kind="gitlab_mr",
        external_id="101",
        metadata={
            "title": "Add payment cubit",
            "changed_files": ["lib/features/payment/payment_cubit.dart"],
        },
        blob_path=blob_path,
    )
    artifact_row = db_conn.execute(
        "SELECT * FROM artifacts WHERE id = ?", (artifact_id,)
    ).fetchone()

    extraction = extract_one(
        role="mobile-dev",
        artifact_row=artifact_row,
        artifact_card="""---
artifact_id: 1
kind: gitlab_mr
external_id: 101
updated_at: 2026-01-10T00:00:00Z
jira_keys: []
linked_artifacts: []
---

# Summary
Add payment cubit

## Intent
Implements mobile payment state flow.

## Key Changes
- Changed file: lib/features/payment/payment_cubit.dart

## Important Files
- `lib/features/payment/payment_cubit.dart`

## Decisions / Patterns
- State: merged

## Evidence Snippets
- "Implements mobile payment state flow."
""",
        supporting_artifacts=[],
        llm_callable=lambda **_: (
            """```json
        {
          "artifact_id": 999,
          "task_type": "update-payment-state",
          "domain_tags": ["flutter", "state-management"],
          "patterns": [
            {
              "kind": "convention",
              "summary": "Keep payment state mutations inside the cubit.",
              "evidence_excerpt": "Implements mobile payment state flow.",
              "confidence": 0.9
            }
          ],
          "files_touched": ["lib/features/payment/payment_cubit.dart"],
          "outcome_signal": "merged"
        }
        ```"""
        ),
    )

    assert extraction.artifact_id == artifact_id
    assert extraction.task_type == "update-payment-state"
    assert extraction.domain_tags == ["flutter", "state-management"]
    assert extraction.patterns[0].summary.startswith("Keep payment state")


def test_run_extraction_logs_invalid_outputs_and_skips_insert(
    db_conn, temp_db, temp_blobs, tmp_path
):
    blob_path = write_blob(
        temp_blobs,
        "gitlab_mr/202.json",
        {"title": "Broken extraction payload"},
    )
    artifact_id = seed_artifact(
        db_conn,
        kind="gitlab_mr",
        external_id="202",
        metadata={"title": "Broken extraction payload", "changed_files": ["lib/app.dart"]},
        blob_path=blob_path,
    )
    seed_score(db_conn, artifact_id=artifact_id, role="mobile-dev", score=9.0)

    summary = run_extraction(
        role="mobile-dev",
        db_path=temp_db,
        blobs_dir=temp_blobs,
        limit=10,
        llm_callable=lambda **_: json.dumps({"artifact_id": artifact_id, "task_type": "broken"}),
        failure_log_path=tmp_path / "extract_failures.jsonl",
    )

    assert summary["processed"] == 1
    assert summary["inserted"] == 0
    assert summary["failed"] == 1
    failures = (tmp_path / "extract_failures.jsonl").read_text()
    assert '"artifact_id": 1' in failures
    assert '"kind": "gitlab_mr"' in failures
    assert '"artifact_card_preview"' in failures
    count = db_conn.execute("SELECT COUNT(*) FROM extractions").fetchone()[0]
    assert count == 0


def test_run_extraction_does_not_skip_when_only_other_role_extraction_exists(
    db_conn, temp_db, temp_blobs
):
    blob_path = write_blob(
        temp_blobs,
        "jira/issue/204.json",
        {"fields": {"summary": "Tester bug", "description": "Steps to reproduce: retry flow."}},
    )
    artifact_id = seed_artifact(
        db_conn,
        kind="jira_issue",
        external_id="QA-204",
        metadata={
            "status": "Resolved",
            "issue_type": "Bug",
            "summary": "Tester bug",
            "description": "Steps to reproduce: retry flow. Actual result: stale state. Expected result: clear state.",
        },
        blob_path=blob_path,
    )
    seed_score(db_conn, artifact_id=artifact_id, role="tester-manual", score=4.0)
    seed_extraction(
        db_conn,
        artifact_id=artifact_id,
        role="business-analyst",
        payload={
            "artifact_id": artifact_id,
            "task_type": "write-spec",
            "domain_tags": ["spec-writing"],
            "patterns": [],
            "files_touched": [],
            "outcome_signal": "accepted",
        },
    )

    summary = run_extraction(
        role="tester-manual",
        db_path=temp_db,
        blobs_dir=temp_blobs,
        llm_callable=lambda **_: json.dumps(
            {
                "artifact_id": 0,
                "task_type": "report-bug",
                "domain_tags": ["bug-report-quality"],
                "patterns": [],
                "files_touched": [],
                "outcome_signal": "resolved",
            }
        ),
    )

    tester_extractions = db_conn.execute(
        "SELECT COUNT(*) FROM extractions WHERE artifact_id = ? AND role = 'tester-manual'",
        (artifact_id,),
    ).fetchone()[0]
    assert summary == {"processed": 1, "inserted": 1, "failed": 0, "skipped": 0}
    assert tester_extractions == 1


def test_extract_one_supports_business_analyst_prompting(db_conn, temp_blobs):
    blob_path = write_blob(
        temp_blobs,
        "confluence/page/301.json",
        {
            "title": "Checkout PRD",
            "body": {"storage": {"value": "<h1>Problem</h1><p>Checkout drop-off is high.</p>"}},
        },
    )
    artifact_id = seed_artifact(
        db_conn,
        kind="confluence_page",
        external_id="page:301",
        metadata={
            "title": "Checkout PRD",
            "body_text": "Problem: Checkout drop-off is high. Success metrics: raise conversion.",
            "labels": ["spec"],
        },
        blob_path=blob_path,
    )
    artifact_row = db_conn.execute(
        "SELECT * FROM artifacts WHERE id = ?", (artifact_id,)
    ).fetchone()
    seen_system_prompt: dict[str, str] = {}

    def llm_callable(**kwargs):
        seen_system_prompt["value"] = kwargs["system"]
        return """{
          "artifact_id": 0,
          "task_type": "write-spec",
          "domain_tags": ["spec-writing", "checkout"],
          "patterns": [
            {
              "kind": "template",
              "summary": "State the problem and success metrics before proposing the solution.",
              "evidence_excerpt": "Problem: Checkout drop-off is high.",
              "confidence": 0.9
            }
          ],
          "files_touched": [],
          "outcome_signal": "accepted"
        }"""

    extraction = extract_one(
        role="business-analyst",
        artifact_row=artifact_row,
        artifact_card="""---
artifact_id: 1
kind: confluence_page
external_id: page:301
updated_at: 2026-01-10T00:00:00Z
jira_keys: []
linked_artifacts: []
---

# Summary
Checkout PRD

## Intent
Problem: Checkout drop-off is high. Success metrics: raise conversion.

## Key Changes
- Label: spec

## Important Files
- None.

## Decisions / Patterns
- Linked artifacts: None.

## Evidence Snippets
- "Problem: Checkout drop-off is high."
""",
        supporting_artifacts=[],
        llm_callable=llm_callable,
    )

    assert extraction.artifact_id == artifact_id
    assert extraction.task_type == "write-spec"
    assert "business-analysis patterns" in seen_system_prompt["value"]


def test_extract_one_supports_tester_manual_prompting(db_conn, temp_blobs):
    blob_path = write_blob(
        temp_blobs,
        "jira/issue/401.json",
        {
            "fields": {
                "summary": "Checkout retry keeps stale error",
                "description": (
                    "Steps to reproduce: retry checkout.\n"
                    "Actual result: stale error remains.\n"
                    "Expected result: error clears."
                ),
            }
        },
    )
    artifact_id = seed_artifact(
        db_conn,
        kind="jira_issue",
        external_id="QA-401",
        metadata={
            "status": "Resolved",
            "issue_type": "Bug",
            "summary": "Checkout retry keeps stale error",
            "description": (
                "Steps to reproduce: retry checkout. Actual result: stale error remains. "
                "Expected result: error clears."
            ),
            "labels": ["regression"],
        },
        blob_path=blob_path,
    )
    artifact_row = db_conn.execute(
        "SELECT * FROM artifacts WHERE id = ?", (artifact_id,)
    ).fetchone()
    seen_system_prompt: dict[str, str] = {}

    def llm_callable(**kwargs):
        seen_system_prompt["value"] = kwargs["system"]
        return """{
          "artifact_id": 0,
          "task_type": "report-bug",
          "domain_tags": ["bug-report-quality", "checkout"],
          "patterns": [
            {
              "kind": "template",
              "summary": "Luôn ghi rõ steps to reproduce, actual result, và expected result trong bug report.",
              "evidence_excerpt": "Steps to reproduce: retry checkout.",
              "confidence": 0.9
            }
          ],
          "files_touched": [],
          "outcome_signal": "resolved"
        }"""

    extraction = extract_one(
        role="tester-manual",
        artifact_row=artifact_row,
        artifact_card="""---
artifact_id: 1
kind: jira_issue
external_id: QA-401
updated_at: 2026-01-10T00:00:00Z
jira_keys: ["QA-401"]
linked_artifacts: []
---

# Summary
Checkout retry keeps stale error

## Intent
Steps to reproduce: retry checkout. Actual result: stale error remains. Expected result: error clears.

## Key Changes
- Issue type: Bug
- Current status: Resolved
- Labels: regression

## Important Files
- None.

## Decisions / Patterns
- Linked artifacts: None.

## Evidence Snippets
- "Steps to reproduce: retry checkout."
""",
        supporting_artifacts=[],
        llm_callable=llm_callable,
    )

    assert extraction.artifact_id == artifact_id
    assert extraction.task_type == "report-bug"
    assert "manual testing patterns" in seen_system_prompt["value"]
