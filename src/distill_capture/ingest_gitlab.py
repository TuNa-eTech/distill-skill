"""Crawl GitLab merge requests into SQLite with redacted JSON blobs."""
from __future__ import annotations

import argparse
import math
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

import requests

from distill_core.config import BLOBS_DIR, DB_PATH, env
from distill_core.db import connect, upsert_artifact

from ._common import (
    DEFAULT_TIMEOUT,
    extract_jira_keys,
    has_test_path,
    is_mobile_path,
    join_url,
    parse_datetime,
    resolve_date_window,
    save_json_blob,
    within_date_range,
)

DEFAULT_MAX_ITEMS = 120
DEFAULT_GROUP_SEED_CAP = 10


def _encode_ref(ref: str) -> str:
    return quote(str(ref).strip(), safe="")


def _project_target(project: dict[str, Any] | None, fallback_ref: str) -> dict[str, Any]:
    return {
        "id": str((project or {}).get("id") or fallback_ref),
        "path_with_namespace": (project or {}).get("path_with_namespace") or str(fallback_ref),
        "web_url": (project or {}).get("web_url"),
        "last_activity_at": (project or {}).get("last_activity_at"),
        "name": (project or {}).get("name"),
    }


def _mr_external_id(*, project_id: str, mr_iid: int | str) -> str:
    return f"{project_id}!{mr_iid}"


def _candidate_updated_at(item: tuple[dict[str, Any], dict[str, Any]]) -> datetime:
    _, mr = item
    return parse_datetime(mr.get("updated_at")) or datetime.min.replace(tzinfo=timezone.utc)


def build_session(*, token: str | None = None) -> requests.Session:
    session = requests.Session()
    session.headers.update({"PRIVATE-TOKEN": token or env("GITLAB_TOKEN", required=True) or ""})
    return session


def fetch_mrs(
    *,
    session: requests.Session,
    base_url: str,
    project_id: str,
    since: date,
    until: date,
    cap: int = DEFAULT_MAX_ITEMS,
    page_size: int | None = None,
) -> list[dict[str, Any]]:
    url = join_url(base_url, "api/v4/projects", _encode_ref(project_id), "merge_requests")
    params = {
        "scope": "all",
        "state": "all",
        "order_by": "updated_at",
        "sort": "desc",
        "updated_after": f"{since.isoformat()}T00:00:00Z",
        "updated_before": f"{until.isoformat()}T23:59:59Z",
    }
    items: list[dict[str, Any]] = []
    page = 1
    per_page = min(100, max(1, page_size or cap))
    while len(items) < cap:
        response = session.get(
            url,
            params={**params, "page": page, "per_page": per_page},
            timeout=DEFAULT_TIMEOUT,
        )
        response.raise_for_status()
        page_items = response.json()
        if not page_items:
            break
        for item in page_items:
            if within_date_range(item.get("updated_at"), since=since, until=until):
                items.append(item)
                if len(items) >= cap:
                    break
        if len(page_items) < per_page:
            break
        page += 1
    return items


def fetch_project(
    *, session: requests.Session, base_url: str, project_ref: str
) -> dict[str, Any] | None:
    url = join_url(base_url, "api/v4/projects", _encode_ref(project_ref))
    response = session.get(url, timeout=DEFAULT_TIMEOUT)
    if response.status_code == 404:
        return None
    response.raise_for_status()
    payload = response.json()
    return payload if isinstance(payload, dict) else None


def list_group_projects(
    *,
    session: requests.Session,
    base_url: str,
    group_ref: str,
) -> list[dict[str, Any]]:
    url = join_url(base_url, "api/v4/groups", _encode_ref(group_ref), "projects")
    items: list[dict[str, Any]] = []
    page = 1
    while True:
        response = session.get(
            url,
            params={
                "include_subgroups": "true",
                "simple": "true",
                "archived": "false",
                "order_by": "last_activity_at",
                "sort": "desc",
                "page": page,
                "per_page": 100,
            },
            timeout=DEFAULT_TIMEOUT,
        )
        if response.status_code == 404:
            return []
        response.raise_for_status()
        page_items = response.json()
        if not page_items:
            break
        items.extend(page_items)
        if len(page_items) < 100:
            break
        page += 1
    return [_project_target(project, str(project.get("id") or "")) for project in items]


def fetch_mr_discussions(
    *, session: requests.Session, base_url: str, project_id: str, mr_iid: int
) -> list[dict[str, Any]]:
    return _fetch_gitlab_list(
        session=session,
        url=join_url(
            base_url,
            "api/v4/projects",
            project_id,
            "merge_requests",
            str(mr_iid),
            "discussions",
        ),
    )


