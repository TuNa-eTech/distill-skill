# Architecture

> How the three layers of Distill fit together, what flows between them, and what's still open.

---

## The three layers

Distill is built as three decoupled layers. Each runs independently, scales independently, and can be swapped out without touching the others.

```
┌──────────────────────────────────────────────────────────────┐
│                      CAPTURE LAYER                           │
│   IDE hooks · API proxy · Git/PR crawler · Doc connectors    │
└──────────────────────────┬───────────────────────────────────┘
                           │  raw events
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                    SHARED EVENT STORE                        │
│         append-only · partitioned by role · redacted         │
└──────────────────────────┬───────────────────────────────────┘
                           │  quality-scored sessions
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                      EVOLVE LAYER                            │
│         Summarize → Aggregate → Execute  (scheduled)         │
└──────────────────────────┬───────────────────────────────────┘
                           │  versioned skill packs
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                   DISTRIBUTE LAYER                           │
│    Pack registry · client injector · progressive disclosure  │
└──────────────────────────┬───────────────────────────────────┘
                           │  injected context
                           ▼
                     every AI session
```

---

## Layer 1 — Capture

The capture layer's only job is to observe AI interactions and engineering activity without changing anyone's workflow.

### Sources

| Source | What it captures | How |
|---|---|---|
| **IDE hooks** | Prompts, tool calls, model outputs, accept/reject events | Claude Code hooks, Cursor/Windsurf extensions |
| **API proxy** | Raw request/response pairs for teams using Anthropic/OpenAI direct | Drop-in reverse proxy with the same API surface |
| **Git/PR crawler** | Commits, PR metadata, review threads, merge status | Webhook or polling against GitHub/GitLab |
| **Doc connectors** | Internal knowledge that contextualizes patterns | Read-only Notion/Confluence/email integrations |

### Event schema

Every captured event is normalized into the same shape before it hits the store:

```
event {
  id
  session_id
  user_role         # not user_id — see privacy below
  source            # ide | proxy | git | doc
  kind              # prompt | tool_call | output | pr_merged | ...
  timestamp
  payload_redacted  # content with PII/secrets stripped
  quality_hints     # early signals: test_passed, review_passed, ...
}
```

Events are role-scoped from the start. The capture layer never writes a `user_id` into the shared store — that mapping lives in a separate, access-controlled table used only for quality correlation.

### Redaction

Redaction happens **at the edge**, before events leave the developer's machine. The capture layer runs a pluggable redaction pipeline (regex + entity detection + domain-specific rules for things like customer IDs) and drops anything that fails the check. An event that cannot be redacted safely is not captured at all.

This is non-negotiable for on-premise deployment.

---

## Layer 2 — Evolve

The evolve layer turns raw events into skill packs. It runs on a schedule (initially nightly), not in real time — freshness matters less than quality.

### Step 1 — Summarize

Each session becomes a structured summary:

- What task was the user trying to accomplish?
- What patterns of prompting, tool use, and iteration did they employ?
- What was the final outcome, and what quality signals attach to it?

Summarization is LLM-driven but bounded. Only the summary (not the raw session) feeds the next stage, which keeps cost linear in session count and sidesteps a lot of the privacy surface.

### Step 2 — Aggregate

This is where the collective learning happens. For each role:

1. Cluster summaries by task type and pattern.
2. Filter out clusters where the quality signal is weak (rejected PRs, reverted commits, abandoned sessions).
3. Identify patterns that appear across **multiple high-performing users** — the "wisdom of the best" signal. A pattern used by one person once is noise; a pattern used by five people across 30 merged PRs is signal.
4. Rank patterns by frequency × quality × recency.

The output is a ranked pattern set per role, with full provenance back to the contributing events.

### Step 3 — Execute

The execute step materializes the ranked patterns into a skill pack (see [`skill-pack.md`](skill-pack.md)). Key operations:

1. **Cluster → module**: each pattern cluster becomes or updates a `skills/*.md` module.
2. **Long-tail → reference**: rare or idiosyncratic patterns go to `references/` for retrieval.
3. **Manifest regeneration**: the trigger table and hard rules are regenerated from the updated cluster index.
4. **Diff + review**: changes from the previous pack version are diffed; large changes optionally go through human review before publishing.
5. **Publish**: the new pack is versioned, checksummed, and pushed to the registry.

### Quality signals

