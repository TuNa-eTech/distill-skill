from __future__ import annotations

import json
from threading import Thread
from urllib.request import urlopen

from distill_web.server import make_server
from tests.support.seeds import seed_artifact, seed_cluster, seed_extraction, seed_score


def test_dashboard_server_serves_health_and_review_detail(db_conn, temp_db, temp_packs):
    artifact_id = seed_artifact(
        db_conn,
        kind="gitlab_mr",
        external_id="513!538",
        metadata={"title": "Improve cart flow"},
    )
    cluster_id = seed_cluster(db_conn, role="mobile-dev", name="state-management")
    seed_score(db_conn, artifact_id=artifact_id, role="mobile-dev", score=4.5)
    extraction_id = seed_extraction(
        db_conn,
        artifact_id=artifact_id,
        role="mobile-dev",
        cluster_id=cluster_id,
        payload={
            "task_type": "implement-state-management",
            "patterns": [{"kind": "template", "summary": "Use Cubit.", "confidence": 0.9}],
            "outcome_signal": "merged",
        },
    )

    server = make_server(host="127.0.0.1", port=0, db_path=temp_db, packs_dir=temp_packs)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    try:
        with urlopen(f"http://{host}:{port}/api/health") as response:
            payload = json.loads(response.read().decode("utf-8"))
        assert payload["ok"] is True

        with urlopen(
            f"http://{host}:{port}/api/review/{extraction_id}?role=mobile-dev"
        ) as response:
            detail = json.loads(response.read().decode("utf-8"))
        assert detail["extractionId"] == extraction_id
        assert detail["clusterName"] == "state-management"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
