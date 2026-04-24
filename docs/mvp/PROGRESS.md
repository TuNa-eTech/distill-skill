# MVP Progress — `mobile-dev`

## Current Status

| Item | Value |
|---|---|
| Current status | MVP baseline is now operational and temporarily accepted as-is. The 2026-YTD pipeline has run against live sources, `mobile-dev` has a tightened Vietnamese-ready pack under `packs/mobile-dev/v0.1/`, `tester-manual` has a fresh live Jira-based pack under `packs/tester-manual/v0.1/`, and role-scoped extractions now prevent cross-role contamination during clustering/synthesis. |
| Current active phase | `G — Validation harness / MVP closeout` |
| Current blockers | No MVP blocker is open. Deferred post-MVP optimization backlog: MR↔Jira link coverage, stronger live BA pack quality, genericity cleanup for `tester-manual` modules, and a fuller manual clustering pass. |
| Last updated | `2026-04-24` |
| Pilot defaults | role=`mobile-dev`, stack=`Flutter`, LLM=`OpenAI-first`, local ingest scope=`2026-01-01..today`, MVP=`full pipeline` |

## Progress Checklist

### MVP Baseline

- [x] Foundation baseline ổn định: CLI, DB, shared helpers, role-aware prompt loading, compile smoke, `distill-init-db`
- [x] Ingest 2026-YTD hoàn tất trên live source với local caps: `gitlab_mr=120`, `jira_issue=200`, `confluence_page=80`
- [x] Linking + scoring có dữ liệu usable cho `mobile-dev`
- [x] Distill pipeline cho `mobile-dev` đã chạy hết: extract, cluster, synthesize
- [x] Pack thật đã tồn tại dưới `packs/mobile-dev/v0.1/`
- [x] `distill-build-prompt --role mobile-dev` compose được prompt từ pack thật
- [x] `distill-validate --role mobile-dev` pass trên live pack
- [x] Multi-role prompt/runtime path đã có cho `business-analyst` và `tester-manual`
- [x] `tester-manual` live pack đã được regenerate sạch sau khi fix role-scoped extractions

### Post-MVP Optimization Backlog

- [ ] Tăng coverage MR↔Jira link để score enrichment mạnh hơn
- [ ] Generate BA live pack mạnh hơn từ Jira/Confluence data thật
- [ ] Làm `tester-manual` modules generic hơn, bớt domain-specific
- [ ] Làm manual clustering pass sâu hơn thay cho heuristic-assisted clustering
- [ ] Fill V1/V2/V3 validation evidence templates bằng review/use-case thật

## Phase Overview

| Phase | Goal | Status | Exit gate | Evidence | Next action |
|---|---|---|---|---|---|
| A — Foundation | Working CLI, DB, shared helpers, and reproducible local setup | `done` | `make setup` + `distill-init-db` baseline work on a clean checkout | Console entrypoints exist in `pyproject.toml`; shared core helpers now cover default ingest dates, blob I/O, role-aware prompt loading/rendering, and role registry dispatch; `.venv/bin/python -m compileall -q src tests` and `.venv/bin/distill-init-db` pass locally | Keep stable; reopen only if setup breaks |
| B — Ingestion | Persist 2026-local GitLab, Jira, and Confluence artifacts with redacted blobs | `done` | Each ingestor writes artifacts + blobs for the local 2026 scope | Live run completed with `gitlab_mr=120`, `jira_issue=200`, `confluence_page=80`; GitLab now supports group-wide multi-repo ingest under `mobile-team` | Tune local caps only if future reruns get too slow |
| C — Linking + Scoring | Populate deterministic links and `mobile-dev` scores | `done` | `links` and `scores` have usable data for `mobile-dev` | Live run produced `9` Jira-reference links and `120` scored MR artifacts for `mobile-dev` | Freeze for MVP; improve MR↔Jira linking after MVP if real usage shows the need |
| D — Distill pipeline | Produce extractions, manual clusters, and synthesized module drafts | `done` | Draft clusters and module content exist for Flutter/mobile patterns | Live run inserted `30` extractions and assigned them into `4` clusters (`state management`, `navigation`, `platform integration`, `code review conventions`) via heuristic-assisted clustering | Freeze for MVP; revisit deeper manual clustering after MVP |
| E — Pack assembly | Freeze `packs/mobile-dev/v0.1/` with manifest, skills, and `pack.yaml` | `done` | Pack tree exists with 3–5 modules and provenance metadata | Live pack now exists in `packs/mobile-dev/v0.1/` with `manifest.md`, `pack.yaml`, `4` curated skill modules, corrected contributor metadata, and Vietnamese-first guidance text | Keep as MVP baseline and collect human feedback before further tuning |
| F — Distribution helpers | Compose a usable AI prompt from the generated pack | `done` | `distill-build-prompt --role mobile-dev --task "..."` works against a real pack | Prompt build smoke succeeded against the live pack and produced a ~12 KB prompt for a Flutter task | Keep stable through MVP; optimize prompt usefulness later |
| G — Validation harness | Prepare evidence templates and final validation flow | `done` | Validation templates exist and `distill-validate` passes on a real pack | `distill-validate --role mobile-dev` now passes on the live pack (`4 modules`, `~3622 tokens`); validator also enforces `>=2` distinct source IDs per rule bullet and validates `manifest.md` itself | Use the current baseline for V1/V2/V3 evidence capture; defer deeper quality tuning until after MVP |