def fetch_mr_commits(
    *, session: requests.Session, base_url: str, project_id: str, mr_iid: int
) -> list[dict[str, Any]]:
    return _fetch_gitlab_list(
        session=session,
        url=join_url(
            base_url,
            "api/v4/projects",
            project_id,
            "merge_requests",
            str(mr_iid),
            "commits",
        ),
    )


def fetch_mr_changes(
    *, session: requests.Session, base_url: str, project_id: str, mr_iid: int
) -> dict[str, Any]:
    url = join_url(
        base_url,
        "api/v4/projects",
        project_id,
        "merge_requests",
        str(mr_iid),
        "changes",
    )
    response = session.get(url, timeout=DEFAULT_TIMEOUT)
    response.raise_for_status()
    return response.json()


def summarize_mr(
    mr: dict[str, Any],
    *,
    project: dict[str, Any],
    discussions: list[dict[str, Any]],
    commits: list[dict[str, Any]],
    changes: dict[str, Any],
) -> dict[str, Any]:
    changed_files = [
        change.get("new_path") or change.get("old_path")
        for change in changes.get("changes", [])
        if change.get("new_path") or change.get("old_path")
    ]
    discussion_count = len(discussions)
    resolved_discussions = sum(1 for discussion in discussions if discussion.get("resolved"))
    project_id = str(project.get("id") or "")
    return {
        "iid": mr.get("iid"),
        "project_id": project_id,
        "project_path_with_namespace": project.get("path_with_namespace", ""),
        "project_web_url": project.get("web_url"),
        "title": mr.get("title", ""),
        "description": mr.get("description", ""),
        "state": mr.get("state"),
        "web_url": mr.get("web_url"),
        "source_branch": mr.get("source_branch"),
        "target_branch": mr.get("target_branch"),
        "labels": mr.get("labels", []),
        "author": (mr.get("author") or {}).get("username"),
        "merged_at": mr.get("merged_at"),
        "changed_files": changed_files,
        "discussion_count": discussion_count,
        "resolved_discussions": resolved_discussions,
        "commit_count": len(commits),
        "mobile_touch": any(is_mobile_path(path) for path in changed_files),
        "test_touch": has_test_path(changed_files),
        "jira_keys": extract_jira_keys(
            mr.get("title"), mr.get("source_branch"), mr.get("description")
        ),
    }


def run_ingest(
    *,
    session: requests.Session | None = None,
    base_url: str,
    project_id: str | None = None,
    project_ids: list[str] | None = None,
    project_targets: list[dict[str, Any]] | None = None,
    db_path: Path = DB_PATH,
    blob_root: Path = BLOBS_DIR,
    since: date,
    until: date,
    max_items: int = DEFAULT_MAX_ITEMS,
) -> dict[str, int]:
    client = session or build_session()
    targets = project_targets or []
    if not targets:
        refs = project_ids or ([project_id] if project_id else [])
        targets = [_project_target(None, ref) for ref in refs]
    if not targets:
        raise ValueError("GitLab ingest requires at least one project target.")

    if len(targets) == 1:
        merge_requests = [
            (targets[0], mr)
            for mr in fetch_mrs(
                session=client,
                base_url=base_url,
                project_id=str(targets[0]["id"]),
                since=since,
                until=until,
                cap=max_items,
            )
        ]
    else:
        seed_cap = min(
            50,
            max(
                DEFAULT_GROUP_SEED_CAP,
                math.ceil(max_items / max(1, len(targets))) + 2,
            ),
        )
        merge_requests: list[tuple[dict[str, Any], dict[str, Any]]] = []
        for target in targets:
            project_mrs = fetch_mrs(
                session=client,
                base_url=base_url,
                project_id=str(target["id"]),
                since=since,
                until=until,
                cap=seed_cap,
                page_size=seed_cap,
            )
            merge_requests.extend((target, mr) for mr in project_mrs)
        merge_requests.sort(key=_candidate_updated_at, reverse=True)
        merge_requests = merge_requests[:max_items]

    ingested = 0
    with connect(db_path) as conn:
        for target, mr in merge_requests:
            target_id = str(target["id"])
            discussions = fetch_mr_discussions(
                session=client,
                base_url=base_url,
                project_id=target_id,
                mr_iid=int(mr["iid"]),
            )
            commits = fetch_mr_commits(
                session=client,
                base_url=base_url,
                project_id=target_id,
                mr_iid=int(mr["iid"]),
            )
            changes = fetch_mr_changes(
                session=client,
                base_url=base_url,
                project_id=target_id,
                mr_iid=int(mr["iid"]),
            )
            payload = {
                "project": target,
                "mr": mr,
                "discussions": discussions,
                "commits": commits,
                "changes": changes,
            }
            blob_path = save_json_blob(
                f"gitlab/mr/{target_id}",
                str(mr["iid"]),
                payload,
                blob_root=blob_root,
            )
            metadata = summarize_mr(
                mr,
                project=target,
                discussions=discussions,
                commits=commits,
                changes=changes,
            )
            upsert_artifact(
                conn,
                kind="gitlab_mr",
                external_id=_mr_external_id(project_id=target_id, mr_iid=mr["iid"]),
                created_at=mr.get("created_at"),
                updated_at=mr.get("updated_at"),
                metadata=metadata,
                blob_path=blob_path,
            )
            ingested += 1
    return {"fetched": len(merge_requests), "ingested": ingested, "projects": len(targets)}


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--since", help="Inclusive start date (YYYY-MM-DD)")
    parser.add_argument("--until", help="Inclusive end date (YYYY-MM-DD)")
    parser.add_argument("--window", type=int, help="Rolling-day fallback if explicit dates are absent")
    parser.add_argument("--max-items", type=int, default=DEFAULT_MAX_ITEMS, help="Local ingest cap")
    args = parser.parse_args(argv)

    since, until = resolve_date_window(since=args.since, until=args.until, window=args.window)
    result = ingest_gitlab(
        since=since.isoformat(),
        until=until.isoformat(),
        limit=args.max_items,
    )
    print(
        f"GitLab ingest complete: {result} MRs "
        f"({since.isoformat()}..{until.isoformat()})"
    )


