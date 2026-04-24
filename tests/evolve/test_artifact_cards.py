from __future__ import annotations

import json

from distill_evolve.artifact_cards import build_artifact_card, render_supporting_artifacts_text


def test_build_gitlab_artifact_card_includes_sections_and_verbatim_evidence():
    blob_text = json.dumps(
        {
            "mr": {
                "title": "APP-123 add payment edit flow",
                "description": "Keep payment state mutations inside the cubit.",
                "state": "merged",
                "source_branch": "feature/APP-123-payment-edit",
                "target_branch": "main",
                "author": {"username": "alice"},
            },
            "discussions": [
                {
                    "resolved": True,
                    "notes": [{"body": "<p>Prefer one cubit for the full payment flow.</p>"}],
                }
            ],
            "commits": [{"message": "feat: add payment flow state cleanup"}],
            "changes": {
                "changes": [
                    {
                        "new_path": "lib/features/payment/payment_cubit.dart",
                        "diff": "@@ -1,2 +1,4 @@\n+emit(state.copyWith(isSaving: true));\n+await _repository.save();",
                    }
                ]
            },
        }
    )

    card = build_artifact_card(
        artifact_id=7,
        kind="gitlab_mr",
        external_id="42!101",
        metadata={
            "title": "APP-123 add payment edit flow",
            "state": "merged",
            "source_branch": "feature/APP-123-payment-edit",
            "target_branch": "main",
            "discussion_count": 1,
            "resolved_discussions": 1,
            "changed_files": ["lib/features/payment/payment_cubit.dart"],
            "jira_keys": ["APP-123"],
        },
        blob_text=blob_text,
        updated_at="2026-04-24T03:10:09Z",
        linked_artifacts=["APP-123"],
    )

    assert "# Summary" in card
    assert "## Important Files" in card
    assert "## Evidence Snippets" in card
    assert "Linked artifacts: APP-123" in card
    assert '"Keep payment state mutations inside the cubit."' in card
    assert '"emit(state.copyWith(isSaving: true));"' in card
    assert "https://gitlab.example" not in card


def test_build_jira_artifact_card_includes_lifecycle_and_comment_signal():
    blob_text = json.dumps(
        {
            "key": "APP-123",
            "fields": {
                "summary": "Edit payment schedule",
                "description": "Clarify how schedule edits affect pending reminders.",
                "status": {"name": "Done"},
                "issuetype": {"name": "Story"},
                "labels": ["mobile"],
                "components": [{"name": "Payments"}],
            },
            "comments": [{"body": "Document reminder behavior before release."}],
        }
    )

    card = build_artifact_card(
        artifact_id=8,
        kind="jira_issue",
        external_id="APP-123",
        metadata={
            "summary": "Edit payment schedule",
            "status": "Done",
            "issue_type": "Story",
            "labels": ["mobile"],
            "components": ["Payments"],
            "comment_count": 1,
            "jira_keys": ["APP-123"],
        },
        blob_text=blob_text,
        updated_at="2026-04-20T08:00:00Z",
        linked_artifacts=["42!101"],
        artifact_context={
            "jira_events": [
                {
                    "event_kind": "status_change",
                    "from_value": "To Do",
                    "to_value": "In Progress",
                    "occurred_at": "2026-04-18T10:00:00Z",
                },
                {
                    "event_kind": "scope_change",
                    "from_value": "Old",
                    "to_value": "New",
                    "occurred_at": "2026-04-19T10:00:00Z",
                },
            ]
        },
    )

    assert "Current status: Done" in card
    assert "Lifecycle events: 2 captured" in card
    assert "status_change: To Do -> In Progress @ 2026-04-18T10:00:00Z" in card
    assert '"Document reminder behavior before release."' in card


def test_build_confluence_artifact_card_strips_html_and_surfaces_headings():
    blob_text = json.dumps(
        {
            "title": "APP-321 Payment reminders ADR",
            "body": {
                "storage": {
                    "value": "<h1>Decision</h1><p>Keep reminder edits local-first.</p><h2>Rollout</h2><p>Use one migration window.</p>"
                }
            },
        }
    )

    card = build_artifact_card(
        artifact_id=9,
        kind="confluence_page",
        external_id="page:2001",
        metadata={
            "title": "APP-321 Payment reminders ADR",
            "space": "MOB",
            "version_number": 3,
            "labels": ["spec"],
            "body_text": "Decision Keep reminder edits local-first. Rollout Use one migration window.",
            "jira_keys": ["APP-321"],
        },
        blob_text=blob_text,
        updated_at="2026-04-21T08:00:00Z",
        linked_artifacts=["APP-321"],
    )

    assert "Heading: Decision" in card
    assert "Heading: Rollout" in card
    assert "<h1>" not in card
    assert '"Decision Keep reminder edits local-first. Rollout Use one migration window."' in card


def test_render_supporting_artifacts_text_uses_compact_cards():
    text = render_supporting_artifacts_text(
        [
            {
                "artifact_id": 10,
                "kind": "jira_issue",
                "external_id": "APP-123",
                "link_type": "references_jira",
                "confidence": 1.0,
                "updated_at": "2026-04-20T08:00:00Z",
                "metadata": {"summary": "Edit payment schedule", "status": "Done"},
                "blob_text": json.dumps({"fields": {"summary": "Edit payment schedule"}}),
                "context": {},
            }
        ]
    )

    assert "### Supporting Artifact 1" in text
    assert "- kind: jira_issue" in text
    assert "# Summary" in text
    assert "Edit payment schedule" in text