## Phase Detail

### A — Foundation

- Goal: keep setup, packaging, and core helpers stable enough for all later phases.
- In scope: editable install, `distill-init-db`, shared config/blob/prompt helpers, CI baseline.
- Done when: a clean checkout can install, initialize SQLite, and load the shared helper layer.
- Status: `done`
- Evidence: console scripts are defined, core default ingest helpers exist, `.venv/bin/python -m compileall -q src tests` passes, `.venv/bin/distill-init-db` passes, and CI no longer points at a missing `scripts/` directory.
- Evidence: role-scoped prompt namespaces now exist under `prompts/mobile-dev/`, `prompts/business-analyst/`, `prompts/tester-manual/`, and `prompts/shared/`; prompt loading falls back from role-specific files to shared templates.
- Open risks: capture/evolve slices can still drift if their CLI contracts change without updating ops.
- Blockers: none.
- Next action: keep the contract stable while live ingestion is shaken out.

### B — Ingestion

- Goal: ingest just enough 2026-local data to power the MVP on one laptop.
- In scope: GitLab MRs, Jira issues/events, Confluence pages, redacted blob persistence, local caps/date bounds.
- Done when: the three ingestors write artifacts + blobs for `2026-01-01..today` and reruns are idempotent.
- Status: `done`
- Evidence: the live 2026-YTD ingest completed with `120` GitLab MRs, `200` Jira issues, and `80` Confluence pages persisted into `data/distill.db`.
- Open risks: reruns against the `mobile-team` GitLab group can take time because each MR still fetches discussions, commits, and changes.
- Blockers: none.
- Next action: keep caps practical for local reruns.

### C — Linking + Scoring

- Goal: turn ingested artifacts into a ranked `mobile-dev` candidate set.
- In scope: deterministic Jira/Confluence links, `mobile-dev` composite score, threshold selection.
- Done when: `links` and `scores` contain enough data to select 30–60 extraction candidates.
- Status: `done`
- Evidence: the live run produced `9` `references_jira` links and `120` scored MR artifacts; top score reached `4.50` with `112` positive-score artifacts.
- Open risks: current link coverage is still sparse relative to total MR volume.
- Blockers: none.
- Next action: accept the current linking baseline for MVP and track enrichment improvements after MVP.

### D — Distill Pipeline

- Goal: convert top-ranked work into clusters and module-ready patterns.
- In scope: extraction, manual clustering, synthesis.
- Done when: there are clusterable Flutter/mobile extractions and draft module content.
- Status: `done`
- Evidence: the live run inserted `30` extractions with `0` failures, then grouped them into `4` clusters by heuristic-assisted assignment.
- Open risks: clustering was assisted by heuristics rather than a human pass through the interactive CLI.
- Blockers: none.
- Next action: keep the current clusters as MVP baseline and only reopen if real use shows obvious drift.

### E — Pack Assembly

- Goal: freeze one reproducible pack tree for `mobile-dev`.
- In scope: `manifest.md`, `skills/*.md`, `pack.yaml`.
- Done when: `packs/mobile-dev/v0.1/` exists and contains 3–5 usable modules plus provenance metadata.
- Status: `done`
- Evidence: the live pack now exists with `4` curated modules: `code-review-conventions.md`, `navigation.md`, `platform-integration.md`, and `state-management.md`, plus a corrected `pack.yaml` (`contributors=19`, updated checksum, `language=vi`).
- Open risks: future reruns still depend on extraction/link quality; content quality is better, but it is not yet human-reviewed.
- Blockers: none.
- Next action: use the current pack in one real Flutter task and treat deeper content cleanup as post-MVP work.

### F — Distribution Helpers

- Goal: make the generated pack usable inside a single AI prompt.
- In scope: `distill-build-prompt`, deterministic module ordering, clear missing-pack errors.
- Done when: prompt composition works against a real generated pack and can be used in local AI sessions.
- Status: `done`
- Evidence: prompt composition succeeded against the live pack for `implement payment schedule edit flow in Flutter`, generating a prompt of roughly `12 KB`.
- Open risks: prompt usefulness still needs review in a real coding workflow.
- Open risks: the BA prompt path still lacks a stronger live pack; the tester-manual path now has a live clean pack, but its usefulness should be checked in a real QA workflow before broader use.
- Blockers: none at code level.
- Next action: freeze the helper path for MVP and capture one real prompt example before any further optimization.

### G — Validation Harness

- Goal: make MVP evidence collection operational, not ad hoc.
- In scope: validation templates, implementation report skeleton, later validator pass/fail evidence.
- Done when: validation files are ready and real validation output can be recorded in one place.
- Status: `done`
- Evidence: the live pack passes `distill-validate --role mobile-dev` with `4` modules and an estimated `~3622` tokens total; manifest hard rules are now validated with the same citation standard as skill modules.
- Evidence: the live clean `tester-manual` pack also passes `distill-validate --role tester-manual` with `3` modules and an estimated `~3578` tokens total after removing cross-role contamination from extractions.
- Open risks: V1/V2/V3 evidence templates are still empty, and the validator only proves format/provenance quality, not end-user usefulness.
- Blockers: none at code level.
- Next action: treat the harness as MVP-complete, then use the templates in the first real review cycle before post-MVP optimization.
