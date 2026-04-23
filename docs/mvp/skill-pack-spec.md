# Skill Pack Spec — Backend Dev + Business Analyst

> Concrete shape của pack output. Đây là cái pipeline phải đạt sau Day 7 MVP.
> MVP làm 1 role (Dev *hoặc* BA), nhưng spec dưới cover cả 2 để tham khảo.

---

## Common structure

```
packs/<role>/v0.1/
├── manifest.md          # always-injected (≤ 1500 tokens)
├── skills/              # load theo trigger
│   └── *.md             # mỗi module 500–2000 tokens
└── pack.yaml            # version + provenance
```

**MVP bỏ**: `references/`, `CHANGELOG.md`, pack PR review workflow, vector
retrieval. Tất cả vào Phase 2.

### `pack.yaml`

```yaml
role: backend-dev | business-analyst
version: 2026.04.1                          # YYYY.MM.N
generated_at: 2026-04-22T08:22:00Z
source_window: 2026-01-22..2026-04-22
contributors: 11                            # số người unique đóng góp artifact
quality_signals:
  source_artifacts: 247
  filtered_in: 62                           # vượt threshold score
  filtered_out: 185
  modules_generated: 5
checksum: sha256:9a3b7c...
approved_by: alice (senior-dev), bob (lead-ba)
approved_at: 2026-04-23T10:00:00Z
llm_model: claude-sonnet-4-7-20251022       # pin để reproducible
```

---

## Backend Dev pack

### Skill modules (target 4–6 cho MVP)

| Module | Trigger (regex/path) | Source artifacts |
|---|---|---|
| `api-design.md` | `**/handlers/**`, `**/routes/**`, `openapi.yaml` | MR diffs trong path này |
| `db-migration.md` | `migrations/**`, `schema.sql` | MR + revert history |
| `testing.md` | `**/*_test.go`, `**/test_*.py` | Test additions trong merged MRs |
| `code-review-conventions.md` | luôn load | Review comments aggregated |
| `error-handling.md` | path có `errors.go`, `exceptions.py` | MR diffs + review feedback |

### Module template (Dev)

```markdown
# <Module name>

## When this applies
<Trigger conditions paraphrase từ manifest>

## Hard rules (team conventions)
- <rule> [src: !1234, !1567, !1890]
- <rule> [src: review-thread-1234]

## Patterns

### Pattern A: <name>
**Apply when**: <situation>
**Do**:
\`\`\`<lang>
<code skeleton>
\`\`\`
**Why**: <rationale derived from review comments>
**Sources**: !1234 (merged), !1567 (merged), review-thread-2890

### Pattern B: ...

## Pitfalls
- <anti-pattern> — observed in: !1100 (reverted), !1340 (rejected)

## Provenance
Aggregated from 47 merged MRs + 89 review comments,
window 2026-01-15..2026-04-15, 11 contributors.
```

### Manifest (Dev) — skeleton

```markdown
# Backend Dev — Skill Pack Manifest (v2026.04.1)

You are pairing with a backend engineer on team <X>. Always follow hard rules.
Load skill modules when triggers match.

## Hard rules (always apply)
- Mọi DB migration phải có rollback plan inline
- Mọi endpoint mới phải có Pact contract test
- Không log raw request body (PII risk)
- Error response phải dùng envelope `{code, message, request_id}`
- Concurrency: dùng `lib/sync` helpers, không spawn raw goroutines/threads
- <... 5–10 rules từ aggregated review comments>

## Skill modules

| Module | Load when |
|---|---|
| skills/api-design.md | files match `handlers/**` or prompt mentions endpoint/route/API |
| skills/db-migration.md | files match `migrations/**` or prompt mentions migration/schema |
| skills/testing.md | files match `**/*_test.*` or prompt mentions test/fixture |
| skills/code-review-conventions.md | always |
| skills/error-handling.md | files contain error/exception patterns |
```

---

## Business Analyst pack

### Skill modules (target 4–5 cho MVP)

| Module | Trigger | Source artifacts |
|---|---|---|
| `spec-writing.md` | always | Top 25% Confluence specs |
| `acceptance-criteria.md` | prompt: "AC", "user story", "given when then" | Linked Jira issues của top specs |
| `discovery.md` | prompt: "research", "interview", "discovery" | Confluence discovery docs |
| `prioritization.md` | prompt: "RICE", "priority", "roadmap" | Roadmap pages + Jira priority history |
| `stakeholder-comms.md` | prompt: "update", "status", "escalation" | Confluence retros + Jira comment threads |

### Module template (BA)

BA modules chứa **templates + checklists + decision frameworks**, không phải code:

