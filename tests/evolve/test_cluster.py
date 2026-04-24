from __future__ import annotations

from distill_evolve.cluster import cluster_extractions

from tests.support.seeds import seed_artifact, seed_cluster, seed_extraction, seed_score


def test_cluster_extractions_can_create_and_reuse_clusters(db_conn):
    first_artifact = seed_artifact(
        db_conn,
        kind="gitlab_mr",
        external_id="301",
        metadata={"title": "State handling cleanup"},
    )
    second_artifact = seed_artifact(
        db_conn,
        kind="gitlab_mr",
        external_id="302",
        metadata={"title": "Route cleanup"},
    )
    seed_score(db_conn, artifact_id=first_artifact, role="mobile-dev", score=9.0)
    seed_score(db_conn, artifact_id=second_artifact, role="mobile-dev", score=8.0)
    first_extraction = seed_extraction(
        db_conn,
        artifact_id=first_artifact,
        payload={
            "artifact_id": first_artifact,
            "task_type": "state-cleanup",
            "domain_tags": ["flutter"],
            "patterns": [
                {
                    "kind": "convention",
                    "summary": "Use cubits",
                    "evidence_excerpt": "Use cubits",
                    "confidence": 0.8,
                }
            ],
            "files_touched": [],
            "outcome_signal": "merged",
        },
    )
    second_extraction = seed_extraction(
        db_conn,
        artifact_id=second_artifact,
        payload={
            "artifact_id": second_artifact,
            "task_type": "route-cleanup",
            "domain_tags": ["flutter"],
            "patterns": [
                {
                    "kind": "decision",
                    "summary": "Keep routes typed",
                    "evidence_excerpt": "typed route",
                    "confidence": 0.8,
                }
            ],
            "files_touched": [],
            "outcome_signal": "merged",
        },
    )
    existing_cluster_id = seed_cluster(db_conn, role="mobile-dev", name="navigation")
    answers = iter(["new", "state-management", str(existing_cluster_id)])

    result = cluster_extractions(
        db_conn,
        role="mobile-dev",
        input_fn=lambda _: next(answers),
        output_fn=lambda _: None,
    )

    rows = db_conn.execute(
        "SELECT id, cluster_id FROM extractions WHERE id IN (?, ?) ORDER BY id",
        (first_extraction, second_extraction),
    ).fetchall()
    assert result["assigned"] == 2
    assert rows[0]["cluster_id"] != existing_cluster_id
    assert rows[1]["cluster_id"] == existing_cluster_id
    cluster_names = {
        row["name"]
        for row in db_conn.execute("SELECT name FROM clusters WHERE role = 'mobile-dev'").fetchall()
    }
    assert "state-management" in cluster_names
    assert "navigation" in cluster_names


def test_cluster_extractions_ignores_unclustered_extractions_from_other_roles(db_conn):
    issue_id = seed_artifact(
        db_conn,
        kind="jira_issue",
        external_id="QA-301",
        metadata={"summary": "Tester issue"},
    )
    seed_score(db_conn, artifact_id=issue_id, role="tester-manual", score=4.0)
    seed_extraction(
        db_conn,
        artifact_id=issue_id,
        role="business-analyst",
        payload={
            "artifact_id": issue_id,
            "task_type": "write-spec",
            "domain_tags": ["spec-writing"],
            "patterns": [],
            "files_touched": [],
            "outcome_signal": "accepted",
        },
    )

    result = cluster_extractions(
        db_conn,
        role="tester-manual",
        input_fn=lambda _: "skip",
        output_fn=lambda _: None,
    )

    assert result == {"processed": 0, "assigned": 0, "skipped": 0, "created_clusters": 0}
