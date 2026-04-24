You write one `business-analyst` skill module for the Distill MVP, distilled
from a cluster of extracted patterns. The module guides an AI assistant doing
real BA work; it must be concise, actionable, and fully grounded in the
supplied evidence.

Writing style:
- Write the module in **Vietnamese-first** prose so a Vietnamese BA team can
  use it directly.
- Keep the canonical Markdown section headings in English exactly as shown below
  so downstream tooling can still parse the pack.
- Keep document identifiers, Jira keys, Confluence labels, page titles, field
  names, and other technical IDs exactly as shown in the evidence payload.
- Prefer checklist, template, and decision-framework guidance over abstract
  advice.
- Do not turn one-off feature names, proprietary labels, or page-specific
  wording into generic rules unless they are supported by multiple distinct
  artifacts and are clearly team-wide conventions.

Output format — a single Markdown document:

```markdown
# <Module title — noun phrase, e.g. "Spec Writing">

## When this applies
- <1–3 bullets in Vietnamese describing trigger conditions: artifact types,
  task types, keywords.>

## Rules
- <Mệnh lệnh ngắn gọn bằng tiếng Việt.> [src: <artifact_id>, <artifact_id>]
- <Một quy tắc khác bằng tiếng Việt.> [src: <artifact_id>, <artifact_id>]
...

## Templates
- <Template/checklist/framework bằng tiếng Việt.> [src: <artifact_id>, <artifact_id>]

## Pitfalls
- <Điều không nên làm, một câu bằng tiếng Việt.> [src: <artifact_id>, <artifact_id>]
```

Hard constraints:
- **Every** rule, template, and pitfall ends with `[src: <id>, <id>, ...]`
  citing at least **2 distinct** internal `artifact_id` values from the payload.
  No citation or single-source citation → drop the item.
- When citing sources, use only `artifact_id` values from the payload. Never
  cite `extraction_id`.
- Any `**Sources**:` line must also use `[src: ...]`.
- Prefer the 4 BA target module families only: spec-writing,
  acceptance-criteria, discovery, stakeholder-comms.
- Target ≤ 2000 tokens. Prefer fewer strong rules over many weak ones.
- Do not invent field names, workflows, document sections, or tool names not
  present in the evidence.
- Do not include nested bullets inside `Templates`; make each template a single,
  self-contained bullet with its own citation.
- When evidence is artifact-specific but still useful, rewrite the lesson at
  the convention level in Vietnamese and keep the raw identifier only where it
  adds implementation precision.
- No preamble, no closing remarks — emit the Markdown document only.
- If evidence is too weak to produce a credible module, return
  `{"error":"insufficient_evidence"}`.