The aggregator is only as good as its quality signals. Initial signal set:

- **PR merged** — strongest positive signal
- **Review approved with no change requests** — moderate positive
- **Tests added and passed** — moderate positive
- **PR rejected or closed without merge** — negative
- **Commit reverted within N days** — strong negative
- **Session abandoned (no output accepted)** — mild negative

Signals combine into a session score; only sessions above a threshold feed aggregation.

---

## Layer 3 — Distribute

The distribute layer gets packs to every AI session with minimal overhead.

### Pack registry

A simple artifact store — think "package registry, but for skill packs." Each role has a channel (stable, canary); each pack is immutable and content-addressed. Rollback is a pointer swap.

### Client injector

The injector is what actually reads a pack and shapes the context. It lives wherever AI is called — IDE extension, API proxy, CLI wrapper. Its responsibilities:

1. Fetch the current pack for the user's role from the registry (cached locally, revalidated periodically).
2. Inject the manifest into every system prompt.
3. Inspect task signals (prompt, open files, tool use) and load matching modules.
4. Run retrieval over `references/` for long-tail matches.
5. Log which modules fired, for observability back into the evolve layer.

The injector never calls an LLM itself. All matching is regex, glob, and embedding similarity — fast, cheap, deterministic, debuggable.

### Feedback loop

The injector emits its own events back into the capture layer: which modules loaded, whether the session ended in a quality signal, whether the user overrode the injected context. This closes the loop — the evolve pipeline can learn **which skills actually help** and deprioritize modules that load often but correlate with poor outcomes.

---

## Data flow, end to end

```
1. Dev writes code with Claude Code
     → IDE hook captures prompt, tool calls, output
     → redaction at edge, event written to store (role-scoped)

2. Dev opens PR, CI runs, reviewer approves, PR merges
     → Git crawler writes PR-merged event
     → store correlates with session via session_id

3. Nightly evolve job runs
     → summarize last 24h of sessions
     → filter to sessions with positive quality signals
     → aggregate patterns per role, cluster by topic
     → execute: regenerate skill packs, diff, publish new version

4. Next morning, another dev starts a task
     → injector fetches current pack for their role
     → manifest is already in the cached system prompt
     → dev's task hits trigger for db-migration.md → module loads
     → AI output reflects the team's distilled migration patterns
     → outcome feeds back into capture as new input

5. Repeat.
```

---

## Privacy and security posture

- **Role-scoped by default.** Aggregation happens at the role level. Individual user identities exist only in a separate correlation table used for quality scoring, never exposed in the skill pack.
- **Redaction at the edge.** Raw content with PII or secrets never leaves the developer's machine.
- **Content-addressed packs.** Every published pack is immutable and checksummed. Any tampering is detectable.
- **On-premise friendly.** All three layers can run inside a customer's network. No data ever needs to leave, and no external model calls are required if the customer self-hosts a model.
- **Audit trail.** Every skill change traces back to the set of events that produced it. Rollback is safe and observable.
- **Opt-out at the individual level.** A developer can flag their session as non-contributing with a single setting. The capture layer still runs for their own experience, but their events do not feed aggregation.

---

## Open questions

These are the design decisions we have **not** made yet. Phase 1 should help answer them:

1. **What is the minimum team size where aggregation starts producing signal?** A team of three is probably too small; a team of fifty clearly works. Where is the floor?
2. **Should the evolve pipeline run locally or centrally?** Central is simpler; local is more privacy-friendly. There may be a hybrid.
3. **How do we handle multi-role developers?** A fullstack dev matches multiple packs. Do they load both? Merge?
4. **What does the authoring story look like in Phase 1?** Hand-authored seed packs need an editor, a linter, and a way to convert "I know this pattern works" into structured content quickly.
5. **How do we measure success?** "Does the pack actually help?" is the real question. Leading candidates: onboarding time, PR cycle time, code review comments per PR, self-reported usefulness surveys.
6. **What's the failure mode when the pack is wrong?** An injected bad pattern could systematically steer the whole team toward a bad approach. We need guardrails, canaries, and fast rollback.

---

## Prior art and differences

See [`idea.md`](idea.md) for the three projects that influenced this design (claude-mem, SkillClaw, colleague-skill). The key difference: Distill combines their ideas into a **role-scoped, progressively-disclosed, quality-gated** pipeline. Each piece exists elsewhere; the integration is what's new.
