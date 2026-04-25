<claude-mem-context>
# Memory Context

# [Distill Skill] recent context, 2026-04-25 10:04am GMT+7

Legend: 🎯session 🔴bugfix 🟣feature 🔄refactor ✅change 🔵discovery ⚖️decision 🚨security_alert 🔐security_note
Format: ID TIME TYPE TITLE
Fetch details: get_observations([IDs]) | Search: mem-search skill

Stats: 25 obs (12,514t read) | 323,878t work | 96% savings

### Apr 24, 2026
45 9:58a 🔵 Distill Project: Full Codebase Architecture and MVP Pipeline Scope Discovered
S4 Distill Project: Full Codebase Architecture and MVP Pipeline Scope Discovered (Apr 24 at 9:58 AM)
S5 MVP Architecture Decision: How Many Service Layers for Debt-Payoff-Manager? (Apr 24 at 10:00 AM)
46 10:45a 🔵 Distill Skill MVP POC Architecture and Current State
47 10:46a 🔵 Distill MVP Actual Implementation Status: Only Foundation Layer Done, All Pipeline Steps Are Stubs
48 " 🔵 Distill MVP Success Criteria and 10-Day Execution Plan
49 10:47a 🔵 Distill MVP Environment Health: CI Green, DB Empty, Two Helper Modules Implemented, scripts/init_db.py Missing
50 10:48a 🔵 Distill MVP GETTING_STARTED.md: Full Pipeline Architecture and Definition of Done
51 10:50a 🔵 Distill Skill MVP: Only Phase A Complete — All Pipeline Scripts Are Stubs
52 10:52a 🔵 Distill Skill Pack Output Spec: Concrete Target Shape for Both Backend Dev and BA Roles
53 " 🔵 Distill MVP Architecture: Python + SQLite + Makefile — Deliberately Minimal Stack
54 " 🔵 Open Questions P0 Blockers: 5 Questions Must Be Answered Before Phase 1 Ships
55 " 🔵 score.py and extract.py Implementation Spec: Composite Scoring Formula and LLM Extraction Pattern
56 2:52p ⚖️ Artifact Representation Strategy: raw JSON → canonical card → LLM
57 " ⚖️ Optimization Pass Scope: Extract-first + Full Data Reset
58 2:58p 🔵 Distill Skill: Data Directory Already Clean, Pack Output Exists for mobile-dev Role
59 2:59p ✅ Distill Skill: Full Clean + DB Reset Executed Before Pipeline Re-run
60 3:00p 🔵 Distill Skill: `pgrep` Process Listing Blocked by Sandbox — Cannot Monitor Ingest PID
61 3:01p 🔵 Distill Skill: Ingest Process Running 2+ Minutes with Zero Output or Blob Files Written
62 3:02p 🔵 Distill Skill: Ingest Process Hung for 3+ Minutes with No Output — Killed via pkill
63 3:05p ✅ Distill Skill: Full Ingest Completed — 120 GitLab MRs, 200 Jira Issues, 80 Confluence Pages
64 " ✅ Distill Skill: Link and Score Pipeline Stages Completed for mobile-dev Role
65 " 🔵 Distill Skill: Extract Stage Running Against 112 Scored Artifacts — Zero Extractions Written Yet
66 3:06p 🔵 Distill Skill: Extract Stage Silent for 90+ Seconds — No Failures File, No DB Writes, LLM Calls In-Flight
67 10:05p 🔵 Distill apps/web Dashboard: Full UI Shell, Mock-Only Data, 3 Routes Implemented
68 " 🔵 apps/web Build Health: Lint + TypeScript + Vite Build All Pass Clean
69 10:57p ⚖️ Distill Skill Web: Plan to Replace Mock Data with Real Backend Integration

Access 324k tokens of past work via get_observations([IDs]) or mem-search skill.
</claude-mem-context>

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **Distill Skill** (1433 symbols, 2859 relationships, 111 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> If any GitNexus tool warns the index is stale, run `npx gitnexus analyze` in terminal first.

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `gitnexus_impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `gitnexus_detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `gitnexus_query({query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `gitnexus_context({name: "symbolName"})`.

## When Debugging

1. `gitnexus_query({query: "<error or symptom>"})` — find execution flows related to the issue
2. `gitnexus_context({name: "<suspect function>"})` — see all callers, callees, and process participation
3. `READ gitnexus://repo/Distill Skill/process/{processName}` — trace the full execution flow step by step
4. For regressions: `gitnexus_detect_changes({scope: "compare", base_ref: "main"})` — see what your branch changed

## When Refactoring

- **Renaming**: MUST use `gitnexus_rename({symbol_name: "old", new_name: "new", dry_run: true})` first. Review the preview — graph edits are safe, text_search edits need manual review. Then run with `dry_run: false`.
- **Extracting/Splitting**: MUST run `gitnexus_context({name: "target"})` to see all incoming/outgoing refs, then `gitnexus_impact({target: "target", direction: "upstream"})` to find all external callers before moving code.
- After any refactor: run `gitnexus_detect_changes({scope: "all"})` to verify only expected files changed.

## Never Do

- NEVER edit a function, class, or method without first running `gitnexus_impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `gitnexus_rename` which understands the call graph.
- NEVER commit changes without running `gitnexus_detect_changes()` to check affected scope.

## Tools Quick Reference

| Tool | When to use | Command |
|------|-------------|---------|
| `query` | Find code by concept | `gitnexus_query({query: "auth validation"})` |
| `context` | 360-degree view of one symbol | `gitnexus_context({name: "validateUser"})` |
| `impact` | Blast radius before editing | `gitnexus_impact({target: "X", direction: "upstream"})` |
| `detect_changes` | Pre-commit scope check | `gitnexus_detect_changes({scope: "staged"})` |
| `rename` | Safe multi-file rename | `gitnexus_rename({symbol_name: "old", new_name: "new", dry_run: true})` |
| `cypher` | Custom graph queries | `gitnexus_cypher({query: "MATCH ..."})` |

## Impact Risk Levels

| Depth | Meaning | Action |
|-------|---------|--------|
| d=1 | WILL BREAK — direct callers/importers | MUST update these |
| d=2 | LIKELY AFFECTED — indirect deps | Should test |
| d=3 | MAY NEED TESTING — transitive | Test if critical path |

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/Distill Skill/context` | Codebase overview, check index freshness |
| `gitnexus://repo/Distill Skill/clusters` | All functional areas |
| `gitnexus://repo/Distill Skill/processes` | All execution flows |
| `gitnexus://repo/Distill Skill/process/{name}` | Step-by-step execution trace |

## Self-Check Before Finishing

Before completing any code modification task, verify:
1. `gitnexus_impact` was run for all modified symbols
2. No HIGH/CRITICAL risk warnings were ignored
3. `gitnexus_detect_changes()` confirms changes match expected scope
4. All d=1 (WILL BREAK) dependents were updated

## Keeping the Index Fresh

After committing code changes, the GitNexus index becomes stale. Re-run analyze to update it:

```bash
npx gitnexus analyze
```

If the index previously included embeddings, preserve them by adding `--embeddings`:

```bash
npx gitnexus analyze --embeddings
```

To check whether embeddings exist, inspect `.gitnexus/meta.json` — the `stats.embeddings` field shows the count (0 means no embeddings). **Running analyze without `--embeddings` will delete any previously generated embeddings.**

> Claude Code users: A PostToolUse hook handles this automatically after `git commit` and `git merge`.

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