def _fetch_gitlab_list(*, session: requests.Session, url: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    page = 1
    while True:
        response = session.get(url, params={"page": page, "per_page": 100}, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
        page_items = response.json()
        if not page_items:
            break
        items.extend(page_items)
        if len(page_items) < 100:
            break
        page += 1
    return items


def ingest_gitlab(
    *,
    since: str,
    until: str,
    limit: int = DEFAULT_MAX_ITEMS,
    session: requests.Session | None = None,
    db_path: Path = DB_PATH,
    base_url: str | None = None,
    project_id: str | None = None,
    project_ids: list[str] | None = None,
    group_ref: str | None = None,
) -> int:
    def _split_refs(value: str | None) -> list[str]:
        if not value:
            return []
        return [item.strip() for item in value.split(",") if item.strip()]

    resolved_base_url = base_url or (
        env("GITLAB_URL", required=session is None) or "https://gitlab.example.com"
    )
    client = session or build_session()
    resolved_project_ids = project_ids or _split_refs(env("GITLAB_PROJECT_IDS"))
    resolved_group_ref = group_ref or env("GITLAB_GROUP_PATH") or env("GITLAB_GROUP_ID")
    required_single_project = session is None and not resolved_project_ids and not resolved_group_ref
    resolved_project_id = project_id or (
        env("GITLAB_PROJECT_ID", required=required_single_project) or ""
    )

    if resolved_group_ref:
        targets = list_group_projects(
            session=client,
            base_url=resolved_base_url,
            group_ref=resolved_group_ref,
        )
    elif resolved_project_ids:
        targets = [
            _project_target(
                fetch_project(session=client, base_url=resolved_base_url, project_ref=ref),
                ref,
            )
            for ref in resolved_project_ids
        ]
    else:
        project = fetch_project(
            session=client,
            base_url=resolved_base_url,
            project_ref=resolved_project_id,
        )
        if project is not None:
            targets = [_project_target(project, resolved_project_id)]
        else:
            targets = list_group_projects(
                session=client,
                base_url=resolved_base_url,
                group_ref=resolved_project_id,
            )
        if not targets:
            raise RuntimeError(
                "GitLab project/group not found or inaccessible: "
                f"{resolved_project_id or resolved_group_ref}"
            )

    result = run_ingest(
        session=client,
        base_url=resolved_base_url,
        project_targets=targets,
        db_path=db_path,
        blob_root=BLOBS_DIR,
        since=date.fromisoformat(since),
        until=date.fromisoformat(until),
        max_items=limit,
    )
    return result["ingested"]


if __name__ == "__main__":
    main()
