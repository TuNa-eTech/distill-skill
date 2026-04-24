"""Role registry for prompt loading and role-specific pack generation."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any


@dataclass(frozen=True)
class RoleConfig:
    name: str
    prompt_namespace: str
    primary_artifact_kinds: tuple[str, ...]
    target_modules: dict[str, str]
    module_hints: dict[str, str]
    manifest_intro: tuple[str, ...]
    writing_preferences: dict[str, Any]
    cluster_keywords: dict[str, tuple[str, ...]]


_SLUG_RE = re.compile(r"[^a-z0-9]+")


def _slugify(value: str) -> str:
    slug = _SLUG_RE.sub("-", value.lower()).strip("-")
    return re.sub(r"-{2,}", "-", slug)


ROLE_CONFIGS: dict[str, RoleConfig] = {
    "mobile-dev": RoleConfig(
        name="mobile-dev",
        prompt_namespace="mobile-dev",
        primary_artifact_kinds=("gitlab_mr",),
        target_modules={
            "state-management": "State Management",
            "navigation": "Navigation",
            "widget-testing": "Widget Testing",
            "code-review-conventions": "Code Review Conventions",
            "platform-integration": "Platform Integration",
        },
        module_hints={
            "state-management": "Task chạm state, Bloc, Cubit, Riverpod, Provider, hoặc workflow nhiều bước.",
            "navigation": "Task chạm routes, screen flow, deeplink, app shell, hoặc navigator behavior.",
            "widget-testing": "Task chạm widget tests, golden tests, hoặc integration coverage.",
            "code-review-conventions": "Luôn nạp cho review và implementation task của mobile-dev.",
            "platform-integration": "Task chạm Android, iOS, plugins, permissions, startup config, hoặc platform channels.",
        },
        manifest_intro=(
            "Bạn đang pair với một mobile engineer Flutter. Ưu tiên các hard rules dưới đây,",
            "sau đó nạp module phù hợp với ngữ cảnh task.",
        ),
        writing_preferences={
            "primary_language": "vi",
            "style": "Vietnamese-first",
            "preserve_identifiers": True,
            "avoid_app_specific_overfit": True,
        },
        cluster_keywords={
            "state-management": ("state", "bloc", "cubit", "riverpod", "provider"),
            "navigation": ("route", "router", "navigation", "deeplink"),
            "widget-testing": ("widget", "integration test", "golden", "testing"),
            "code-review-conventions": ("review", "convention", "guideline", "style"),
            "platform-integration": (
                "platform",
                "android",
                "ios",
                "plugin",
                "channel",
                "permission",
                "native",
            ),
        },
    ),
    "business-analyst": RoleConfig(
        name="business-analyst",
        prompt_namespace="business-analyst",
        primary_artifact_kinds=("jira_issue", "confluence_page"),
        target_modules={
            "spec-writing": "Spec Writing",
            "acceptance-criteria": "Acceptance Criteria",
            "discovery": "Discovery",
            "stakeholder-comms": "Stakeholder Communications",
        },
        module_hints={
            "spec-writing": "Luôn nạp khi viết hoặc chỉnh spec, PRD, solution note, hoặc feature outline.",
            "acceptance-criteria": "Task chạm user story, AC, Given/When/Then, testable behavior, hoặc scope clarity.",
            "discovery": "Task chạm research, discovery, assumptions, risks, questions, hoặc stakeholder interview synthesis.",
            "stakeholder-comms": "Task chạm status update, escalation, dependency alignment, retro summary, hoặc cross-team handoff.",
        },
        manifest_intro=(
            "Bạn đang pair với một business analyst. Ưu tiên các hard rules dưới đây,",
            "sau đó nạp module phù hợp với ngữ cảnh spec, AC, discovery, hoặc stakeholder communication.",
        ),
        writing_preferences={
            "primary_language": "vi",
            "style": "Vietnamese-first",
            "preserve_identifiers": True,
            "avoid_app_specific_overfit": True,
            "output_mode": "template-and-checklist-first",
        },
        cluster_keywords={
            "spec-writing": ("spec", "prd", "requirements", "solution", "scope"),
            "acceptance-criteria": (
                "acceptance",
                "criteria",
                "user story",
                "given",
                "when",
                "then",
            ),
            "discovery": (
                "discovery",
                "research",
                "interview",
                "analysis",
                "assumption",
                "question",
            ),
            "stakeholder-comms": (
                "stakeholder",
                "status",
                "update",
                "escalation",
                "retro",
                "handoff",
                "communication",
            ),
        },
    ),
    "tester-manual": RoleConfig(
        name="tester-manual",
        prompt_namespace="tester-manual",
        primary_artifact_kinds=("jira_issue",),
        target_modules={
            "bug-report-quality": "Bug Report Quality",
            "regression-strategy": "Regression Strategy",
            "test-case-design": "Test Case Design",
        },
        module_hints={
            "bug-report-quality": "Luôn nạp khi viết, refine, hoặc review bug report và defect ticket.",
            "regression-strategy": "Task chạm regression checklist, retest scope, release smoke, hoặc risk-based coverage.",
            "test-case-design": "Task chạm test case, scenario, edge case, boundary, hoặc mapping AC sang hành vi cần verify.",
        },
        manifest_intro=(
            "Bạn đang pair với một manual tester. Ưu tiên các hard rules dưới đây,",
            "sau đó nạp module phù hợp với ngữ cảnh bug report, regression, hoặc test case design.",
        ),
        writing_preferences={
            "primary_language": "vi",
            "style": "Vietnamese-first",
            "preserve_identifiers": True,
            "avoid_app_specific_overfit": True,
            "output_mode": "checklist-and-observable-behavior-first",
        },
        cluster_keywords={
            "bug-report-quality": (
                "bug report",
                "defect",
                "steps to reproduce",
                "actual result",
                "expected result",
                "environment",
            ),
            "regression-strategy": (
                "regression",
                "smoke",
                "release",
                "risk",
                "coverage",
                "impact",
            ),
            "test-case-design": (
                "test case",
                "scenario",
                "edge case",
                "boundary",
                "checklist",
                "acceptance criteria",
                "given",
                "when",
                "then",
            ),
        },
    ),
}

SUPPORTED_ROLES = tuple(ROLE_CONFIGS)


def get_role_config(role: str) -> RoleConfig:
    try:
        return ROLE_CONFIGS[role]
    except KeyError as exc:  # pragma: no cover - defensive guard
        raise ValueError(f"Unsupported role: {role!r}") from exc


def normalize_cluster_name(role: str, name: str, description: str = "") -> str | None:
    config = get_role_config(role)
    lowered = f"{name} {description}".lower()
    direct = _slugify(name)
    if direct in config.target_modules:
        return direct
    for module_slug, keywords in config.cluster_keywords.items():
        if any(keyword in lowered for keyword in keywords):
            return module_slug
    return None
