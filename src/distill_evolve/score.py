"""Compute composite quality scores per artifact for the given role."""
from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime, timezone
from typing import Any

from distill_core.config import DB_PATH
from distill_core.db import connect, upsert_score
from distill_core.roles import SUPPORTED_ROLES, get_role_config

DONE_STATUSES = {"done", "accepted", "closed", "resolved", "shipped"}
REOPENED_STATUSES = {"reopened", "re-opened", "open", "to do", "todo", "in progress"}
TARGET_MODULE_KEYWORDS = (
    "bloc",
    "cubit",
    "riverpod",
    "provider",
    "state",
    "route",
    "router",
    "navigation",
    "screen",
    "test",
    "golden",
    "android",
    "ios",
    "platform",
    "plugin",
    "permission",
    "channel",
)
BA_MODULE_KEYWORDS = (
    "spec",
    "prd",
    "requirement",
    "acceptance criteria",
    "given",
    "when",
    "then",
    "discovery",
    "research",
    "interview",
    "assumption",
    "open question",
    "stakeholder",
    "status update",
    "retro",
    "escalation",
)
TESTER_MODULE_KEYWORDS = (
    "bug",
    "defect",
    "steps to reproduce",
    "reproduce",
    "actual result",
    "expected result",
    "environment",
    "device",
    "version",
    "regression",
    "checklist",
    "test case",
    "test cases",
    "scenario",
    "edge case",
    "boundary",
    "given",
    "when",
    "then",
)
BUG_LIKE_ISSUE_TYPES = ("bug", "defect", "incident", "regression")


