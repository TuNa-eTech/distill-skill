"""Canonical artifact cards for LLM extraction."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import json
import re
from html import unescape
from typing import Any

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")
_HEADING_RE = re.compile(r"<h[1-6][^>]*>(.*?)</h[1-6]>", re.IGNORECASE | re.DOTALL)


def build_artifact_card(
    *,
    artifact_id: int,
    kind: str,
    external_id: str,
    metadata: Mapping[str, Any] | None,
    blob_text: str,
    updated_at: str | None = None,
    linked_artifacts: Sequence[str] | None = None,
    artifact_context: Mapping[str, Any] | None = None,
) -> str:
    metadata_map = dict(metadata or {})
    linked = _normalize_text_list(linked_artifacts or [])
    context = dict(artifact_context or {})
    payload = _parse_blob_text(blob_text)

    if kind == "gitlab_mr":
        sections = _build_gitlab_sections(
            external_id=external_id,
            metadata=metadata_map,
            payload=payload,
            linked_artifacts=linked,
        )
    elif kind == "jira_issue":
        sections = _build_jira_sections(
            external_id=external_id,
            metadata=metadata_map,
            payload=payload,
            linked_artifacts=linked,
            jira_events=context.get("jira_events", []),
        )
    elif kind == "confluence_page":
        sections = _build_confluence_sections(
            external_id=external_id,
            metadata=metadata_map,
            payload=payload,
            linked_artifacts=linked,
        )
    else:
        sections = _build_generic_sections(
            external_id=external_id,
            metadata=metadata_map,
            payload=payload,
            linked_artifacts=linked,
        )

    if not _has_signal(sections):
        raise ValueError(
            f"Artifact {artifact_id} has insufficient signal for canonical extraction."
        )

    frontmatter = [
        "---",
        f"artifact_id: {artifact_id}",
        f"kind: {kind}",
        f"external_id: {external_id}",
        f"updated_at: {updated_at or ''}",
        f"jira_keys: {json.dumps(_normalize_text_list(metadata_map.get('jira_keys', [])), ensure_ascii=False)}",
        f"linked_artifacts: {json.dumps(linked, ensure_ascii=False)}",
        "---",
    ]

    lines = [
        *frontmatter,
        "",
        "# Summary",
        sections["summary"],
        "",
        "## Intent",
        sections["intent"],
        "",
        "## Key Changes",
        *_render_bullets(sections["key_changes"], empty="- None."),
        "",
        "## Important Files",
        *_render_code_bullets(sections["important_files"], empty="- None."),
        "",
        "## Decisions / Patterns",
        *_render_bullets(sections["decisions"], empty="- None."),
        "",
        "## Evidence Snippets",
        *_render_snippets(sections["evidence_snippets"], empty="- None."),
    ]
    return "\n".join(lines).strip()


def render_supporting_artifacts_text(supporting_artifacts: Sequence[Mapping[str, Any]]) -> str:
    if not supporting_artifacts:
        return "None."

    blocks: list[str] = []
    for index, artifact in enumerate(supporting_artifacts, start=1):
        metadata = artifact.get("metadata")
        try:
            card = build_artifact_card(
                artifact_id=int(artifact["artifact_id"]),
                kind=str(artifact["kind"]),
                external_id=str(artifact["external_id"]),
                metadata=metadata if isinstance(metadata, Mapping) else {},
                blob_text=str(artifact.get("blob_text") or ""),
                updated_at=_coerce_text(artifact.get("updated_at")),
                linked_artifacts=[],
                artifact_context=artifact.get("context")
                if isinstance(artifact.get("context"), Mapping)
                else {},
            )
        except ValueError:
            fallback = _first_non_empty(
                _coerce_text(
                    (metadata or {}).get("summary") if isinstance(metadata, Mapping) else ""
                ),
                _coerce_text(
                    (metadata or {}).get("title") if isinstance(metadata, Mapping) else ""
                ),
                str(artifact["external_id"]),
            ) or str(artifact["external_id"])
            card = f"# Summary\n{fallback}\n\n## Intent\nNo supporting details available."

        blocks.append(
            "\n".join(
                [
                    f"### Supporting Artifact {index}",
                    f"- kind: {artifact['kind']}",
                    f"- external_id: {artifact['external_id']}",
                    f"- link_type: {artifact.get('link_type') or 'related'}",
                    f"- confidence: {float(artifact.get('confidence', 0.0)):.2f}",
                    "",
                    card,
                ]
            ).strip()
        )
    return "\n\n".join(blocks)


def _build_gitlab_sections(
    *,
    external_id: str,
    metadata: Mapping[str, Any],
    payload: Any,
    linked_artifacts: Sequence[str],
) -> dict[str, list[str] | str]:
    payload_map = payload if isinstance(payload, Mapping) else {}
    mr = payload_map.get("mr") if isinstance(payload_map.get("mr"), Mapping) else {}
    changes = payload_map.get("changes") if isinstance(payload_map.get("changes"), Mapping) else {}
    discussions = (
        payload_map.get("discussions") if isinstance(payload_map.get("discussions"), list) else []
    )
    commits = payload_map.get("commits") if isinstance(payload_map.get("commits"), list) else []

    title = _first_non_empty(metadata.get("title"), mr.get("title"), external_id) or external_id
    description = _first_non_empty(metadata.get("description"), mr.get("description"))
    changed_files = _normalize_text_list(metadata.get("changed_files"))
    if not changed_files and isinstance(changes.get("changes"), list):
        changed_files = _normalize_text_list(
            [
                change.get("new_path") or change.get("old_path")
                for change in changes.get("changes", [])
                if isinstance(change, Mapping)
            ]
        )
    labels = _normalize_text_list(metadata.get("labels") or mr.get("labels") or [])
    author = _first_non_empty(
        metadata.get("author_username"),
        metadata.get("author"),
        (mr.get("author") or {}).get("username") if isinstance(mr.get("author"), Mapping) else None,
    )
    source_branch = _first_non_empty(metadata.get("source_branch"), mr.get("source_branch"))
    target_branch = _first_non_empty(metadata.get("target_branch"), mr.get("target_branch"))
    state = _first_non_empty(metadata.get("state"), mr.get("state"))

    key_changes: list[str] = []
    if labels:
        key_changes.append(f"Labels: {', '.join(labels[:4])}")
    if author:
        key_changes.append(f"Author: {author}")
    if changed_files:
        key_changes.extend([f"Changed file: {path}" for path in changed_files[:4]])
    if commits:
        key_changes.append(f"Commit count: {len(commits)}")
    discussion_count = _coerce_int(metadata.get("discussion_count")) or len(discussions)
    if discussion_count:
        key_changes.append(f"Discussion threads: {discussion_count}")

    decisions: list[str] = []
    if state:
        decisions.append(f"State: {state}")
    if source_branch:
        decisions.append(f"Source branch: {source_branch}")
    if target_branch:
        decisions.append(f"Target branch: {target_branch}")
    resolved = _coerce_int(metadata.get("resolved_discussions")) or _coerce_int(
        metadata.get("resolved_discussion_count")
    )
    if resolved is None and discussions:
        resolved = sum(
            1
            for discussion in discussions
            if isinstance(discussion, Mapping) and discussion.get("resolved")
        )
    if discussion_count:
        decisions.append(f"Resolved discussions: {resolved or 0}/{discussion_count}")
    if linked_artifacts:
        decisions.append(f"Linked artifacts: {', '.join(linked_artifacts[:4])}")

    evidence = _take_unique(
        [
            title,
            description,
            *[
                _coerce_text((commit or {}).get("message"))
                for commit in commits
                if isinstance(commit, Mapping)
            ],
            *[
                _clean_text((note or {}).get("body"))
                for discussion in discussions
                if isinstance(discussion, Mapping)
                for note in discussion.get("notes", [])
                if isinstance(note, Mapping)
            ],
            *[
                _coerce_text(line)
                for change in changes.get("changes", [])
                if isinstance(change, Mapping)
                for line in _extract_diff_evidence(change.get("diff"))
            ],
            *changed_files,
        ],
        limit=8,
    )

    return {
        "summary": title,
        "intent": _first_non_empty(
            description,
            next(iter([item for item in evidence if item != title]), ""),
            "No concise intent is available.",
        )
        or "No concise intent is available.",
        "key_changes": key_changes,
        "important_files": changed_files[:6],
        "decisions": decisions,
        "evidence_snippets": evidence,
    }


def _build_jira_sections(
    *,
    external_id: str,
    metadata: Mapping[str, Any],
    payload: Any,
    linked_artifacts: Sequence[str],
    jira_events: Sequence[Mapping[str, Any]],
) -> dict[str, list[str] | str]:
    payload_map = payload if isinstance(payload, Mapping) else {}
    fields = payload_map.get("fields") if isinstance(payload_map.get("fields"), Mapping) else {}
    comments_payload = payload_map.get("comments")
    comments = comments_payload if isinstance(comments_payload, list) else []

    summary = (
        _first_non_empty(metadata.get("summary"), fields.get("summary"), external_id) or external_id
    )
    description = _first_non_empty(metadata.get("description"), fields.get("description"))
    status = _first_non_empty(metadata.get("status"), ((fields.get("status") or {}).get("name")))
    issue_type = _first_non_empty(
        metadata.get("issue_type"), ((fields.get("issuetype") or {}).get("name"))
    )
    labels = _normalize_text_list(metadata.get("labels") or fields.get("labels") or [])
    components = _normalize_text_list(
        metadata.get("components")
        or [
            component.get("name")
            for component in fields.get("components", [])
            if isinstance(component, Mapping)
        ]
    )
    comment_count = _coerce_int(metadata.get("comment_count"))
    if comment_count is None:
        comment_count = len(comments)

    lifecycle_lines = _render_jira_events(jira_events)

    key_changes: list[str] = []
    if issue_type:
        key_changes.append(f"Issue type: {issue_type}")
    if status:
        key_changes.append(f"Current status: {status}")
    if labels:
        key_changes.append(f"Labels: {', '.join(labels[:4])}")
    if components:
        key_changes.append(f"Components: {', '.join(components[:4])}")
    if comment_count:
        key_changes.append(f"Comment count: {comment_count}")
    if lifecycle_lines:
        key_changes.append(f"Lifecycle events: {len(lifecycle_lines)} captured")

    decisions: list[str] = []
    if linked_artifacts:
        decisions.append(f"Linked artifacts: {', '.join(linked_artifacts[:4])}")
    decisions.extend(lifecycle_lines[:4])

    evidence = _take_unique(
        [
            summary,
            description,
            *[
                _clean_text((comment or {}).get("body"))
                for comment in comments
                if isinstance(comment, Mapping)
            ],
            *[_coerce_text(item) for item in labels],
            *[_coerce_text(item) for item in components],
        ],
        limit=8,
    )

    return {
        "summary": summary,
        "intent": _first_non_empty(
            description,
            next(iter([item for item in evidence if item != summary]), ""),
            "No concise intent is available.",
        )
        or "No concise intent is available.",
        "key_changes": key_changes,
        "important_files": [],
        "decisions": decisions,
        "evidence_snippets": evidence,
    }


def _build_confluence_sections(
    *,
    external_id: str,
    metadata: Mapping[str, Any],
    payload: Any,
    linked_artifacts: Sequence[str],
) -> dict[str, list[str] | str]:
    payload_map = payload if isinstance(payload, Mapping) else {}
    title = (
        _first_non_empty(metadata.get("title"), payload_map.get("title"), external_id)
        or external_id
    )
    body_text = _first_non_empty(metadata.get("body_text"))

    storage_value = ""
    body = payload_map.get("body")
    if isinstance(body, Mapping):
        storage = body.get("storage")
        if isinstance(storage, Mapping):
            storage_value = str(storage.get("value") or "")

    headings = _extract_headings(storage_value)
    clean_storage_text = _clean_text(storage_value)
    version_number = _first_non_empty(metadata.get("version_number"))
    space = _first_non_empty(metadata.get("space"))
    labels = _normalize_text_list(metadata.get("labels"))

    abstract = _first_non_empty(body_text, clean_storage_text)

    key_changes: list[str] = []
    if space:
        key_changes.append(f"Space: {space}")
    if version_number:
        key_changes.append(f"Version: {version_number}")
    if labels:
        key_changes.append(f"Labels: {', '.join(labels[:4])}")
    if headings:
        key_changes.extend([f"Heading: {heading}" for heading in headings[:4]])

    decisions: list[str] = []
    if linked_artifacts:
        decisions.append(f"Linked artifacts: {', '.join(linked_artifacts[:4])}")
    if _first_non_empty(metadata.get("updated_by")):
        decisions.append(f"Updated by: {metadata['updated_by']}")
    if _first_non_empty(metadata.get("version_when")):
        decisions.append(f"Version timestamp: {metadata['version_when']}")

    evidence = _take_unique(
        [
            title,
            abstract,
            *headings,
        ],
        limit=8,
    )

    return {
        "summary": title,
        "intent": _first_non_empty(
            abstract,
            next(iter([item for item in evidence if item != title]), ""),
            "No concise intent is available.",
        )
        or "No concise intent is available.",
        "key_changes": key_changes,
        "important_files": [],
        "decisions": decisions,
        "evidence_snippets": evidence,
    }


def _build_generic_sections(
    *,
    external_id: str,
    metadata: Mapping[str, Any],
    payload: Any,
    linked_artifacts: Sequence[str],
) -> dict[str, list[str] | str]:
    payload_map = payload if isinstance(payload, Mapping) else {}
    summary = (
        _first_non_empty(metadata.get("title"), metadata.get("summary"), external_id) or external_id
    )
    intent = _first_non_empty(
        metadata.get("description"), metadata.get("body_text"), _coerce_text(payload_map)
    )
    decisions = [f"Linked artifacts: {', '.join(linked_artifacts[:4])}"] if linked_artifacts else []
    evidence = _take_unique([summary, intent], limit=4)
    return {
        "summary": summary,
        "intent": intent or "No concise intent is available.",
        "key_changes": [],
        "important_files": _normalize_text_list(metadata.get("changed_files"))[:6],
        "decisions": decisions,
        "evidence_snippets": evidence,
    }


def _parse_blob_text(blob_text: str) -> Any:
    if not blob_text:
        return {}
    try:
        return json.loads(blob_text)
    except json.JSONDecodeError:
        return {}


def _render_jira_events(jira_events: Sequence[Mapping[str, Any]]) -> list[str]:
    lines: list[str] = []
    for event in jira_events:
        event_kind = _coerce_text(event.get("event_kind"))
        if not event_kind:
            continue
        from_value = _coerce_text(event.get("from_value"))
        to_value = _coerce_text(event.get("to_value"))
        occurred_at = _coerce_text(event.get("occurred_at"))
        transition = (
            " -> ".join([item for item in [from_value, to_value] if item]) or "state updated"
        )
        if occurred_at:
            lines.append(f"{event_kind}: {transition} @ {occurred_at}")
        else:
            lines.append(f"{event_kind}: {transition}")
    return lines


def _extract_diff_evidence(diff_text: Any) -> list[str]:
    if not isinstance(diff_text, str):
        return []
    candidates: list[str] = []
    for line in diff_text.splitlines():
        if not line.startswith("+") or line.startswith("+++"):
            continue
        snippet = _clean_text(line[1:])
        if len(snippet) < 6:
            continue
        candidates.append(snippet[:240])
    return candidates


def _extract_headings(html_text: str) -> list[str]:
    if not html_text:
        return []
    headings = [_clean_text(unescape(match)) for match in _HEADING_RE.findall(html_text)]
    return _take_unique(headings, limit=6)


def _normalize_text_list(values: Any) -> list[str]:
    if isinstance(values, (str, bytes)):
        values = [values]
    if not isinstance(values, Sequence):
        return []
    normalized: list[str] = []
    for value in values:
        text = _clean_text(value)
        if text:
            normalized.append(text)
    return _take_unique(normalized, limit=None)


def _take_unique(values: Sequence[str], *, limit: int | None) -> list[str]:
    seen: set[str] = set()
    items: list[str] = []
    for value in values:
        text = _clean_text(value)
        if not text:
            continue
        key = text.casefold()
        if key in seen:
            continue
        seen.add(key)
        items.append(text[:240])
        if limit is not None and len(items) >= limit:
            break
    return items


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        try:
            value = json.dumps(value, ensure_ascii=False, sort_keys=True)
        except TypeError:
            value = str(value)
    text = unescape(str(value))
    text = _TAG_RE.sub(" ", text)
    text = _WS_RE.sub(" ", text)
    return text.strip()


def _first_non_empty(*values: Any) -> str:
    for value in values:
        text = _clean_text(value)
        if text:
            return text
    return ""


def _render_bullets(items: Sequence[str], *, empty: str) -> list[str]:
    if not items:
        return [empty]
    return [f"- {item}" for item in items]


def _render_code_bullets(items: Sequence[str], *, empty: str) -> list[str]:
    if not items:
        return [empty]
    return [f"- `{item}`" for item in items]


def _render_snippets(items: Sequence[str], *, empty: str) -> list[str]:
    if not items:
        return [empty]
    return [f"- {json.dumps(item, ensure_ascii=False)}" for item in items]


def _coerce_text(value: Any) -> str:
    return _clean_text(value)


def _coerce_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _has_signal(sections: Mapping[str, Any]) -> bool:
    return bool(
        _clean_text(sections.get("summary"))
        and (
            _clean_text(sections.get("intent"))
            or sections.get("key_changes")
            or sections.get("important_files")
            or sections.get("evidence_snippets")
        )
    )
