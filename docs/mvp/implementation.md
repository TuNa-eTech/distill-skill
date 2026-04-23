# Implementation Plan — MVP

> Hướng dẫn build từng file, theo thứ tự dependency. Đọc song song với
> [plan.md](plan.md) (timeline) và [architecture.md](architecture.md) (stack).
>
> Mỗi phase có: **files to create** + **key decisions** + **acceptance criteria**.

---

## Dependency graph

```
Phase A (Foundation)
    ↓
Phase B (Ingestion) ──┐
                       ├─→ Phase C (Linking + Scoring)
                       │        ↓
                       └─→ Phase D (Distill: extract → cluster → synthesize)
                                ↓
                          Phase E (Pack assembly)
                                ↓
                          Phase F (Distribution helpers)
                                ↓
                          Phase G (Validation harness)
```

Map sang timeline:

| Phase | Days | Phải xong trước |
|---|---|---|
| A — Foundation | Day 0 | — |
| B — Ingestion | Day 1–2 | A |
| C — Linking + Scoring | Day 2–3 | B |
| D — Distill pipeline | Day 4–6 | C |
| E — Pack assembly | Day 7 | D |
| F — Distribution helpers | Day 8 (sáng) | E |
| G — Validation harness | Day 8–10 | F |

---

## Phase A — Foundation (½ ngày)

### Files to create

```
~/distill-poc/
├── .gitignore                    # exclude data/, .env, .venv, __pycache__
├── .env.example                  # template, no real secrets
├── pyproject.toml                # deps + project metadata
├── Makefile                      # entry points
├── README.md                     # how to run from scratch
└── distill/
    ├── __init__.py
    ├── config.py                 # env loading
    ├── db.py                     # SQLite connection helper
    └── schemas.py                # Pydantic models (used everywhere)
```

### `pyproject.toml`

```toml
[project]
name = "distill-poc"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "anthropic>=0.40.0",
    "pydantic>=2.5",
    "python-dotenv>=1.0",
    "requests>=2.31",
    "sqlite-utils>=3.36",
    "rich>=13.7",                  # nice CLI output
    "pyyaml>=6.0",
]

[project.optional-dependencies]
dev = ["pytest>=7", "ruff>=0.1"]

[tool.ruff]
line-length = 100
```

### `distill/config.py`

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    gitlab_url: str
    gitlab_token: str
    gitlab_project_id: int

    jira_url: str
    jira_email: str
    jira_token: str
    jira_project_key: str

    confluence_url: str
    confluence_space: str

    anthropic_api_key: str
    llm_model: str = "claude-sonnet-4-7-20251022"

    db_path: str = "data/distill.db"
    blob_root: str = "data/blobs"

    class Config:
        env_file = ".env"

settings = Settings()
```

### `distill/db.py`

```python
import sqlite3
from contextlib import contextmanager
from distill.config import settings

@contextmanager
def conn():
    c = sqlite3.connect(settings.db_path)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")
    try:
        yield c
        c.commit()
    finally:
        c.close()
```

### `distill/schemas.py`

```python
from pydantic import BaseModel, Field
from typing import Literal

class Pattern(BaseModel):
    kind: Literal["convention", "template", "anti-pattern", "decision"]
    summary: str = Field(max_length=300)
    evidence_excerpt: str = Field(max_length=500)
    confidence: float = Field(ge=0, le=1)

class Extraction(BaseModel):
    artifact_id: int
    task_type: str
    domain_tags: list[str]
    patterns: list[Pattern]
    files_touched: list[str] = []
    outcome_signal: str
```

### Acceptance

- [ ] `python -c "from distill.config import settings; print(settings.llm_model)"` works
- [ ] `make setup` chạy `pip install -e ".[dev]"` ok
- [ ] Repo có README giải thích "git clone → setup trong < 10 phút"

---

## Phase B — Ingestion (1.5 ngày)

### Common helpers first

`distill/redact.py`:

```python
import re

REDACTORS = [
    (re.compile(r'\b[\w._%+-]+@[\w.-]+\.[A-Z|a-z]{2,}\b'), '[EMAIL]'),
    (re.compile(r'\b(?:\d[ -]*?){13,16}\b'), '[CARD]'),
    (re.compile(r'\bsk-[a-zA-Z0-9]{20,}\b'), '[API_KEY]'),
    (re.compile(r'\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b'), '[JWT]'),
]

