# Skill Pack Spec — Mobile Dev + Business Analyst + Tester Manual

> Concrete shape của pack output. Đây là cái pipeline phải đạt sau Day 7 MVP.
> Pilot hiện tại là `mobile-dev`; BA và `tester-manual` là role extension path
> đã có runtime support, nhưng chưa phải pilot scope chính.

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
role: mobile-dev | business-analyst | tester-manual
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
approved_by: alice (staff-mobile), bob (lead-ba)
approved_at: 2026-04-23T10:00:00Z
llm_model: claude-sonnet-4-7-20251022       # pin để reproducible
```

---

## Mobile Dev pack

### Skill modules (target 4–6 cho MVP)

| Module | Trigger (regex/path) | Source artifacts |
|---|---|---|
| `state-management.md` | `lib/**/bloc/**`, `lib/**/cubit/**`, `riverpod`, `provider` | MR diffs trong state layer |
| `navigation.md` | `lib/**/routes/**`, `go_router`, `navigator` | Screen/navigation MRs |
| `widget-testing.md` | `test/**`, `integration_test/**`, `golden` | Test additions trong merged MRs |
| `code-review-conventions.md` | luôn load | Review comments aggregated |
| `platform-integration.md` | `android/`, `ios/`, plugin/channel keywords | Native/plugin MRs + review feedback |

### Module template (Mobile Dev)

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
# Mobile Dev — Skill Pack Manifest (v2026.04.1)

You are pairing with a mobile engineer on team <X>. Always follow hard rules.
Load skill modules when triggers match.

## Hard rules (always apply)
- State thay đổi phải đi qua single source of truth, không duplicate state giữa widget và controller
- Async UI phải biểu diễn đủ loading, success, empty, error
- Luồng điều hướng mới phải có back behavior và deep-link expectation rõ ràng
- Không gọi plugin/platform channel mà không có fallback hoặc error UX
- Flow người dùng critical phải có widget/integration test trước merge
- <... 5–10 rules từ aggregated review comments>

## Skill modules

| Module | Load when |
|---|---|
| skills/state-management.md | files match `bloc/**`, `cubit/**`, `riverpod/**`, `provider/**` or prompt mentions state/event |
| skills/navigation.md | files match `routes/**` or prompt mentions screen/flow/navigation |
| skills/widget-testing.md | files match `test/**`, `integration_test/**` or prompt mentions widget/golden/integration test |
| skills/code-review-conventions.md | always |
| skills/platform-integration.md | files touch `android/`, `ios/`, plugins, permissions, channels |
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

## Tester Manual pack

### Skill modules (target 3 cho extension path)

| Module | Trigger | Source artifacts |
|---|---|---|
| `bug-report-quality.md` | prompt mentions defect/bug/actual vs expected/environment | Jira bug tickets |
| `regression-strategy.md` | prompt mentions regression/release/retest/checklist | Jira bugs + release-related stories/tasks |
| `test-case-design.md` | prompt mentions scenario/boundary/edge case/test case | Jira stories/tasks với AC hoặc coverage notes |

### Module template (Tester Manual)

Tester modules ưu tiên **observable behavior + checklist + defect communication**:

```markdown
# Bug Report Quality

## When this applies
Khi viết defect ticket mới hoặc refine bug đã được reopen / bounce lại.

## Rules
- Luôn có Steps to reproduce, Actual result, Expected result, Environment [src: QA-101, QA-122]
- Nếu bug chỉ xảy ra ở một build/device/version, ghi rõ ngay trong summary hoặc bullet đầu tiên [src: QA-101, QA-145]

## Templates
- Dùng skeleton: Preconditions, Steps, Actual, Expected, Environment, Severity, Attachments [src: QA-101, QA-122]

## Pitfalls
- ❌ Chỉ ghi "không chạy" mà không có đường đi tái hiện [src: QA-156, QA-199]
- ❌ Gộp nhiều lỗi không cùng root cause vào một ticket [src: QA-145, QA-188]
```

### Manifest (Tester Manual) — skeleton

```markdown
# Tester Manual — Skill Pack Manifest (v2026.04.1)

You are pairing with a manual tester. Help write clearer bug reports,
regression scope, and test cases. Always follow hard rules. Load modules per trigger.

## Hard rules (always apply)
- Bug report phải có Steps, Actual, Expected, và Environment nếu có dependency runtime
- Regression checklist phải cover main flow, failure path, và edge case có risk cao
- Không close bug nếu chưa xác nhận exact build / environment đã retest
- Test case phải mô tả observable behavior, không chỉ lặp lại tên field hoặc button
- Nếu issue bị reopen, bổ sung rõ gap coverage hoặc mismatch environment trước khi reassign

## Skill modules

| Module | Load when |
|---|---|
| skills/bug-report-quality.md | prompt mentions bug/defect/actual/expected/environment |
| skills/regression-strategy.md | prompt mentions regression/retest/release/smoke |
| skills/test-case-design.md | prompt mentions scenario/test case/edge case/boundary |
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
