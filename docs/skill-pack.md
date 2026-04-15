# Skill Pack — Design Notes

> How Distill packages and delivers distilled knowledge without blowing up the AI context window.

---

## Why not a single `SKILL.md`?

The original sketch said "one `SKILL.md` per role, injected into every session." That works for a seed phase with a few hundred lines of hand-written content. It does **not** work once the evolve pipeline starts synthesizing real patterns across dozens of engineers:

| Problem | What happens at scale |
|---|---|
| **Context bloat** | Every session pays token cost for the whole file, even when the task only touches 5% of it. |
| **Signal dilution** | Irrelevant patterns crowd out relevant ones; the model gets noisier advice, not better advice. |
| **Cache invalidation** | One edit busts the entire prompt cache — and the evolve pipeline edits constantly. |
| **Role misfit** | A senior backend dev does not need the junior frontend patterns, but a flat file cannot distinguish. |
| **No observability** | You cannot tell which part of the skill actually fired on a given task. |

The fix: treat the skill as a **pack** — a small, stable manifest plus a library of modular skill files, loaded progressively.

---

## Anatomy of a Skill Pack

```
senior-backend-dev/
├── manifest.md              # the only file always injected
├── skills/
│   ├── api-design.md
│   ├── db-migration.md
│   ├── testing.md
│   ├── code-review.md
│   ├── observability.md
│   └── prompting-patterns.md
├── references/              # long-tail, retrieved via embedding search
│   ├── legacy-auth-notes.md
│   ├── vendor-sdk-quirks.md
│   └── ...
└── pack.yaml                # version, role, checksum, provenance
```

### `manifest.md` — the always-on index

The manifest is the only thing injected unconditionally into every AI session. It is deliberately small (target: **under 1,500 tokens**) and deliberately stable (changes rarely, so prompt cache stays warm).

It contains:

- The role name and a one-paragraph description
- A **trigger table** — for each skill module, a short description and the task signals that should load it
- A list of hard rules that always apply (team conventions, non-negotiable constraints)
- A pointer to the retrieval index for long-tail references

Example shape:

```markdown
# Senior Backend Dev — Skill Pack Manifest

You are pairing with a senior backend engineer on the Acme payments team.
Always follow the hard rules below. Load the listed skill modules when
their triggers match the current task.

## Hard rules (always apply)
- Never run DB migrations without a rollback plan
- All new endpoints require a Pact contract test
- ...

## Skill modules

| Module | Load when | Description |
|---|---|---|
| skills/api-design.md | Task touches routes, handlers, OpenAPI | REST patterns, error envelopes, versioning |
| skills/db-migration.md | Task edits migrations/ or schema.sql | Migration safety, backfill strategy |
| skills/testing.md | Task edits *_test.go or adds a fixture | Test layering, fixture conventions |
| ...
```

### `skills/*.md` — the modules

Each module is a focused, self-contained chunk of distilled knowledge — typically 500–3,000 tokens. A module is big enough to be useful on its own but small enough that loading three or four still fits comfortably in context.

A module contains:

- **When to apply** — the trigger conditions restated from the manifest
- **Core patterns** — the actual distilled patterns, each with a short rationale
- **Pitfalls** — what goes wrong when you skip the pattern
- **Examples** — one or two concrete examples (redacted, pattern-level)
- **Provenance** — aggregation metadata: how many merged PRs contributed, which date range

### `references/` — the long tail

Anything too rare to justify a dedicated module goes here. These files are embedded and retrieved via similarity search, not loaded by trigger. A task that happens to touch vendor SDK quirks will pull in the right reference chunk; a task that does not will never see it.

### `pack.yaml` — provenance and versioning

```yaml
role: senior-backend-dev
version: 2026.04.2
generated_at: 2026-04-15T08:22:00Z
source_window: 2026-03-01..2026-04-14
contributors: 11
quality_signals:
  merged_prs: 247
  passed_reviews: 418
  rejected_samples_filtered: 63
checksum: sha256:9a3b...
```

Every field is auditable. Every skill change can be traced back to the set of merged PRs it was aggregated from.

---

## Progressive disclosure at inject time

The distribute layer runs a small **injector** on the client side (an IDE hook or API proxy middleware). Its job is:

1. Always inject `manifest.md` into the system prompt. (Stable, cache-friendly.)
2. Observe the incoming task signals — the user prompt, the files currently open, the tool calls so far.
3. Match those signals against the manifest's trigger table.
4. For each matching row, inject the corresponding `skills/*.md` module.
5. If the task still looks unusual, run a similarity search against `references/` and inject the top-k chunks.

The injector is stateless between sessions and has no model calls of its own — matching is regex-and-embedding, not LLM-based. This keeps it fast, cheap, and debuggable.

### Task signals the injector uses

- **Prompt keywords** — cheap first-pass filter against the manifest's trigger strings
- **File path patterns** — `migrations/**`, `**/*_test.go`, `openapi.yaml`, etc.
- **Tool use patterns** — did the session call a database tool? A browser tool? A git tool?
- **User role** — which skill pack to use in the first place

### Prompt cache strategy

- The manifest is the **stable prefix** — cached aggressively, rarely invalidated.
- Modules are **insertable segments** — each keyed by content hash, so cache hits across sessions when the same module loads.
- The user's task message is the **tail** — never cached.

A well-designed pack should hit >80% cache reuse on the stable prefix across sessions for the same role.

---

## How the Evolve pipeline produces a pack

The evolve pipeline doesn't need to change much — it already aggregates patterns. What changes is the **Execute** step:

1. After aggregation, patterns are clustered by topic (api, db, testing, etc.). Clustering can be embedding-based or rule-based on source file paths.
2. Each cluster becomes (or updates) one module file.
3. The manifest is regenerated from the cluster index.
4. Any pattern that doesn't fit a cluster — or is used too rarely — is written to `references/` instead.
5. The pack is versioned, checksummed, and published.

Clustering naturally produces the modular structure the injector needs. No extra authoring step.

---

## Open questions

These are unresolved and worth discussing before Phase 2:

- **Trigger granularity.** Manifest-level triggers are fast but coarse. Should individual modules declare sub-triggers for partial loading (load only the "error handling" section of `api-design.md`)?
- **Conflict resolution.** What if two modules give contradictory advice? Is the pack allowed to contain contradictions, or must the aggregate step resolve them?
- **Personalization vs. role-scope.** The design is strictly role-scoped to avoid privacy issues. But individuals clearly diverge within a role. Is there a sanctioned way to layer personal overrides on top of the pack without leaking individual data back into the collective?
- **Pack size budget.** How big is too big? A soft cap (e.g., manifest ≤ 1.5k tokens, any single module ≤ 3k, total pack ≤ 50k) would force discipline.
- **Update cadence.** Daily? Weekly? On-demand? Too-frequent updates break cache; too-rare updates lose freshness.

---

## Non-goals

Things the skill pack deliberately does **not** try to do:

- **Replace documentation.** The pack captures *practiced* patterns, not canonical reference material. Docs still belong in Confluence/Notion.
- **Run as a RAG system for everything.** Only the long-tail `references/` folder uses retrieval. The core patterns are deterministic injection.
- **Be human-authored.** Phase 1 seeds the pack by hand, but the long-term design assumes generation. Hand-editing a generated pack is a bad smell — fix the aggregator instead.
- **Be a prompt library.** Prompts change per task; patterns are more durable. The pack optimizes for durability.