def _parse_json(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    try:
        data = json.loads(value)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _lower(value: Any) -> str:
    return str(value or "").strip().lower()


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    raw = value.strip()
    if not raw:
        return None
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        try:
            parsed = datetime.fromisoformat(f"{raw}T00:00:00+00:00")
        except ValueError:
            return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def _normalize_paths(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        paths: list[str] = []
        for key in ("path", "new_path", "old_path", "file", "filename"):
            raw = value.get(key)
            if raw:
                paths.append(str(raw))
        nested = value.get("paths")
        if nested:
            paths.extend(_normalize_paths(nested))
        return paths
    if isinstance(value, list):
        paths: list[str] = []
        for item in value:
            paths.extend(_normalize_paths(item))
        return paths
    return []


def _artifact_metadata(row: sqlite3.Row) -> dict[str, Any]:
    return _parse_json(row["metadata"])


def _collect_changed_files(metadata: dict[str, Any]) -> list[str]:
    for key in ("changed_files", "files_touched", "file_paths", "paths", "changes"):
        paths = _normalize_paths(metadata.get(key))
        if paths:
            return paths
    return []


def _load_linked_artifacts(conn: sqlite3.Connection, artifact_id: int) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT a.*, l.link_type, l.confidence
        FROM links l
        JOIN artifacts a
          ON a.id = CASE
              WHEN l.source_id = ? THEN l.target_id
              ELSE l.source_id
            END
        WHERE l.source_id = ? OR l.target_id = ?
        ORDER BY l.confidence DESC, a.kind ASC, a.id ASC
        """,
        (artifact_id, artifact_id, artifact_id),
    ).fetchall()


def _is_done_status(status: Any) -> bool:
    return _lower(status) in DONE_STATUSES


def _touches_flutter_app_code(paths: list[str]) -> bool:
    return any(path.startswith("lib/") for path in paths)


def _touches_tests(paths: list[str]) -> bool:
    return any(path.startswith("test/") or path.startswith("integration_test/") for path in paths)


def _touches_target_module_area(paths: list[str], metadata: dict[str, Any]) -> bool:
    lowered_paths = " ".join(path.lower() for path in paths)
    lowered_text = " ".join(
        _lower(metadata.get(field))
        for field in ("title", "description", "source_branch", "target_branch")
    )
    haystack = f"{lowered_paths} {lowered_text}"
    return any(keyword in haystack for keyword in TARGET_MODULE_KEYWORDS)


def _artifact_text(metadata: dict[str, Any], *fields: str) -> str:
    values: list[str] = []
    for field in fields:
        value = metadata.get(field)
        if isinstance(value, list):
            values.extend(_lower(item) for item in value)
        else:
            values.append(_lower(value))
    return " ".join(item for item in values if item)


def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    return any(keyword in text for keyword in keywords)


def _has_resolved_review_discussion(metadata: dict[str, Any]) -> bool:
    resolved = metadata.get("resolved_discussion_count")
    discussion_count = metadata.get("discussion_count")
    unresolved = metadata.get("unresolved_discussion_count")
    try:
        if resolved is not None and float(resolved) > 0:
            return True
        if discussion_count is not None and unresolved is not None:
            return float(discussion_count) > 0 and float(unresolved) == 0
    except (TypeError, ValueError):
        pass
    discussions = metadata.get("discussions")
    if isinstance(discussions, list):
        for thread in discussions:
            if not isinstance(thread, dict):
                continue
            if thread.get("resolved") or thread.get("resolved_by"):
                return True
            notes = thread.get("notes")
            if isinstance(notes, list):
                resolved_notes = [
                    note
                    for note in notes
                    if isinstance(note, dict) and (note.get("resolved") or note.get("resolvable"))
                ]
                if len(notes) >= 2 and resolved_notes:
                    return True
    return False


def _jira_reopened_after_completion(conn: sqlite3.Connection, issue_ids: list[int]) -> bool:
    for issue_id in issue_ids:
        seen_done = False
        rows = conn.execute(
            """
            SELECT event_kind, from_value, to_value, occurred_at
            FROM jira_events
            WHERE issue_id = ?
            ORDER BY COALESCE(occurred_at, '')
            """,
            (issue_id,),
        ).fetchall()
        for row in rows:
            from_status = _lower(row["from_value"])
            to_status = _lower(row["to_value"])
            if from_status in DONE_STATUSES or to_status in DONE_STATUSES:
                seen_done = True
            if seen_done and to_status in REOPENED_STATUSES:
                return True
    return False


def _jira_scope_change_count(conn: sqlite3.Connection, issue_ids: list[int]) -> int:
    total = 0
    for issue_id in issue_ids:
        total += int(
            conn.execute(
                """
                SELECT COUNT(*)
                FROM jira_events
                WHERE issue_id = ? AND event_kind = 'scope_change'
                """,
                (issue_id,),
            ).fetchone()[0]
        )
    return total


def _rollback_detected(conn: sqlite3.Connection, artifact: sqlite3.Row, metadata: dict[str, Any]) -> bool:
    for flag in ("rollback_detected", "reverted", "followup_rollback"):
        if metadata.get(flag):
            return True

    created_at = _parse_datetime(artifact["created_at"]) or _parse_datetime(artifact["updated_at"])
    if created_at is None:
        return False
    external_id = str(artifact["external_id"])
    title = _lower(metadata.get("title"))
    candidates = conn.execute(
        """
        SELECT *
        FROM artifacts
        WHERE kind = 'gitlab_mr' AND id != ?
        ORDER BY COALESCE(created_at, updated_at, ingested_at)
        """,
        (artifact["id"],),
    ).fetchall()
    for row in candidates:
        candidate_dt = _parse_datetime(row["created_at"]) or _parse_datetime(row["updated_at"])
        if candidate_dt is None:
            continue
        delta_days = (candidate_dt - created_at).days
        if delta_days < 0 or delta_days > 14:
            continue
        candidate_meta = _artifact_metadata(row)
        candidate_text = " ".join(
            _lower(candidate_meta.get(field))
            for field in ("title", "description", "commit_message")
        )
        if "revert" not in candidate_text and "rollback" not in candidate_text:
            continue
        if external_id in candidate_text or f"!{external_id}" in candidate_text:
            return True
        if title and title in candidate_text:
            return True
    return False


def score_mobile_mr(conn: sqlite3.Connection, artifact_id: int) -> tuple[float, dict[str, float]]:
    artifact = conn.execute("SELECT * FROM artifacts WHERE id = ?", (artifact_id,)).fetchone()
    if artifact is None:
        raise ValueError(f"Artifact not found: {artifact_id}")
    metadata = _artifact_metadata(artifact)
    linked = _load_linked_artifacts(conn, artifact_id)
    linked_meta = [(row, _artifact_metadata(row)) for row in linked]
    issue_ids = [int(row["id"]) for row, _ in linked_meta if row["kind"] == "jira_issue"]
    changed_files = _collect_changed_files(metadata)
    state = _lower(metadata.get("state"))

    breakdown = {
        "merged": 3.0 if state == "merged" or metadata.get("merged_at") else 0.0,
        "closed_without_merge": -2.0
        if state in {"closed", "locked"} and not metadata.get("merged_at")
        else 0.0,
        "linked_jira_done": 1.5
        if any(row["kind"] == "jira_issue" and _is_done_status(meta.get("status")) for row, meta in linked_meta)
        else 0.0,
        "linked_confluence": 1.0
        if any(row["kind"] == "confluence_page" for row, _ in linked_meta)
        else 0.0,
        "flutter_app_code": 1.0 if _touches_flutter_app_code(changed_files) else 0.0,
        "test_coverage": 1.0 if _touches_tests(changed_files) else 0.0,
        "resolved_review_discussion": 0.5 if _has_resolved_review_discussion(metadata) else 0.0,
        "target_module_area": 0.5 if _touches_target_module_area(changed_files, metadata) else 0.0,
        "jira_reopened": -3.0 if _jira_reopened_after_completion(conn, issue_ids) else 0.0,
        "rollback_detected": -4.0 if _rollback_detected(conn, artifact, metadata) else 0.0,
    }
    return sum(breakdown.values()), breakdown


def score_ba_artifact(conn: sqlite3.Connection, artifact_id: int) -> tuple[float, dict[str, float]]:
    artifact = conn.execute("SELECT * FROM artifacts WHERE id = ?", (artifact_id,)).fetchone()
    if artifact is None:
        raise ValueError(f"Artifact not found: {artifact_id}")

    metadata = _artifact_metadata(artifact)
    linked = _load_linked_artifacts(conn, artifact_id)
    linked_meta = [(row, _artifact_metadata(row)) for row in linked]
    issue_ids = [int(row["id"]) for row, _ in linked_meta if row["kind"] == "jira_issue"]
    linked_confluence = any(row["kind"] == "confluence_page" for row, _ in linked_meta)
    module_text = _artifact_text(
        metadata,
        "title",
        "summary",
        "description",
        "body_text",
        "labels",
        "components",
    )
    scope_change_count = _jira_scope_change_count(conn, issue_ids or [artifact_id])
    reopened = _jira_reopened_after_completion(conn, issue_ids or [artifact_id])

    if artifact["kind"] == "confluence_page":
        body_text = _lower(metadata.get("body_text"))
        breakdown = {
            "linked_jira": 1.5 if issue_ids else 0.0,
            "linked_jira_done": 1.5
            if any(
                row["kind"] == "jira_issue" and _is_done_status(linked_metadata.get("status"))
                for row, linked_metadata in linked_meta
            )
            else 0.0,
            "problem_framing": 1.0
            if _contains_any(module_text, ("problem", "context", "pain", "objective"))
            else 0.0,
            "success_metrics": 1.0
            if _contains_any(module_text, ("success metric", "success metrics", "metric", "kpi"))
            else 0.0,
            "acceptance_criteria": 1.0
            if _contains_any(module_text, ("acceptance criteria", "given", "when", "then"))
            else 0.0,
            "scope_clarity": 0.5
            if _contains_any(module_text, ("edge case", "out of scope", "open question", "risk", "assumption"))
            else 0.0,
            "module_area_match": 0.5 if _contains_any(module_text, BA_MODULE_KEYWORDS) else 0.0,
            "substantive_content": 1.0 if len(body_text) >= 400 else 0.0,
            "jira_reopened": -3.0 if reopened else 0.0,
            "scope_churn": -2.0 if scope_change_count >= 2 else 0.0,
            "thin_content": -1.5 if len(body_text) < 120 else 0.0,
        }
        return sum(breakdown.values()), breakdown

    description = _lower(metadata.get("description"))
    breakdown = {
        "done_or_accepted": 2.5 if _is_done_status(metadata.get("status")) else 0.0,
        "linked_confluence": 1.5 if linked_confluence else 0.0,
        "description_quality": 1.0 if len(description) >= 120 else 0.0,
        "acceptance_criteria": 1.5
        if _contains_any(module_text, ("acceptance criteria", "given", "when", "then"))
        else 0.0,
        "scope_clarity": 0.5
        if _contains_any(module_text, ("out of scope", "open question", "dependency", "edge case"))
        else 0.0,
        "discussion_signal": 0.5 if int(metadata.get("comment_count") or 0) >= 3 else 0.0,
        "module_area_match": 0.5 if _contains_any(module_text, BA_MODULE_KEYWORDS) else 0.0,
        "jira_reopened": -3.0 if reopened else 0.0,
        "scope_churn": -2.0 if scope_change_count >= 2 else 0.0,
        "thin_description": -1.0 if len(description) < 60 else 0.0,
    }
    return sum(breakdown.values()), breakdown


def score_tester_manual_artifact(
    conn: sqlite3.Connection, artifact_id: int
) -> tuple[float, dict[str, float]]:
    artifact = conn.execute("SELECT * FROM artifacts WHERE id = ?", (artifact_id,)).fetchone()
    if artifact is None:
        raise ValueError(f"Artifact not found: {artifact_id}")

    metadata = _artifact_metadata(artifact)
    issue_type = _lower(metadata.get("issue_type"))
    module_text = _artifact_text(
        metadata,
        "summary",
        "description",
        "labels",
        "components",
        "issue_type",
    )
    description = _lower(metadata.get("description"))
    reopened = _jira_reopened_after_completion(conn, [artifact_id])
    scope_change_count = _jira_scope_change_count(conn, [artifact_id])

    bug_like = _contains_any(issue_type, BUG_LIKE_ISSUE_TYPES)
    tester_relevant = bug_like or _contains_any(module_text, TESTER_MODULE_KEYWORDS)
    has_expected_actual = (
        ("actual result" in module_text and "expected result" in module_text)
        or ("actual:" in module_text and "expected:" in module_text)
    )

    breakdown = {
        "bug_or_defect": 1.5 if bug_like else 0.0,
        "done_or_resolved": 1.5 if _is_done_status(metadata.get("status")) else 0.0,
        "reproduction_steps": 1.0
        if _contains_any(module_text, ("steps to reproduce", "step to reproduce", "reproduce"))
        else 0.0,
        "expected_vs_actual": 1.0 if has_expected_actual else 0.0,
        "environment_details": 0.5
        if _contains_any(module_text, ("environment", "device", "version", "build", "ios", "android"))
        else 0.0,
        "regression_signal": 1.0
        if _contains_any(module_text, ("regression", "release", "smoke", "hotfix"))
        else 0.0,
        "test_design_signal": 1.0
        if _contains_any(
            module_text,
            (
                "test case",
                "test cases",
                "scenario",
                "edge case",
                "boundary",
                "checklist",
                "steps to reproduce",
                "actual result",
                "expected result",
                "given",
                "when",
                "then",
            ),
        )
        else 0.0,
        "discussion_signal": 0.5 if int(metadata.get("comment_count") or 0) >= 2 else 0.0,
        "module_area_match": 0.5 if _contains_any(module_text, TESTER_MODULE_KEYWORDS) else 0.0,
        "jira_reopened": -3.0 if reopened else 0.0,
        "scope_churn": -2.0 if scope_change_count >= 2 else 0.0,
        "thin_description": -1.0 if len(description) < 60 else 0.0,
        "low_relevance_issue": -1.5 if not tester_relevant else 0.0,
    }
    return sum(breakdown.values()), breakdown


def score_role(
    *,
    role: str,
    db_path=DB_PATH,
) -> dict[str, Any]:
    role_config = get_role_config(role)
    scorers = {
        "mobile-dev": score_mobile_mr,
        "business-analyst": score_ba_artifact,
        "tester-manual": score_tester_manual_artifact,
    }
    scorer = scorers[role]
    with connect(db_path) as conn:
        artifact_ids = [
            int(row["id"])
            for row in conn.execute(
                """
                SELECT id
                FROM artifacts
                WHERE kind IN ({placeholders})
                ORDER BY id
                """.format(placeholders=", ".join("?" for _ in role_config.primary_artifact_kinds)),
                role_config.primary_artifact_kinds,
            ).fetchall()
        ]
        for artifact_id in artifact_ids:
            score, breakdown = scorer(conn, artifact_id)
            upsert_score(
                conn,
                artifact_id=artifact_id,
                role=role,
                score=score,
                breakdown=breakdown,
            )
    return {"role": role, "count": len(artifact_ids)}


def select_extraction_candidates(
    conn: sqlite3.Connection,
    *,
    role: str,
    min_candidates: int = 30,
    max_candidates: int = 60,
) -> list[sqlite3.Row]:
    rows = conn.execute(
        """
        SELECT a.*, s.score, s.breakdown
        FROM scores s
        JOIN artifacts a ON a.id = s.artifact_id
        WHERE s.role = ?
        ORDER BY s.score DESC, a.id ASC
        """,
        (role,),
    ).fetchall()
    if not rows:
        return []
    desired = max(1, (len(rows) + 3) // 4)
    count = min(max_candidates, max(min_candidates, desired), len(rows))
    return rows[:count]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--role", required=True, choices=list(SUPPORTED_ROLES))
    args = parser.parse_args()

    summary = score_role(role=args.role, db_path=DB_PATH)
    print(f"Scored {summary['count']} artifacts for role={summary['role']}.")


if __name__ == "__main__":
    main()
