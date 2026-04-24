"""Crawl Jira issues and lifecycle events into SQLite with redacted JSON blobs."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
from typing import Any

import requests

from distill_core.config import BLOBS_DIR, DB_PATH, env
from distill_core.db import connect, insert_jira_event, upsert_artifact

from ._common import (
    DEFAULT_TIMEOUT,
    extract_jira_keys,
    is_done_status,
    is_started_status,
    join_url,
    resolve_date_window,
    save_json_blob,
    within_date_range,
)

DEFAULT_MAX_ITEMS = 200
DEFAULT_API_VERSION = "2"


def _resolve_auth_mode(*, username: str, explicit: str | None = None) -> str:
    mode = (
        (explicit or env("JIRA_AUTH_MODE") or env("ATLASSIAN_AUTH_MODE") or "auto").strip().lower()
    )
    if mode in {"basic", "bearer"}:
        return mode
    return "bearer"


def _api_version(explicit: str | None = None) -> str:
    version = (explicit or env("JIRA_API_VERSION") or DEFAULT_API_VERSION).strip()
    return version or DEFAULT_API_VERSION


def build_session(*, username: str, token: str, auth_mode: str | None = None) -> requests.Session:
    session = requests.Session()
    session.headers.update({"Accept": "application/json"})
    resolved_auth_mode = _resolve_auth_mode(username=username, explicit=auth_mode)
    if resolved_auth_mode == "basic":
        session.auth = (username, token)
    else:
        session.headers.update({"Authorization": f"Bearer {token}"})
    return session


def fetch_issues(
    *,
    session: requests.Session,
    base_url: str,
    project_key: str,
    api_version: str = DEFAULT_API_VERSION,
    since: date,
    until: date,
    cap: int = DEFAULT_MAX_ITEMS,
) -> list[dict[str, Any]]:
    url = join_url(base_url, f"rest/api/{api_version}/search")
    jql = (
        f'project = "{project_key}" '
        f'AND updated >= "{since.isoformat()}" '
        f'AND updated <= "{until.isoformat()}" '
        "ORDER BY updated DESC"
    )
    items: list[dict[str, Any]] = []
    start_at = 0
    while len(items) < cap:
        response = session.get(
            url,
            params={
                "jql": jql,
                "startAt": start_at,
                "maxResults": 100,
                "expand": "changelog,renderedFields",
                "fields": ",".join(
                    [
                        "assignee",
                        "components",
                        "created",
                        "description",
                        "issuetype",
                        "labels",
                        "reporter",
                        "resolutiondate",
                        "status",
                        "summary",
                        "updated",
                    ]
                ),
            },
            timeout=DEFAULT_TIMEOUT,
        )
        response.raise_for_status()
        page = response.json()
        page_items = page.get("issues", [])
        if not page_items:
            break
        for item in page_items:
            updated_at = (item.get("fields") or {}).get("updated")
            if within_date_range(updated_at, since=since, until=until):
                items.append(item)
                if len(items) >= cap:
                    break
        if start_at + len(page_items) >= page.get("total", 0) or len(page_items) < page.get(
            "maxResults", 100
        ):
            break
        start_at += page.get("maxResults", 100)
    return items


def extract_lifecycle_events(issue: dict[str, Any]) -> list[dict[str, Any]]:
    histories = sorted(
        (issue.get("changelog") or {}).get("histories", []),
        key=lambda history: history.get("created") or "",
    )
    started = False
    events: list[dict[str, Any]] = []
    for history in histories:
        occurred_at = history.get("created")
        for item in history.get("items", []):
            field = (item.get("field") or "").casefold()
            from_value = item.get("fromString")
            to_value = item.get("toString")

            if field == "status":
                events.append(
                    {
                        "event_kind": "status_change",
                        "from_value": from_value,
                        "to_value": to_value,
                        "occurred_at": occurred_at,
                    }
                )
                if is_started_status(to_value):
                    started = True
                if is_done_status(from_value) and not is_done_status(to_value):
                    events.append(
                        {
                            "event_kind": "reopened",
                            "from_value": from_value,
                            "to_value": to_value,
                            "occurred_at": occurred_at,
                        }
                    )
            elif field in {"description", "summary"} and started:
                events.append(
                    {
                        "event_kind": "scope_change",
                        "from_value": from_value,
                        "to_value": to_value,
                        "occurred_at": occurred_at,
                    }
                )
    return events


def summarize_issue(issue: dict[str, Any]) -> dict[str, Any]:
    fields = issue.get("fields") or {}
    summary = fields.get("summary", "")
    description = fields.get("description", "")
    if isinstance(description, dict):
        description = str(description)
    comments = issue.get("comments", [])
    return {
        "key": issue.get("key"),
        "summary": summary,
        "description": description,
        "status": ((fields.get("status") or {}).get("name")),
        "issue_type": ((fields.get("issuetype") or {}).get("name")),
        "labels": fields.get("labels", []),
        "components": [component.get("name") for component in fields.get("components", [])],
        "assignee": ((fields.get("assignee") or {}).get("displayName")),
        "reporter": ((fields.get("reporter") or {}).get("displayName")),
        "resolution_date": fields.get("resolutiondate"),
        "comment_count": len(comments),
        "jira_keys": extract_jira_keys(issue.get("key"), summary, description),
    }


def run_ingest(
    *,
    session: requests.Session | None = None,
    base_url: str,
    project_key: str,
    username: str,
    token: str,
    auth_mode: str | None = None,
    api_version: str | None = None,
    db_path: Path = DB_PATH,
    blob_root: Path = BLOBS_DIR,
    since: date,
    until: date,
    max_items: int = DEFAULT_MAX_ITEMS,
) -> dict[str, int]:
    client = session or build_session(username=username, token=token, auth_mode=auth_mode)
    resolved_api_version = _api_version(api_version)
    issues = fetch_issues(
        session=client,
        base_url=base_url,
        project_key=project_key,
        api_version=resolved_api_version,
        since=since,
        until=until,
        cap=max_items,
    )

    ingested = 0
    with connect(db_path) as conn:
        for issue in issues:
            payload = dict(issue)
            payload["comments"] = fetch_issue_comments(
                session=client,
                base_url=base_url,
                api_version=resolved_api_version,
                issue_key=issue["key"],
            )
            blob_path = save_json_blob(
                "jira/issue",
                issue["key"],
                payload,
                blob_root=blob_root,
            )
            artifact_id = upsert_artifact(
                conn,
                kind="jira_issue",
                external_id=issue["key"],
                created_at=(issue.get("fields") or {}).get("created"),
                updated_at=(issue.get("fields") or {}).get("updated"),
                metadata=summarize_issue(payload),
                blob_path=blob_path,
            )
            conn.execute("DELETE FROM jira_events WHERE issue_id = ?", (artifact_id,))
            for event in extract_lifecycle_events(issue):
                insert_jira_event(conn, issue_id=artifact_id, **event)
            ingested += 1
    return {"fetched": len(issues), "ingested": ingested}


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--since", help="Inclusive start date (YYYY-MM-DD)")
    parser.add_argument("--until", help="Inclusive end date (YYYY-MM-DD)")
    parser.add_argument(
        "--window", type=int, help="Rolling-day fallback if explicit dates are absent"
    )
    parser.add_argument("--max-items", type=int, default=DEFAULT_MAX_ITEMS, help="Local ingest cap")
    args = parser.parse_args(argv)

    since, until = resolve_date_window(since=args.since, until=args.until, window=args.window)
    result = ingest_jira(
        since=since.isoformat(),
        until=until.isoformat(),
        limit=args.max_items,
    )
    print(f"Jira ingest complete: {result} issues ({since.isoformat()}..{until.isoformat()})")


def _jira_username() -> str:
    return (
        env("JIRA_USER_NAME")
        or env("JIRA_EMAIL")
        or env("ATLASSIAN_USER_NAME", required=True)
        or ""
    )


def _jira_token() -> str:
    return (
        env("JIRA_PERSONAL_TOKEN")
        or env("JIRA_TOKEN")
        or env("ATLASSIAN_TOKEN", required=True)
        or ""
    )


def fetch_issue_comments(
    *,
    session: requests.Session,
    base_url: str,
    api_version: str = DEFAULT_API_VERSION,
    issue_key: str,
) -> list[dict[str, Any]]:
    url = join_url(base_url, f"rest/api/{api_version}/issue", issue_key, "comment")
    response = session.get(url, timeout=DEFAULT_TIMEOUT)
    response.raise_for_status()
    payload = response.json()
    return payload.get("comments", [])


def ingest_jira(
    *,
    since: str,
    until: str,
    limit: int = DEFAULT_MAX_ITEMS,
    session: requests.Session | None = None,
    db_path: Path = DB_PATH,
    base_url: str | None = None,
    project_key: str | None = None,
    username: str | None = None,
    token: str | None = None,
    auth_mode: str | None = None,
    api_version: str | None = None,
) -> int:
    resolved_base_url = base_url or (
        env("JIRA_URL", required=session is None) or "https://company.atlassian.net"
    )
    resolved_project_key = project_key or (
        env("JIRA_PROJECT_KEY", required=session is None) or "APP"
    )
    resolved_username = username or (_jira_username() if session is None else "")
    resolved_token = token or (_jira_token() if session is None else "")
    resolved_auth_mode = auth_mode or env("JIRA_AUTH_MODE") or env("ATLASSIAN_AUTH_MODE")
    resolved_api_version = api_version or env("JIRA_API_VERSION") or DEFAULT_API_VERSION
    result = run_ingest(
        session=session,
        base_url=resolved_base_url,
        project_key=resolved_project_key,
        username=resolved_username,
        token=resolved_token,
        auth_mode=resolved_auth_mode,
        api_version=resolved_api_version,
        db_path=db_path,
        blob_root=BLOBS_DIR,
        since=date.fromisoformat(since),
        until=date.fromisoformat(until),
        max_items=limit,
    )
    return result["ingested"]


if __name__ == "__main__":
    main()