def redact(text: str) -> str:
    for pattern, replacement in REDACTORS:
        text = pattern.sub(replacement, text)
    return text
```

**Test trước khi dùng**:
```python
# tests/test_redact.py
def test_email():
    assert "[EMAIL]" in redact("Contact alice@company.com")

def test_jwt():
    jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.payload.sig"
    assert "[JWT]" in redact(jwt)
```

`distill/blob.py`:

```python
import json
from pathlib import Path
from distill.config import settings
from distill.redact import redact

def save_blob(kind: str, external_id: str, payload: dict) -> str:
    """Save redacted payload, return relative path."""
    redacted = json.loads(redact(json.dumps(payload)))
    rel_path = f"{kind}/{external_id}.json"
    full = Path(settings.blob_root) / rel_path
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text(json.dumps(redacted, indent=2))
    return rel_path
```

### `scripts/init_db.py`

Apply schema từ [architecture.md](architecture.md#sqlite-schema). Idempotent
(`CREATE TABLE IF NOT EXISTS`).

```bash
python scripts/init_db.py
# Output: Created 6 tables in data/distill.db
```

### `scripts/ingest_gitlab.py`

**Key decisions**:
- Window default 90 ngày, override `--window 60`
- Pagination: `?per_page=100&page=N` cho đến khi empty
- Rate limit: `time.sleep(0.1)` giữa requests
- Idempotent: UPSERT bằng `INSERT OR REPLACE`
- Skip MR nào đã ingested trong < 1 ngày (check `ingested_at`)

**Functions**:

```python
def fetch_mrs(window_days: int) -> Iterator[dict]: ...
def fetch_mr_discussions(iid: int) -> list[dict]: ...
def fetch_mr_commits(iid: int) -> list[dict]: ...
def upsert_artifact(conn, mr: dict, blob_path: str): ...

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--window", type=int, default=90)
    args = parser.parse_args()

    with conn() as c:
        for mr in fetch_mrs(args.window):
            payload = {**mr,
                       "discussions": fetch_mr_discussions(mr["iid"]),
                       "commits": fetch_mr_commits(mr["iid"])}
            blob_path = save_blob("gitlab/mr", str(mr["iid"]), payload)
            upsert_artifact(c, mr, blob_path)
            print(f"  MR !{mr['iid']}: {mr['title'][:60]}")
