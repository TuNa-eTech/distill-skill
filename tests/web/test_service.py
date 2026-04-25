from __future__ import annotations

from pathlib import Path

from distill_web.service import (
    get_overview,
    get_pipeline,
    get_review_entry,
    list_review_entries,
    list_roles,
)
from tests.support.seeds import seed_artifact, seed_cluster, seed_extraction, seed_link, seed_score


def _write_pack(temp_packs: Path, *, role: str, module_names: list[str]) -> None:
    pack_root = temp_packs / role / "v0.1"
    skills_dir = pack_root / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)
    (pack_root / "pack.yaml").write_text(
        "\n".join(
            [
                f"role: {role}",
                "version: v0.1",
                "language: vi",
                "generated_at: '2026-04-24T08:08:35.980053Z'",
                "source_window: 2026-01-01..2026-04-24",
                "contributors: 3",
                "quality_signals:",
                "  source_artifacts: 10",
                "  filtered_in: 2",
                "  filtered_out: 8",
                f"  modules_generated: {len(module_names)}",
                "llm_model: gpt-5.4-mini",
            ]
        ),
        encoding="utf-8",
    )
    (pack_root / "manifest.md").write_text(
        "\n".join(
            [
                f"# {role} - Skill Pack Manifest (v0.1)",
                "",
                "## Hard rules",
                "- Use grounded source material. [src: A-1, A-2]",
                "",
                "## Skill modules",
                "| Module | Load when |",
                "|---|---|",
                *[f"| skills/{name}.md | Always |" for name in module_names],
            ]
        ),
        encoding="utf-8",
    )
    for name in module_names:
        (skills_dir / f"{name}.md").write_text(
            "\n".join(
                [
                    f"# {name}",
                    "",
                    "## Rules",
                    "- Keep guidance grounded. [src: A-1, A-2]",
                ]
            ),
            encoding="utf-8",
        )


def test_list_roles_and_overview_surface_real_counts(db_conn, temp_db, temp_packs):
    mr_id = seed_artifact(
        db_conn,
        kind="gitlab_mr",
        external_id="513!538",
        metadata={"title": "Improve cart flow"},
    )
    issue_id = seed_artifact(
        db_conn,
        kind="jira_issue",
        external_id="APP-123",
        metadata={"summary": "Regression checklist"},
    )
    page_id = seed_artifact(
        db_conn,
        kind="confluence_page",
        external_id="page:274698698",
        metadata={"title": "Payment reminders ADR"},
    )
    state_cluster = seed_cluster(db_conn, role="mobile-dev", name="state-management")
    seed_cluster(db_conn, role="tester-manual", name="regression-strategy")
    seed_score(db_conn, artifact_id=mr_id, role="mobile-dev", score=4.5, breakdown={"clarity": 2.0})
    seed_score(db_conn, artifact_id=issue_id, role="tester-manual", score=3.9)
    seed_score(db_conn, artifact_id=page_id, role="business-analyst", score=3.7)
    seed_extraction(
        db_conn,
        artifact_id=mr_id,
        role="mobile-dev",
        cluster_id=state_cluster,
        payload={
            "task_type": "implement-state-management",
            "domain_tags": ["flutter", "bloc"],
            "patterns": [{"kind": "template", "summary": "Use Cubit.", "confidence": 0.9}],
            "files_touched": ["lib/cart.dart"],
            "outcome_signal": "merged",
        },
    )
    seed_extraction(
        db_conn,
        artifact_id=page_id,
        role="business-analyst",
        payload={
            "task_type": "write-spec",
            "domain_tags": ["ux"],
            "patterns": [
                {"kind": "decision", "summary": "Set measurable success.", "confidence": 0.8}
            ],
            "outcome_signal": "build",
        },
    )
    seed_link(db_conn, source_id=mr_id, target_id=issue_id)
    _write_pack(temp_packs, role="mobile-dev", module_names=["state-management", "navigation"])
    _write_pack(temp_packs, role="business-analyst", module_names=["spec-writing"])
    _write_pack(temp_packs, role="tester-manual", module_names=["regression-strategy"])

    roles = list_roles(db_path=temp_db, packs_dir=temp_packs)
    assert [item["role"] for item in roles] == [
        "mobile-dev",
        "business-analyst",
        "tester-manual",
    ]

    overview = get_overview("mobile-dev", db_path=temp_db, packs_dir=temp_packs)
    assert overview["role"] == "mobile-dev"
    assert overview["metrics"][0]["value"] == "1"
    assert overview["metrics"][1]["value"] == "1"
    assert overview["metrics"][2]["value"] == "1"
    assert overview["metrics"][3]["value"] == "2"
    assert overview["validation"]["ok"] is True
    assert overview["packSummary"]["moduleCount"] == 2
    assert overview["alerts"][0]["tone"] == "info" or overview["alerts"][0]["tone"] == "warn"


