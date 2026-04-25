# MVP Progress — `mobile-dev`

## Current Status

| Item | Value |
|---|---|
| Current status | MVP implementation baseline is operational, the generated `mobile-dev/v0.1` pack validates, and the V1/V2/V3 validation packet is now prepared for evidence collection. The project-value decision is still pending real reviewer, judge, and self-use evidence. |
| Current active phase | `G — External validation evidence collection / MVP decision` |
| Current blockers | No code blocker is open. The Phase 2 decision is blocked on V1 expert review, V2 blind taste test scoring, and V3 self-use logs. Deferred post-MVP optimization backlog remains: MR↔Jira link coverage, stronger live BA pack quality, genericity cleanup for `tester-manual` modules, and a fuller manual clustering pass. |
| Last updated | `2026-04-25` |
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
- [x] Validation packet đã sẵn sàng: V1 rubric, V2 blind-test tasks/key, V3 self-use log, MVP report guardrail

### MVP Decision Evidence

- [ ] Thu V1 expert review score thật cho `mobile-dev/v0.1`
- [ ] Generate/chấm V2 blind taste test outputs cho 5 task `mobile-dev`
- [ ] Ghi đủ 5 V3 self-use logs từ task thật hoặc mô phỏng sát workflow thật
- [ ] Cập nhật `validation/mvp_report.md` với verdict `Go Phase 2 | Iterate MVP | Pivot | Stop`

### Post-MVP Optimization Backlog

- [ ] Tăng coverage MR↔Jira link để score enrichment mạnh hơn
- [ ] Generate BA live pack mạnh hơn từ Jira/Confluence data thật
- [ ] Làm `tester-manual` modules generic hơn, bớt domain-specific
- [ ] Làm manual clustering pass sâu hơn thay cho heuristic-assisted clustering

## Phase Overview

| Phase | Goal | Status | Exit gate | Evidence | Next action |
|---|---|---|---|---|---|
| A — Foundation | Working CLI, DB, shared helpers, and reproducible local setup | `done` | `make setup` + `distill-init-db` baseline work on a clean checkout | Console entrypoints exist in `pyproject.toml`; shared core helpers now cover default ingest dates, blob I/O, role-aware prompt loading/rendering, and role registry dispatch; `.venv/bin/python -m compileall -q src tests` and `.venv/bin/distill-init-db` pass locally | Keep stable; reopen only if setup breaks |
| B — Ingestion | Persist 2026-local GitLab, Jira, and Confluence artifacts with redacted blobs | `done` | Each ingestor writes artifacts + blobs for the local 2026 scope | Live run completed with `gitlab_mr=120`, `jira_issue=200`, `confluence_page=80`; GitLab now supports group-wide multi-repo ingest under `mobile-team` | Tune local caps only if future reruns get too slow |
| C — Linking + Scoring | Populate deterministic links and `mobile-dev` scores | `done` | `links` and `scores` have usable data for `mobile-dev` | Live run produced `9` Jira-reference links and `120` scored MR artifacts for `mobile-dev` | Freeze for MVP; improve MR↔Jira linking after MVP if real usage shows the need |
| D — Distill pipeline | Produce extractions, manual clusters, and synthesized module drafts | `done` | Draft clusters and module content exist for Flutter/mobile patterns | Live run inserted `30` extractions and assigned them into `4` clusters (`state management`, `navigation`, `platform integration`, `code review conventions`) via heuristic-assisted clustering | Freeze for MVP; revisit deeper manual clustering after MVP |
| E — Pack assembly | Freeze `packs/mobile-dev/v0.1/` with manifest, skills, and `pack.yaml` | `done` | Pack tree exists with 3–5 modules and provenance metadata | Live pack now exists in `packs/mobile-dev/v0.1/` with `manifest.md`, `pack.yaml`, `4` curated skill modules, corrected contributor metadata, and Vietnamese-first guidance text | Keep as MVP baseline and collect human feedback before further tuning |
| F — Distribution helpers | Compose a usable AI prompt from the generated pack | `done` | `distill-build-prompt --role mobile-dev --task "..."` works against a real pack | Prompt build smoke succeeded against the live pack and produced a ~12 KB prompt for a Flutter task | Keep stable through MVP; optimize prompt usefulness later |
| G — Validation harness | Prepare evidence packet and final decision flow | `in_progress` | V1/V2/V3 evidence is collected and `validation/mvp_report.md` records a decision | `distill-validate --role mobile-dev` passes on the live pack; `validation/expert_review_rubric.md`, `validation/blind_test_packet.md`, `validation/blind_test_key.md`, `validation/self_use_log.md`, and `validation/mvp_report.md` are prepared for evidence collection | Collect real V1/V2/V3 evidence before any Phase 2 claim |

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
- In scope: validation packet, implementation report skeleton, real V1/V2/V3 evidence, final decision report.
- Done when: V1/V2/V3 results are recorded and `validation/mvp_report.md` contains a decision.
- Status: `in_progress`
- Evidence: the live pack passes `distill-validate --role mobile-dev` with `4` modules and an estimated `~3969` tokens total; manifest hard rules are now validated with the same citation standard as skill modules.
- Evidence: the live clean `tester-manual` pack also passes `distill-validate --role tester-manual` with `3` modules and an estimated `~3578` tokens total after removing cross-role contamination from extractions.
- Evidence: V1/V2/V3 files are no longer blank templates; the packet now has reviewer instructions, five concrete blind-test tasks, an operator answer key, self-use task candidates, and a guarded MVP report.
- Open risks: external evidence is still pending, and the validator only proves format/provenance quality, not end-user usefulness.
- Blockers: none at code level; decision is blocked on evidence collection.
- Next action: collect V1/V2/V3 evidence, then update `validation/mvp_report.md` with the decision matrix result.