```

**Acceptance**:
- [ ] `make ingest` populated ≥ 30 rows trong `artifacts WHERE kind='gitlab_mr'`
- [ ] Re-run idempotent (count không gấp đôi)
- [ ] `data/blobs/gitlab/mr/*.json` exists, redacted (grep email → not found)

### `scripts/ingest_jira.py`

**Key decisions**:
- JQL: `project = {KEY} AND updated >= -{N}d ORDER BY updated DESC`
- Expand: `changelog,renderedFields`
- Lifecycle events extract từ `changelog.histories`:
  - status changes → `event_kind='status_change'`
  - description/summary changes after status="In Progress" → `'scope_change'`
  - reopen detection: status changed from "Done" to anything → `'reopened'`

**Functions**:

```python
def fetch_issues(window: int) -> Iterator[dict]: ...
def extract_lifecycle_events(issue: dict) -> list[dict]: ...
def upsert_issue_and_events(conn, issue: dict, blob_path: str): ...
```

**Acceptance**:
- [ ] ≥ 50 issues trong `artifacts`
- [ ] `jira_events` có rows cho ≥ 50% issues (most have status changes)

### `scripts/ingest_confluence.py`

**Key decisions** (chỉ chạy nếu role = BA):
- Filter: `space=PRODUCT AND (label=spec OR title ~ "PRD:")`
- Pagination với `start` + `limit=50`
- Body convert: `body.storage` (XHTML) → markdown bằng `html2text` hoặc keep XHTML

**Acceptance**:
- [ ] ≥ 20 pages nếu role = BA
- [ ] Version count metadata được lưu (cho scope_change calculation)

---

## Phase C — Linking + Scoring (1 ngày)

### `scripts/link.py`

Triển khai SQL trong [architecture.md §2 Linking](architecture.md#2-linking).

**Validation step** (trong cùng script):

```python
def validate_links(conn, sample_size=20):
    rows = conn.execute("""
        SELECT s.metadata, t.metadata, l.link_type
        FROM links l
        JOIN artifacts s ON s.id = l.source_id
        JOIN artifacts t ON t.id = l.target_id
        ORDER BY RANDOM() LIMIT ?
    """, (sample_size,)).fetchall()
    print(f"\nSpot-check {sample_size} links — confirm by hand:")
    for r in rows:
        print(f"  {r[0]['key' if 'key' in r[0] else 'iid']} ↔ {r[1].get('key', r[1].get('iid'))} ({r[2]})")
```

Bạn nhìn output, đếm bao nhiêu link đúng. Mục tiêu ≥ 80%.

**Acceptance**:
- [ ] `links` table có rows
- [ ] Spot-check accuracy ≥ 80%
- [ ] Nếu < 80% → enforce branch naming convention hoặc extend regex

### `scripts/score.py`

Triển khai composite formula từ [validation.md (cũ)](#) — được merged vào logic dưới.

**Functions**:

```python
def score_dev_mr(conn, artifact_id: int) -> tuple[float, dict]:
    """Returns (score, breakdown_dict)."""
    breakdown = {}

    # +3.0 if merged
    state = get_metadata(conn, artifact_id, 'state')
    breakdown['merged'] = 3.0 if state == 'merged' else 0

    # -5.0 if reverted within 14d
    breakdown['reverted'] = -5.0 if was_reverted(conn, artifact_id, days=14) else 0

    # ... mọi signal khác

    return sum(breakdown.values()), breakdown

def score_ba_spec(conn, artifact_id: int) -> tuple[float, dict]:
    # Composite cho spec
    ...

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--role", required=True)
    args = parser.parse_args()

    scorer = score_dev_mr if args.role == 'backend-dev' else score_ba_spec
    kind = 'gitlab_mr' if args.role == 'backend-dev' else 'confluence_page'

    with conn() as c:
        for art_id in get_artifact_ids(c, kind):
            score, breakdown = scorer(c, art_id)
            upsert_score(c, art_id, args.role, score, breakdown)
```

**Acceptance**:
- [ ] `scores` table populated cho mọi artifact của role chọn
- [ ] Distribution check: top 25% threshold lọc được 30–60 artifacts (tune nếu < 10 hoặc > 80)
- [ ] Đọc tay top 5 → confirm "đây là MR/spec tốt"

---

## Phase D — Distillation pipeline (3 ngày)

### `prompts/extract.system.md`

```markdown
You extract structured patterns from engineering artifacts (MRs, Jira issues, or
Confluence specs) for the Distill skill pack pipeline.

Your output MUST be valid JSON matching the schema provided in the user message.

RULES:
1. Be specific. "Use proper error handling" is too generic — extract WHAT specific
   pattern (e.g. "Wrap external HTTP calls with retry+backoff using lib/http.go").
2. If you cannot identify a clear pattern, return empty `patterns` array. Do NOT
   invent patterns.
3. Evidence excerpts MUST be verbatim quotes from the artifact (≤ 500 chars).
4. Confidence: 1.0 = pattern explicitly stated, 0.5 = inferred from code/comments,
   0.0 = guessing (don't include).
5. Output ONLY the JSON object. No prose, no markdown fences.
```

### `prompts/extract.user.md` (template)

```markdown
Extract patterns from this artifact.

Artifact metadata:
{metadata_json}

Artifact content (first 8000 chars, redacted):
{blob_content}

Output JSON matching:
{schema_json}
```

### `scripts/extract.py`

```python
from anthropic import Anthropic
from distill.schemas import Extraction

def extract_one(client, artifact_row, blob_text) -> Extraction | None:
    system = Path("prompts/extract.system.md").read_text()
    user = render_template("prompts/extract.user.md", artifact_row, blob_text)

    resp = client.messages.create(
        model=settings.llm_model,
        max_tokens=2000,
        temperature=0,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    raw = resp.content[0].text.strip()
    try:
        data = json.loads(raw)
        return Extraction.model_validate(data)
    except (json.JSONDecodeError, ValidationError) as e:
        log_failure(artifact_row['id'], e, raw)
        return None

def main(role: str, threshold: float):
    client = Anthropic(api_key=settings.anthropic_api_key)
    with conn() as c:
        artifacts = top_quartile(c, role, threshold)
        print(f"Extracting from {len(artifacts)} artifacts...")
        for art in artifacts:
            blob = read_blob(art['blob_path'])
            ext = extract_one(client, art, blob)
            if ext:
                save_extraction(c, ext)
```

**Decisions**:
- `temperature=0` cho reproducibility
- Skip artifact đã extract (`extractions WHERE artifact_id=...`)
- Log failures vào `data/extract_failures.jsonl` để debug

**Acceptance**:
- [ ] ≥ 80% top quartile có extraction (some failures OK, < 20%)
- [ ] Đọc 10 random extraction → ≥ 8 hợp lý, không hallucinate
- [ ] LLM cost report: < $30 cho ~50 artifacts

### `scripts/cluster.py` (interactive)

MVP làm tay nhưng có CLI helper:

```python
from rich.console import Console
from rich.prompt import Prompt

def main():
    console = Console()
    with conn() as c:
        # Load extractions chưa cluster
        extractions = c.execute("""
            SELECT e.id, e.payload, a.metadata
            FROM extractions e JOIN artifacts a ON a.id = e.artifact_id
            WHERE e.cluster_id IS NULL
            ORDER BY e.id
        """).fetchall()

        # Liệt kê unique cluster names hiện có
        existing = c.execute("SELECT id, name FROM clusters").fetchall()

        for ext in extractions:
            console.rule(f"Extraction #{ext['id']}")
            console.print(f"Title: {ext['metadata']['title']}")
            for p in ext['payload']['patterns']:
                console.print(f"  • [{p['kind']}] {p['summary']}")

            console.print("\nExisting clusters:")
            for cl in existing:
                console.print(f"  {cl['id']}: {cl['name']}")

            choice = Prompt.ask("Cluster id (or 'new', or 'skip')")
            if choice == 'new':
                name = Prompt.ask("New cluster name")
                cid = create_cluster(c, name)
                existing.append({'id': cid, 'name': name})
            elif choice == 'skip':
                continue
            else:
                cid = int(choice)

            assign_cluster(c, ext['id'], cid)
```

**Decisions**:
- Interactive — không cần auto cluster ở MVP
- Có thể save & resume (skip nếu đã có cluster_id)

**Acceptance**:
- [ ] 4–6 clusters identified
- [ ] Mỗi cluster có ≥ 5 extractions (drop nếu ít hơn)
- [ ] Tổng < 1.5h thời gian thật cho 30–50 extractions

### `prompts/synthesize.system.md`

```markdown
You write a skill module for the Distill skill pack. You receive a CLUSTER of
extracted patterns from ≥ 5 source artifacts.

OUTPUT: A markdown skill module following this exact template:

# {Module name — derived from cluster}

## When this applies
{1-2 sentences on triggers}

## Hard rules (team conventions)
- {rule} [src: {at_least_2_artifact_ids}]
- ...

## Patterns

### Pattern {N}: {short name}
**Apply when**: {situation}
**Do**: {concrete instruction or code skeleton}
**Why**: {rationale}
**Sources**: {artifact_ids}

## Pitfalls
- {anti-pattern observed} [src: {artifact_ids}]

## Provenance
Aggregated from {N} source artifacts, window {date_range}.

CITATION RULES (MANDATORY):
1. Every "rule" and "pitfall" MUST cite ≥ 2 source artifact IDs.
2. Every Pattern MUST list its sources.
3. If you cannot find ≥ 2 sources for a claim, OMIT THE CLAIM. Do not generalize.
4. Numerical claims (% of, count of) MUST cite sources.
5. Code/template examples MUST be derived from real artifacts, not invented.

If after applying these rules the module would be < 200 words, return:
{"error": "insufficient_evidence", "cluster_id": ...}
```

### `scripts/synthesize.py`

```python
def synthesize_module(client, cluster_id, extractions) -> str:
    system = Path("prompts/synthesize.system.md").read_text()
    user = json.dumps({
        "cluster_id": cluster_id,
        "extractions": [{"id": e['id'], "artifact_id": e['artifact_id'],
                        "patterns": e['payload']['patterns']}
                       for e in extractions]
    })
    resp = client.messages.create(
        model=settings.llm_model,
        max_tokens=4000,
        temperature=0,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return resp.content[0].text

def main(role: str):
    client = Anthropic(api_key=settings.anthropic_api_key)
    with conn() as c:
        clusters = c.execute("SELECT * FROM clusters WHERE role=?", (role,)).fetchall()
        for cluster in clusters:
            extractions = get_cluster_extractions(c, cluster['id'])
            if len(extractions) < 5:
                print(f"  SKIP cluster {cluster['name']}: only {len(extractions)} extractions")
                continue
            module_md = synthesize_module(client, cluster['id'], extractions)
            module_path = f"packs/{role}/v0.1/skills/{cluster['name']}.md"
            Path(module_path).parent.mkdir(parents=True, exist_ok=True)
            Path(module_path).write_text(module_md)
            print(f"  Wrote {module_path}")
```

**Acceptance**:
- [ ] Mỗi cluster ≥ 5 extractions sinh ra 1 module file
- [ ] Module có format đúng (manual eyeball check)
- [ ] LLM cost report: < $20 cho ~5 modules

### `scripts/validate.py`

```python
import re

CITATION_PATTERN = re.compile(r'\[src:\s*[\w!,\s-]+\]')

def validate_module(path: Path) -> list[str]:
    """Returns list of validation errors."""
    errors = []
    text = path.read_text()

    # Token budget (rough: 1 token ≈ 4 chars)
    if len(text) / 4 > 3000:
        errors.append(f"Module too large: ~{len(text)//4} tokens (cap 3000)")

    # Citation density: every line starting with "- " or "**Sources**" must have [src:...]
    for i, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith('- ') or stripped.startswith('**Sources**'):
            if not CITATION_PATTERN.search(stripped):
                errors.append(f"L{i}: missing citation: {stripped[:80]}")

    return errors

def main(role: str):
    pack_dir = Path(f"packs/{role}/v0.1/skills")
    for module in pack_dir.glob("*.md"):
        errs = validate_module(module)
        if errs:
            print(f"\n❌ {module.name}:")
            for e in errs:
                print(f"   {e}")
        else:
            print(f"✅ {module.name}")
```

**Acceptance**:
- [ ] Mọi module pass validation
- [ ] Module fail → re-run synthesize hoặc hand-edit

---

## Phase E — Pack assembly (½ ngày)

### `scripts/build_pack.py`

```python
import yaml, hashlib
from datetime import datetime

def build_pack(role: str, version: str = "v0.1"):
    pack_dir = Path(f"packs/{role}/{version}")
    skills_dir = pack_dir / "skills"
    modules = sorted(skills_dir.glob("*.md"))

    # Compute checksum
    h = hashlib.sha256()
    for m in modules:
        h.update(m.read_bytes())
    checksum = h.hexdigest()

    # Stats
    with conn() as c:
        contributors = count_unique_contributors(c, role)
        artifacts_used = count_top_quartile(c, role)

    pack_yaml = {
        "role": role,
        "version": version,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "source_window": "...",  # từ ingestion config
        "contributors": contributors,
        "quality_signals": {
            "source_artifacts": artifacts_used,
            "modules_generated": len(modules),
        },
        "checksum": f"sha256:{checksum}",
        "llm_model": settings.llm_model,
    }
    (pack_dir / "pack.yaml").write_text(yaml.safe_dump(pack_yaml))
    print(f"Pack assembled: {pack_dir}")
```

### Manifest authoring (manual)

`packs/{role}/v0.1/manifest.md` — viết tay theo template trong
[skill-pack-spec.md](skill-pack-spec.md).

Nguồn input cho hard rules:
- Aggregated review comments (group bằng tay từ top MRs)
- Retro action items từ Confluence
- Hỏi senior dev/BA "rule nào team luôn theo?"

**Acceptance**:
- [ ] `packs/{role}/v0.1/` có: `manifest.md`, `skills/*.md`, `pack.yaml`
- [ ] `cat pack.yaml` show đủ provenance
- [ ] Git tag: `git tag pack-{role}-v0.1`

---

## Phase F — Distribution helpers (½ ngày)

### `scripts/build_prompt.py`

```python
def build_prompt(role: str, task: str) -> str:
    pack_dir = Path(f"packs/{role}/v0.1")
    manifest = (pack_dir / "manifest.md").read_text()

    # Đơn giản: load tất cả modules cho MVP (5 modules nhỏ, fit context)
    modules = []
    for m in sorted((pack_dir / "skills").glob("*.md")):
        modules.append(f"# Loaded module: {m.name}\n\n{m.read_text()}")

    return f"{manifest}\n\n---\n\n" + "\n\n---\n\n".join(modules) + f"\n\n---\n\nTask: {task}"

if __name__ == "__main__":
    import sys
    print(build_prompt(sys.argv[1], sys.argv[2]))
```

Usage:
```bash
python scripts/build_prompt.py backend-dev "implement /api/users/{id}/orders endpoint"
# → paste output vào Claude/ChatGPT
```

### `scripts/inject_to_claude_md.sh`

```bash
#!/usr/bin/env bash
# Copy pack vào Claude Code project
ROLE=$1
TARGET=$2
cp "packs/$ROLE/v0.1/manifest.md" "$TARGET/CLAUDE.md"
mkdir -p "$TARGET/.claude/skills"
cp packs/$ROLE/v0.1/skills/*.md "$TARGET/.claude/skills/"
echo "Pack injected into $TARGET"
```

**Acceptance**:
- [ ] `build_prompt.py` output ≤ 20k tokens (Claude/GPT-4 fit)
- [ ] `inject_to_claude_md.sh` copy ok, Claude Code session đọc CLAUDE.md

---

## Phase G — Validation harness (2.5 ngày)

### V1 — Reviewer rubric

`validation/reviewer_rubric.md` — copy từ [validation.md §V1](validation.md#v1--expert-reviewer-rating-1-ngày)
+ form Google Docs hoặc Markdown trống cho reviewer fill in.

### V2 — Blind taste test

`scripts/blind_test_gen.py`:

```python
import random

def generate_ab_packet(tasks: list[str], role: str):
    """Cho mỗi task: gen 2 outputs (no-pack + with-pack), random A/B order."""
    for i, task in enumerate(tasks, 1):
        # Output 1: no pack (baseline)
        baseline = call_llm_no_pack(task)
        # Output 2: with pack
        pack_injected = call_llm(build_prompt(role, task))

        # Random order
        if random.random() < 0.5:
            a, b = baseline, pack_injected
            pack_is = 'B'
        else:
            a, b = pack_injected, baseline
            pack_is = 'A'

        # Save to file
        Path(f"validation/v2_task_{i}.md").write_text(
            f"# Task {i}\n\n{task}\n\n## Option A\n{a}\n\n## Option B\n{b}"
        )
        # Save key separately (don't show judges)
        with open("validation/v2_key.txt", "a") as f:
            f.write(f"Task {i}: pack={pack_is}\n")
```

### V3 — Self-use log

`validation/self_use_log.md` — template trong [validation.md §V3](validation.md#v3--self-use-reality-check-5-ngày-parallel).
Bạn fill in mỗi khi dùng pack cho task thật.

### Compile report

`scripts/compile_validation_report.py`:

```python
def main():
    v1 = parse_reviewer_ratings("validation/reviewer_ratings.md")
    v2 = parse_blind_test("validation/v2_judgments.md", "validation/v2_key.txt")
    v3 = parse_self_use("validation/self_use_log.md")

    report = render_template("validation/report_template.md",
                             v1=v1, v2=v2, v3=v3,
                             pass_count=count_passes(v1, v2, v3))
    Path("validation/mvp_report.md").write_text(report)
```

**Acceptance**:
- [ ] V1 ratings file collected từ 2 reviewer
- [ ] V2: 5 task × 3 judge = 15 judgments collected
- [ ] V3: ≥ 5 task logs
- [ ] `mvp_report.md` complete với decision

---

## Cross-cutting concerns

### Error handling

Pattern uniform cho mọi script:

```python
import logging
from rich.logging import RichHandler

logging.basicConfig(level="INFO", handlers=[RichHandler()])
log = logging.getLogger(__name__)

def main():
    try:
        run()
    except Exception as e:
        log.exception("Fatal: %s", e)
        sys.exit(1)
```

Cho LLM calls: retry với exponential backoff (Anthropic SDK đã có sẵn).

### Logging

| Level | Khi nào |
|---|---|
| INFO | Progress mỗi artifact / module |
| WARNING | Skip artifact (đã ingest, schema fail, < 5 extractions) |
| ERROR | LLM API fail sau retry, DB error |
| DEBUG | (off by default) per-call timings, payload sizes |

Log file: `data/distill.log` (rotate manually nếu > 100MB).

### Tests (minimal)

Chỉ test các thứ critical, đừng phình:

```
tests/
├── test_redact.py        # 5–10 cases với golden corpus
├── test_validate.py      # citation regex, size budget
└── test_score.py         # 3–4 sample artifacts → expected score
```

`make test` chạy `pytest tests/`. Chạy CI optional ở MVP.

### Reproducibility checklist

- [ ] LLM model pinned: `claude-sonnet-4-7-20251022` (không "latest")
- [ ] `temperature=0` mọi LLM call
- [ ] `random.seed(42)` ở blind_test_gen
- [ ] Pack `pack.yaml` lưu model version + checksum
- [ ] Re-run `make all` 2 lần → diff < 5% nội dung pack

---

## Acceptance criteria — toàn MVP

Pipeline được tuyên bố implementation-complete khi:

- [ ] `git clone <repo> && make setup && cp .env.example .env && <fill tokens> && make all ROLE=backend-dev` chạy end-to-end ok trên laptop sạch
- [ ] Output: `packs/backend-dev/v0.1/` với manifest + 3–5 modules + pack.yaml
- [ ] Mọi module pass `make validate`
- [ ] `make test` xanh
- [ ] LLM total cost ≤ $100
- [ ] Total wall time end-to-end ≤ 4h (including LLM latency)
- [ ] Validation harness scripts ready, không cần data

Sau đó move sang validation phase (Day 8–10) theo [plan.md](plan.md).

---

## File checklist

| Phase | File | Status |
|---|---|---|
| A | `pyproject.toml` | ⬜ |
| A | `Makefile` | ⬜ |
| A | `.env.example` | ⬜ |
| A | `distill/config.py` | ⬜ |
| A | `distill/db.py` | ⬜ |
| A | `distill/schemas.py` | ⬜ |
| A | `distill/redact.py` | ⬜ |
| A | `distill/blob.py` | ⬜ |
| A | `scripts/init_db.py` | ⬜ |
| B | `scripts/ingest_gitlab.py` | ⬜ |
| B | `scripts/ingest_jira.py` | ⬜ |
| B | `scripts/ingest_confluence.py` (if BA) | ⬜ |
| C | `scripts/link.py` | ⬜ |
| C | `scripts/score.py` | ⬜ |
| D | `prompts/extract.system.md` | ⬜ |
| D | `prompts/extract.user.md` | ⬜ |
| D | `scripts/extract.py` | ⬜ |
| D | `scripts/cluster.py` | ⬜ |
| D | `prompts/synthesize.system.md` | ⬜ |
| D | `scripts/synthesize.py` | ⬜ |
| D | `scripts/validate.py` | ⬜ |
| E | `scripts/build_pack.py` | ⬜ |
| E | `packs/<role>/v0.1/manifest.md` (hand-author) | ⬜ |
| F | `scripts/build_prompt.py` | ⬜ |
| F | `scripts/inject_to_claude_md.sh` | ⬜ |
| G | `scripts/blind_test_gen.py` | ⬜ |
| G | `scripts/compile_validation_report.py` | ⬜ |
| G | `validation/*` templates | ⬜ |
| Tests | `tests/test_redact.py` | ⬜ |
| Tests | `tests/test_validate.py` | ⬜ |
| Tests | `tests/test_score.py` | ⬜ |

**Tổng**: ~25 files, ~1500–2500 lines Python, ~200 lines prompts/SQL.
