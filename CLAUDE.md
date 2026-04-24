# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Setup

```bash
cp .env.example .env   # fill in GitLab, Jira, Confluence, and OpenAI/GPT tokens
make setup             # creates .venv, installs deps + dev deps, inits SQLite schema
```

Required env vars: `GITLAB_URL`, `GITLAB_TOKEN`, `GITLAB_PROJECT_ID`, `JIRA_URL`, `JIRA_PERSONAL_TOKEN`, `JIRA_USER_NAME`, `JIRA_PROJECT_KEY`, `CONFLUENCE_URL`, `CONFLUENCE_PERSONAL_TOKEN`, `CONFLUENCE_USER_NAME`, `CONFLUENCE_SPACE`, `GPT_API_KEY`, `GPT_MODEL`.

Optional LLM provider override: `LLM_PROVIDER=openai` (default) | `anthropic` (stub — must be implemented in `src/distill_core/llm.py:_complete_anthropic` before use; also requires `ANTHROPIC_API_KEY` and optionally `ANTHROPIC_MODEL`).

## Pipeline Commands

```bash
make all ROLE=mobile-dev WINDOW=90    # full pipeline end-to-end

# Step by step (preferred for debugging):
make ingest WINDOW=90                 # crawl GitLab MRs, Jira issues, Confluence pages
make link                             # cross-source key matching (MR ↔ Jira issue)
make score ROLE=mobile-dev           # composite quality score per artifact
make extract ROLE=mobile-dev         # LLM extracts patterns from top-scored artifacts
make cluster ROLE=mobile-dev         # INTERACTIVE — label each extraction with a cluster name
make synthesize ROLE=mobile-dev      # LLM generates skill modules → packs/<role>/v0.1/
make validate ROLE=mobile-dev        # citation check + context-window budget check

make trace MODULE=packs/mobile-dev/v0.1/skills/state-management.md  # provenance debug
make clean && make init-db           # reset all data and recreate schema
```

## Linting

```bash
.venv/bin/ruff check --fix src/
.venv/bin/ruff format src/
pre-commit run --all-files
```

Ruff is configured in `pyproject.toml` (line length 100, target Python 3.10).

## Tests

```bash
.venv/bin/pytest
```

No tests exist yet — `pytest` is in dev dependencies only.

## Architecture

Distill is a **one-shot pipeline** (not a service) that produces a role-scoped **skill pack** from real engineering artifacts.

### Three Layers

```
Capture  →  Evolve (Summarize → Aggregate → Execute)  →  Distribute
```

- **Capture**: Ingests GitLab MRs, Jira issues, Confluence pages into SQLite (`data/distill.db`) + raw blobs under `data/blobs/`.
- **Evolve**: `ingest → link → score → extract → cluster → synthesize` — filters by quality signal (merged MR = positive, reverted commit = negative), clusters patterns across high-performing users, materializes them into skill modules.
- **Distribute**: Output in `packs/<role>/v0.1/` — `manifest.md` (always injected) + `skills/*.md` (loaded on trigger match) + `pack.yaml`.

### Key Directories

| Path | Purpose |
|---|---|
| `src/distill_core/` | Shared primitives: `config`, `db`, `llm` (OpenAI), `schemas`, `cli` |
| `src/distill_capture/` | `redact`, `ingest_gitlab`, `ingest_jira`, `ingest_confluence`, `link` |
| `src/distill_evolve/` | `score`, `extract`, `cluster`, `synthesize`, `validate`, `trace` |
| `src/distill_distribute/` | `build_prompt`, `pack` (loader); `mcp_server` planned |
| `prompts/` | LLM prompt templates (`extract.system.md`, `synthesize.system.md`, etc.) |
| `packs/<role>/v0.1/` | Generated skill pack output |
| `data/distill.db` | SQLite — 6 tables: `artifacts, links, jira_events, scores, extractions, clusters` |
| `validation/` | Reviewer ratings and blind-test logs |

**Layer boundary**: `distill_capture` / `distill_evolve` / `distill_distribute` import from `distill_core` only — no cross-imports between the three outer layers. Each pipeline step is exposed as a `distill-*` console script (see `[project.scripts]` in `pyproject.toml`); the Makefile is a thin wrapper.

### SQLite Schema

`artifacts` → `links` (MR ↔ Jira cross-reference) → `scores` (quality per role) → `extractions` (LLM output) → `clusters` (named groups) → synthesized into skill modules.

### Skill Pack Format

Each role pack has: `manifest.md` (trigger table + module index, always in system prompt), `skills/*.md` (one file per pattern cluster, loaded on trigger), `references/` (long-tail patterns for retrieval), `pack.yaml` (metadata + checksums).

The cluster step is the only **interactive** step — the operator manually assigns a cluster name to each LLM extraction before synthesis.

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **Distill Skill** (1798 symbols, 2971 relationships, 83 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> If any GitNexus tool warns the index is stale, run `npx gitnexus analyze` in terminal first.

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `gitnexus_impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `gitnexus_detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `gitnexus_query({query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `gitnexus_context({name: "symbolName"})`.

## Never Do

- NEVER edit a function, class, or method without first running `gitnexus_impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `gitnexus_rename` which understands the call graph.
- NEVER commit changes without running `gitnexus_detect_changes()` to check affected scope.

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/Distill Skill/context` | Codebase overview, check index freshness |
| `gitnexus://repo/Distill Skill/clusters` | All functional areas |
| `gitnexus://repo/Distill Skill/processes` | All execution flows |
| `gitnexus://repo/Distill Skill/process/{name}` | Step-by-step execution trace |

## CLI

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->