def test_pipeline_marks_partial_when_extractions_are_unclustered(db_conn, temp_db, temp_packs):
    page_id = seed_artifact(
        db_conn,
        kind="confluence_page",
        external_id="page:1",
        metadata={"title": "Write spec"},
    )
    seed_score(db_conn, artifact_id=page_id, role="business-analyst", score=3.7)
    seed_extraction(
        db_conn,
        artifact_id=page_id,
        role="business-analyst",
        payload={
            "task_type": "write-spec",
            "patterns": [{"kind": "decision", "summary": "Use 6R.", "confidence": 0.9}],
            "outcome_signal": "build",
        },
    )
    _write_pack(temp_packs, role="business-analyst", module_names=["spec-writing"])

    pipeline = get_pipeline("business-analyst", db_path=temp_db, packs_dir=temp_packs)
    cluster_stage = next(item for item in pipeline["stages"] if item["key"] == "cluster")
    validate_stage = next(item for item in pipeline["stages"] if item["key"] == "validate")

    assert cluster_stage["state"] == "partial"
    assert validate_stage["state"] == "ready"


def test_review_list_and_detail_surface_payload_fields(db_conn, temp_db, temp_packs):
    mr_id = seed_artifact(
        db_conn,
        kind="gitlab_mr",
        external_id="513!538",
        metadata={"title": "Improve cart flow", "web_url": "https://example.test/mr/538"},
    )
    issue_id = seed_artifact(
        db_conn,
        kind="jira_issue",
        external_id="APP-123",
        metadata={"summary": "Regression checklist"},
    )
    cluster_id = seed_cluster(db_conn, role="mobile-dev", name="state-management")
    seed_score(
        db_conn,
        artifact_id=mr_id,
        role="mobile-dev",
        score=4.5,
        breakdown={"clarity": 2.0, "review": 1.0},
    )
    extraction_id = seed_extraction(
        db_conn,
        artifact_id=mr_id,
        role="mobile-dev",
        cluster_id=cluster_id,
        payload={
            "task_type": "implement-state-management",
            "domain_tags": ["flutter", "bloc"],
            "patterns": [
                {
                    "kind": "template",
                    "summary": "Use a reusable Cubit.",
                    "evidence_excerpt": "class CartCubit",
                    "confidence": 0.94,
                }
            ],
            "files_touched": ["lib/cart.dart", "lib/cart_state.dart"],
            "outcome_signal": "merged",
        },
    )
    seed_link(db_conn, source_id=mr_id, target_id=issue_id)
    _write_pack(temp_packs, role="mobile-dev", module_names=["state-management"])

    listing = list_review_entries("mobile-dev", db_path=temp_db, packs_dir=temp_packs)
    assert listing["summary"]["visible"] == 1
    assert listing["items"][0]["title"] == "Improve cart flow"
    assert listing["items"][0]["clusterName"] == "state-management"

    detail = get_review_entry("mobile-dev", extraction_id, db_path=temp_db, packs_dir=temp_packs)
    assert detail["taskType"] == "implement-state-management"
    assert detail["filesTouched"] == ["lib/cart.dart", "lib/cart_state.dart"]
    assert detail["linkedArtifacts"][0]["externalId"] == "APP-123"
    assert detail["scoreBreakdown"]["clarity"] == 2.0
