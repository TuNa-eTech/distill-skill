from __future__ import annotations

from distill_evolve.trace import trace_module

from tests.support.seeds import seed_artifact, seed_extraction


def test_trace_module_resolves_citations_to_extractions_and_artifacts(
    db_conn,
    temp_db,
    tmp_path,
):
    artifact_id = seed_artifact(
        db_conn,
        kind="gitlab_mr",
        external_id="501",
        metadata={"title": "Traceable MR"},
    )
    extraction_id = seed_extraction(
        db_conn,
        artifact_id=artifact_id,
        payload={
            "artifact_id": artifact_id,
            "task_type": "trace",
            "domain_tags": ["flutter"],
            "patterns": [],
            "files_touched": [],
            "outcome_signal": "merged",
        },
    )
    module_path = tmp_path / "state-management.md"
    module_path.write_text("# State Management\n\n## Rules\n- Keep things traceable. [src: 1]\n")

    trace = trace_module(module_path=module_path, db_path=temp_db)

    assert list(trace.keys()) == [artifact_id]
    assert trace[artifact_id]["artifact"]["external_id"] == "501"
    assert trace[artifact_id]["extractions"][0]["id"] == extraction_id


def test_trace_module_filters_extractions_by_role_when_path_is_under_pack(
    db_conn,
    temp_db,
    tmp_path,
):
    artifact_id = seed_artifact(
        db_conn,
        kind="jira_issue",
        external_id="QA-501",
        metadata={"summary": "Traceable Jira"},
    )
    tester_extraction_id = seed_extraction(
        db_conn,
        artifact_id=artifact_id,
        role="tester-manual",
        payload={
            "artifact_id": artifact_id,
            "task_type": "report-bug",
            "domain_tags": ["bug-report-quality"],
            "patterns": [],
            "files_touched": [],
            "outcome_signal": "resolved",
        },
    )
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
    module_path = tmp_path / "packs" / "tester-manual" / "v0.1" / "skills" / "bug-report-quality.md"
    module_path.parent.mkdir(parents=True, exist_ok=True)
    module_path.write_text("# Bug Report Quality\n\n## Rules\n- Keep things traceable. [src: 1]\n")

    trace = trace_module(module_path=module_path, db_path=temp_db)

    assert list(trace.keys()) == [artifact_id]
    assert [row["id"] for row in trace[artifact_id]["extractions"]] == [tester_extraction_id]
