"""Crawl Confluence pages into SQLite with redacted JSON blobs."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
from typing import Any

import requests

from distill_core.config import BLOBS_DIR, DB_PATH, env
from distill_core.db import connect, upsert_artifact

from ._common import (
    DEFAULT_TIMEOUT,
    extract_jira_keys,
    join_url,
    resolve_date_window,
    save_json_blob,
    strip_html,
    within_date_range,
)

DEFAULT_MAX_ITEMS = 80


def _resolve_auth_mode(*, username: str, explicit: str | None = None) -> str:
    mode = (
        (explicit or env("CONFLUENCE_AUTH_MODE") or env("ATLASSIAN_AUTH_MODE") or "auto")
        .strip()
        .lower()
    )
    if mode in {"basic", "bearer"}:
        return mode
    return "basic"


def build_session(*, username: str, token: str, auth_mode: str | None = None) -> requests.Session:
    session = requests.Session()
    session.headers.update({"Accept": "application/json"})
    resolved_auth_mode = _resolve_auth_mode(username=username, explicit=auth_mode)
    if resolved_auth_mode == "basic":
        session.auth = (username, token)
    else:
        session.headers.update({"Authorization": f"Bearer {token}"})
    return session


def fetch_pages(
    *,
    session: requests.Session,
    base_url: str,
    space: str,
    since: date,
    until: date,
    cap: int = DEFAULT_MAX_ITEMS,
) -> list[dict[str, Any]]:
    url = join_url(base_url, "rest/api/content/search")
    cql = (
        f'space = "{space}" '
        "AND type = page "
        f'AND lastmodified >= "{since.isoformat()}" '
        f'AND lastmodified <= "{until.isoformat()}" '
        "ORDER BY lastmodified DESC"
    )
    items: list[dict[str, Any]] = []
    start = 0
    while len(items) < cap:
        response = session.get(
            url,
            params={
                "cql": cql,
                "expand": "body.storage,history,metadata.labels,version",
                "limit": 50,
                "start": start,
            },
            timeout=DEFAULT_TIMEOUT,
        )
        response.raise_for_status()
        page = response.json()
        page_items = page.get("results", [])
        if not page_items:
            break
        for item in page_items:
            version = item.get("version") or {}
            updated_at = version.get("when") or ((item.get("history") or {}).get("createdDate"))
            if within_date_range(updated_at, since=since, until=until):
                items.append(item)
                if len(items) >= cap:
                    break
        if len(page_items) < page.get("limit", 50):
            break
        start += page.get("limit", 50)
    return items


def summarize_page(page: dict[str, Any], *, base_url: str, space: str) -> dict[str, Any]:
    storage = (((page.get("body") or {}).get("storage")) or {}).get("value", "")
    body_text = strip_html(storage)
    version = page.get("version") or {}
    labels = (((page.get("metadata") or {}).get("labels")) or {}).get("results", [])
    webui = ((page.get("_links") or {}).get("webui")) or ""
    return {
        "page_id": page.get("id"),
        "title": page.get("title", ""),
        "space": space,
        "status": page.get("status"),
        "body_text": body_text,
        "version_number": version.get("number"),
        "version_when": version.get("when"),
        "labels": [label.get("name") for label in labels],
        "updated_by": (version.get("by") or {}).get("displayName"),
        "web_url": join_url(base_url, webui) if webui else None,
        "jira_keys": extract_jira_keys(page.get("title"), body_text),
    }


def run_ingest(
    *,
    session: requests.Session | None = None,
    base_url: str,
    space: str,
    username: str,
    token: str,
    auth_mode: str | None = None,
    db_path: Path = DB_PATH,
    blob_root: Path = BLOBS_DIR,
    since: date,
    until: date,
    max_items: int = DEFAULT_MAX_ITEMS,
) -> dict[str, int]:
    client = session or build_session(username=username, token=token, auth_mode=auth_mode)
    pages = fetch_pages(
        session=client,
        base_url=base_url,
        space=space,
        since=since,
        until=until,
        cap=max_items,
    )
    ingested = 0
    with connect(db_path) as conn:
        for page in pages:
            blob_path = save_json_blob(
                "confluence/page",
                str(page["id"]),
                page,
                blob_root=blob_root,
            )
            upsert_artifact(
                conn,
                kind="confluence_page",
                external_id=f"page:{page['id']}",
                created_at=((page.get("history") or {}).get("createdDate")),
                updated_at=((page.get("version") or {}).get("when")),
                metadata=summarize_page(page, base_url=base_url, space=space),
                blob_path=blob_path,
            )
            ingested += 1
    return {"fetched": len(pages), "ingested": ingested}


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
    result = ingest_confluence(
        since=since.isoformat(),
        until=until.isoformat(),
        limit=args.max_items,
    )
    print(f"Confluence ingest complete: {result} pages ({since.isoformat()}..{until.isoformat()})")


def _confluence_username() -> str:
    return (
        env("CONFLUENCE_USER_NAME")
        or env("CONFLUENCE_EMAIL")
        or env("ATLASSIAN_USER_NAME", required=True)
        or ""
    )


def _confluence_token() -> str:
    return (
        env("CONFLUENCE_PERSONAL_TOKEN")
        or env("CONFLUENCE_TOKEN")
        or env("ATLASSIAN_TOKEN", required=True)
        or ""
    )


def ingest_confluence(
    *,
    since: str,
    until: str,
    limit: int = DEFAULT_MAX_ITEMS,
    session: requests.Session | None = None,
    db_path: Path = DB_PATH,
    base_url: str | None = None,
    space: str | None = None,
    username: str | None = None,
    token: str | None = None,
    auth_mode: str | None = None,
) -> int:
    resolved_base_url = base_url or (
        env("CONFLUENCE_URL", required=session is None) or "https://company.atlassian.net/wiki"
    )
    resolved_space = space or (env("CONFLUENCE_SPACE", required=session is None) or "MOB")
    resolved_username = username or (_confluence_username() if session is None else "")
    resolved_token = token or (_confluence_token() if session is None else "")
    resolved_auth_mode = auth_mode or env("CONFLUENCE_AUTH_MODE") or env("ATLASSIAN_AUTH_MODE")
    result = run_ingest(
        session=session,
        base_url=resolved_base_url,
        space=resolved_space,
        username=resolved_username,
        token=resolved_token,
        auth_mode=resolved_auth_mode,
        db_path=db_path,
        blob_root=BLOBS_DIR,
        since=date.fromisoformat(since),
        until=date.fromisoformat(until),
        max_items=limit,
    )
    return result["ingested"]


if __name__ == "__main__":
    main()
