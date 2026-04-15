# Distill

> Your team's best work, distilled into every AI session.

Distill is an **organizational brain** for engineering teams using AI coding assistants. It captures how your best engineers actually work with AI, synthesizes those patterns across the team, and injects the result into everyone's AI context — so every developer gets to work at the level of your most experienced ones.

---

## Table of Contents

- [The Problem](#the-problem)
- [How Distill Works](#how-distill-works)
- [Output: Role-Scoped Skill Pack](#output-role-scoped-skill-pack)
- [Why It Fits the Enterprise](#why-it-fits-the-enterprise)
- [Compared to Existing Tools](#compared-to-existing-tools)
- [Architecture](#architecture)
- [Roadmap](#roadmap)
- [Inspirations](#inspirations)
- [Contributing](#contributing)
- [License](#license)

---

## The Problem

Every developer on your team uses AI differently — different tools, different prompts, different results. Three problems compound:

- **Knowledge silos** — your best people discover effective workflows, but nothing spreads. New hires start from zero.
- **Tribal knowledge** — the most effective patterns live in people's heads. When they leave, it all goes with them.
- **Inconsistency** — five developers given the same task will prompt AI five different ways, producing five different quality levels.

The core insight: **AI is only as good as the person using it.** Distill institutionalizes the tacit knowledge of your best users so the whole team benefits.

---

## How Distill Works

```
Raw behavior capture
        ↓
Quality scoring
(PR merged? Review passed? Task completed?)
        ↓
Cross-user aggregation
(does this pattern appear across top performers?)
        ↓
Role skill synthesis
        ↓
Skill Pack per role → progressively injected into every AI session
```

Three layers, running quietly in the background:

### 1. Capture
Hooks into every AI interaction — prompts, tool calls, outputs — plus Git history (PRs, commits, reviews). No workflow changes required.

**Data sources:**
- IDE hooks (Claude Code, Cursor, Windsurf)
- API proxy intercepting AI calls
- Git, PR, and code review history
- Internal docs (Notion, Confluence, email)

### 2. Evolve
A three-step pipeline runs on shared storage:

1. **Summarize** — distill each session into its essence
2. **Aggregate** — find patterns recurring across multiple high performers
3. **Execute** — produce an updated **Skill Pack** (manifest + modular skill files)

Only **quality interactions** are learned from: merged PR = signal, rejected = noise.

### 3. Distribute
Skill packs sync to every developer by role. When they open their IDE or chat with an AI, the pack's manifest auto-injects into context, and individual skill modules load on demand as the task demands them — zero extra effort, zero context bloat.

---

## Output: Role-Scoped Skill Pack

A **skill pack** is a bundle of composable skill modules, not a single file. Each role gets its own pack — for example `senior-backend-dev/`:

```
senior-backend-dev/
├── manifest.md          # lightweight index: triggers, descriptions, module map
├── skills/
│   ├── api-design.md
│   ├── db-migration.md
│   ├── testing.md
│   ├── code-review.md
│   └── ...
└── references/          # long-tail patterns, retrieved on demand
```

Each pack captures:

- Real tech standards and coding conventions (as practiced, not as documented)
- Workflow patterns that actually work
- How to prompt AI effectively for each kind of task
- Common pitfalls and how to avoid them
- Decision patterns for recurring situations

**Why a pack instead of one big `SKILL.md`?** At scale, a monolithic file blows up the context window, dilutes signal, and breaks prompt caching on every edit. The skill pack uses **progressive disclosure**: the manifest is always present (cheap, stable, cache-friendly), and full modules load only when their triggers match the current task. See [`docs/skill-pack.md`](docs/skill-pack.md) for the full design.

---

## Why It Fits the Enterprise

| Criterion | How Distill handles it |
|---|---|
| **Privacy-safe** | Captures patterns, not sensitive content. Fully on-premise deployable. |
| **Opt-in friendly** | Nothing changes for developers — skills improve silently in the background. |
| **Auditable** | Every skill change is versioned, reviewable, and rollback-safe. |
| **Role-scoped** | Skills belong to roles, not individuals — no personal privacy concerns, easy onboarding. |
| **Platform-agnostic** | Works with Claude Code, Cursor, Windsurf, Copilot — no lock-in. |

---

## Compared to Existing Tools

|  | Prompt libraries | AI coding guidelines | Knowledge mgmt | **Distill** |
|---|---|---|---|---|
| Automated capture | No | No | No | **Yes** |
| Collective learning | No | No | Partial | **Yes** |
| Executable output | Partial | Yes | No | **Yes** |
| Self-evolving | No | No | No | **Yes** |

No existing product combines all four. That gap is what Distill fills.

---

## Architecture

Distill is organized around three decoupled layers — each can run independently, scale separately, and be swapped out.

- **Capture layer** — lightweight hooks and proxies that stream AI interaction events into shared storage.
- **Evolve layer** — the `Summarize → Aggregate → Execute` pipeline, triggered on a schedule or event.
- **Distribute layer** — role-indexed skill pack sync that reaches every IDE and AI client the team uses, with progressive disclosure at inject time.

More design notes:

- [`docs/idea.md`](docs/idea.md) — original vision and motivation
- [`docs/skill-pack.md`](docs/skill-pack.md) — skill pack format, manifest schema, progressive disclosure
- [`docs/architecture.md`](docs/architecture.md) — layer breakdown, data flow, open questions

---

## Roadmap

| Phase | Timeline | Goal | Validation |
|---|---|---|---|
| **1. Manual seed** | 2–4 weeks | Interview top 2–3 engineers, hand-write the first `SKILL.md` | Does it help other engineers do better work? |
| **2. Semi-auto** | 1–2 months | Deploy capture layer + basic evolve pipeline | Do auto-updates stay correct? |
| **3. Full pipeline** | 3–6 months | Automated capture → evolve → distribute, company-wide | ROI: onboarding time, code quality, AI output consistency |

---

## Inspirations

Distill stands on the shoulders of three projects whose ideas shaped its design:

| Project | What we learned |
|---|---|
| **claude-mem** | Lifecycle hooks, the capture → compress → inject pattern, progressive disclosure |
| **SkillClaw** | Collective evolution engine, the Summarize → Aggregate → Execute pipeline, multi-user aggregation |
| **colleague-skill** | Chat-based intake flow, correction layer, diverse data sources (chat, email, docs, PRs) |

---

## Contributing

Distill is in early development. We're looking for collaborators interested in:

- Capture integrations for IDEs and AI tools
- Pattern-mining and aggregation strategies
- Skill file formats and distribution mechanisms
- Real-world feedback from teams willing to pilot Phase 1

Open an issue to start a conversation. Contribution guidelines will land with the first tagged release.

---

## License

To be decided before the first release. Likely Apache 2.0 or MIT — feedback welcome.

---

*Distill — your team's best work, distilled into every AI session.*