```markdown
# Spec Writing

## When this applies
Always — luôn áp dụng khi viết PRD/spec mới.

## Required sections (chưng từ top 31 specs)

| Section | % top specs có | Rationale |
|---|---|---|
| Problem | 100% | [src: PRD-201, PRD-189, PRD-245] |
| Success metrics | 94% | [src: PRD-201, PRD-189] |
| Solution | 100% | — |
| Acceptance criteria | 87% | [src: PRD-201, PRD-167] |
| Edge cases (≥5) | 74% | [src: PRD-189, PRD-245] |
| Out of scope | 68% | [src: PRD-201] |
| Rollout plan | 58% | [src: PRD-189] |

## Template skeleton

\`\`\`markdown
# [Feature name]

## Problem
- Who: [user segment + size]
- Pain: [evidence — quote, data, support tickets]
- Cost of inaction: [opportunity cost / risk]

## Success metrics
- Leading: [đo trong 1 tuần post-launch]
- Lagging: [đo trong 1 quý]

## Solution
[2–4 đoạn]

## Acceptance criteria
GIVEN <preconditions>
WHEN <action>
THEN <observable outcome>

## Edge cases
- [scenario 1]
- ...

## Out of scope
- [explicit list]

## Rollout plan
- Flag: [name]
- Stages: [%]
- Kill switch: [criteria]

## Open questions
- [ ] ...
\`\`\`

## Pitfalls (từ specs có scope-change cao)
- ❌ Solution viết trước khi xong Problem [src: PRD-156, PRD-178]
- ❌ AC dùng "should support" thay vì observable behavior [src: PRD-198]
- ❌ Không có "What we don't know" → dev hỏi clarification giữa sprint [src: PRD-167]

## Provenance
Aggregated from 31 high-quality specs (top 25%),
window 2026-01-01..2026-04-15, 6 BA contributors.
Quality threshold: composite score ≥ 7.0 (xem evaluation.md).
```

### Manifest (BA) — skeleton

```markdown
# Business Analyst — Skill Pack Manifest (v2026.04.1)

You are pairing with a BA on team <X>. Help draft specs, user stories,
acceptance criteria. Always follow hard rules. Load modules per trigger.

## Hard rules (always apply)
- Mọi spec mới phải có Success Metrics section (leading + lagging)
- AC luôn dùng GWT format, observable behavior
- Edge cases tối thiểu 5 scenarios, mỗi scenario có expected behavior
- Out-of-scope explicit, không để ngầm
- Spec phải có "Open questions" section nếu chưa decide
- Khi update spec sau khi dev đã start, đánh dấu BREAKING CHANGE
- <... rules từ retro action items>

## Skill modules

| Module | Load when |
|---|---|
| skills/spec-writing.md | always |
| skills/acceptance-criteria.md | prompt mentions AC/user story/GWT |
| skills/discovery.md | prompt mentions research/interview/discovery |
| skills/prioritization.md | prompt mentions RICE/priority/roadmap |
| skills/stakeholder-comms.md | prompt mentions status/update/escalation |
```

---

## Generation rules (LLM constraints)

Khi LLM synthesize module, **mọi claim phải có citation**:

```python
SYNTHESIZE_SYSTEM_PROMPT = """
You are writing a skill module for role X. You receive N extracted patterns
from artifacts (MR diffs, review comments, spec sections).

RULES:
1. Every "do" or "don't" rule MUST cite ≥ 2 source artifact IDs.
2. Patterns appearing in < 3 sources MUST be moved to "long-tail" or dropped.
3. Numerical claims MUST cite source ("87% of top specs use GWT [src: ids]").
4. If you cannot find evidence for a claim, OMIT IT. Do not generalize.
5. Code/template examples MUST be derived from real diffs/specs, not invented.
6. Output JSON matching schema MODULE_SCHEMA.
7. Tone: imperative, concise. No filler.

If you have low confidence in a section, leave it empty rather than fabricate.
"""
```

### Citation validator

Post-process: parse module markdown, mọi bullet/claim phải match regex
`\[src: [\w!,-]+\]`. Modules fail validation:

1. Reject + log để debug prompt
2. Optionally: regenerate với feedback "missing citations on lines X, Y"
3. Nếu fail 2 lần → đẩy sang **human-author queue** thay vì auto-publish

---

## Extraction schema (LLM output JSON)

Đây là structured output từ extract step (trước cluster + synthesize):

```json
{
  "artifact_id": "...",
  "artifact_kind": "gitlab_mr | jira_issue | confluence_page",
  "task_type": "string",
  "domain_tags": ["api", "db", "testing", ...],
  "patterns": [
    {
      "kind": "convention | template | anti-pattern | decision",
      "summary": "string (≤ 200 chars)",
      "evidence_excerpt": "string (≤ 500 chars, redacted)",
      "confidence": 0.0-1.0
    }
  ],
  "files_touched": ["path/...", ...],
  "outcome_signal": "merged | reverted | reopened | shipped_clean | ..."
}
```

Schema enforcement: dùng JSON mode của LLM API. Nếu output không parse được →
retry 1 lần, fail → drop artifact (log để debug).

---

## Module size budget

| File | Soft cap | Hard cap |
|---|---|---|
| `manifest.md` | 1500 tokens | 2000 |
| Mỗi `skills/*.md` | 2000 tokens | 3000 |
| Total pack (manifest + all modules) | 12000 tokens | 20000 |

Vượt cap → split module hoặc tighten content. Lý do: Claude Project knowledge
file budget + prompt cache efficiency.

---

## Versioning (MVP)

- MVP chỉ có 1 version: `v0.1`
- Git tag: `pack-<role>-v0.1`
- Pack.yaml chứa checksum để kiểm reproducibility
- Phase 2 mới quan tâm: rollback automation, multi-version maintenance, sync
