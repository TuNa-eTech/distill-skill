# Architecture — MVP

> Stack tối giản nhất có thể work. Python + SQLite + LLM API + filesystem.
> Không có service chạy nền, không có cron, không có cloud.

---

## Folder layout

```
~/distill-poc/
├── .env                          # API tokens (gitignored)
├── .gitignore
├── Makefile                      # entry point: make ingest, make distill, ...
├── pyproject.toml                # deps: requests, sqlite-utils, pydantic, anthropic
├── README.md                     # how to run
│
├── data/
│   ├── distill.db                # SQLite database
│   └── blobs/                    # raw payloads (redacted)
│       ├── gitlab/mr/<iid>.json
│       ├── jira/issue/<key>.json
│       └── confluence/page/<id>.json
│
├── scripts/
│   ├── ingest_gitlab.py
│   ├── ingest_jira.py
│   ├── ingest_confluence.py
│   ├── link.py
│   ├── score.py
│   ├── extract.py
│   ├── cluster.py                # opens markdown editor, manual grouping
│   ├── synthesize.py
│   ├── validate.py               # citation check + size budget
│   └── trace.py                  # debug: tại sao module X có claim Y
│
├── prompts/
│   ├── extract.system.md
│   ├── extract.user.md
│   └── synthesize.system.md
│
├── packs/
│   └── mobile-dev/
│       └── v0.1/
│           ├── manifest.md
│           ├── skills/
│           │   ├── state-management.md
│           │   ├── widget-testing.md
│           │   └── ...
│           └── pack.yaml
│
└── validation/
    ├── reviewer_ratings.md
    ├── blind_test_results.md
    └── self_use_log.md
```

---

## Stack

| Layer | Choice | Tại sao |
|---|---|---|
| Language | Python 3.11+ | Quick scripting, LLM SDKs tốt |
| Storage | SQLite (file) | Zero setup, query SQL được |
| Blobs | Filesystem (`data/blobs/`) | Đơn giản, grep được |
| LLM | Anthropic Claude (or OpenAI) SDK | Pin model version |
| HTTP | `requests` + retry | Đủ cho 3 crawlers |
| Schema | `pydantic` v2 | LLM JSON output validation |
| Build | `Makefile` | Mỗi step 1 target rõ |

**Không cần**: Postgres, Redis, S3, Docker, Kubernetes, FastAPI, Airflow,
SQLAlchemy, dbt, vector DB, anything else.

---

## SQLite schema

```sql
-- artifacts từ 3 sources
CREATE TABLE artifacts (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  kind         TEXT NOT NULL,           -- gitlab_mr | jira_issue | confluence_page
  external_id  TEXT NOT NULL,           -- "PROJ-1234" | "!4521" | "page:12345"
  created_at   TEXT,                    -- ISO8601
  updated_at   TEXT,
  metadata     TEXT,                    -- JSON: title, status, labels...
  blob_path    TEXT,                    -- relative path vào data/blobs/
  ingested_at  TEXT DEFAULT (datetime('now')),
  UNIQUE (kind, external_id)
);
CREATE INDEX idx_artifacts_kind ON artifacts(kind);

-- linking artifact ↔ artifact (MR ↔ Jira, spec ↔ Jira)
CREATE TABLE links (
  source_id   INTEGER NOT NULL,
  target_id   INTEGER NOT NULL,
  link_type   TEXT NOT NULL,
  confidence  REAL DEFAULT 1.0,
  PRIMARY KEY (source_id, target_id, link_type),
  FOREIGN KEY (source_id) REFERENCES artifacts(id),
  FOREIGN KEY (target_id) REFERENCES artifacts(id)
);

-- Jira lifecycle events (cho scope_change, reopen detection)
CREATE TABLE jira_events (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  issue_id     INTEGER REFERENCES artifacts(id),
  event_kind   TEXT,                    -- status_change | scope_change | reopened
  from_value   TEXT,
  to_value     TEXT,
  occurred_at  TEXT
);

-- composite quality scores
CREATE TABLE scores (
  artifact_id  INTEGER REFERENCES artifacts(id),
  role         TEXT,                    -- mobile-dev | business-analyst | tester-manual
  score        REAL,
  breakdown    TEXT,                    -- JSON per-signal contribution
  scored_at    TEXT DEFAULT (datetime('now')),
  PRIMARY KEY (artifact_id, role)
);

-- LLM extractions
CREATE TABLE extractions (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  artifact_id   INTEGER REFERENCES artifacts(id),
  cluster_id    INTEGER,                -- NULL nếu chưa cluster
  payload       TEXT,                   -- JSON match EXTRACTION_SCHEMA
  llm_model     TEXT,
  extracted_at  TEXT DEFAULT (datetime('now'))
);

-- manual clusters
CREATE TABLE clusters (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  role         TEXT,
  name         TEXT,                    -- "api-design", "db-migration"
  description  TEXT,
  created_at   TEXT DEFAULT (datetime('now'))
);
```

Tổng 6 tables. Tất cả trong 1 file `data/distill.db`.

---

## Pipeline — chạy bằng Makefile

```makefile
ROLE ?= mobile-dev
WINDOW ?= 90

.PHONY: setup ingest link score extract cluster synthesize validate all

setup:
	python -m venv .venv && \
	.venv/bin/pip install -e . && \
	.venv/bin/python scripts/init_db.py

ingest:
	.venv/bin/python scripts/ingest_gitlab.py --window $(WINDOW)
	.venv/bin/python scripts/ingest_jira.py --window $(WINDOW)
	.venv/bin/python scripts/ingest_confluence.py --window $(WINDOW)

link:
	.venv/bin/python scripts/link.py

score:
	.venv/bin/python scripts/score.py --role $(ROLE)

extract:
	.venv/bin/python scripts/extract.py --role $(ROLE)

cluster:
	.venv/bin/python scripts/cluster.py --role $(ROLE)
	# Mở $EDITOR với top extractions, bạn group manually

synthesize:
	.venv/bin/python scripts/synthesize.py --role $(ROLE)

validate:
	.venv/bin/python scripts/validate.py --role $(ROLE)

all: ingest link score extract cluster synthesize validate
	@echo "Pack ready: packs/$(ROLE)/v0.1/"

trace:
	.venv/bin/python scripts/trace.py --module $(MODULE)

clean:
	rm -rf data/distill.db data/blobs/*
```

**Run end-to-end**:
```bash
make setup
make all ROLE=mobile-dev WINDOW=90
```

Mọi step idempotent — re-run được không corrupt state (UPSERT pattern).

---

## .env

```bash
GITLAB_URL=https://gitlab.company.com
GITLAB_TOKEN=glpat-xxx
GITLAB_PROJECT_ID=42

JIRA_URL=https://company.atlassian.net
JIRA_EMAIL=you@company.com
JIRA_TOKEN=xxx
JIRA_PROJECT_KEY=PROJ

CONFLUENCE_URL=https://company.atlassian.net/wiki
CONFLUENCE_SPACE=PRODUCT

ANTHROPIC_API_KEY=sk-ant-xxx
LLM_MODEL=claude-sonnet-4-7
```

`.env` gitignored. Personal tokens, không share.

---

## Redaction (MVP version — basic)

MVP không cần entity recognition mạnh. Đủ:

```python
# scripts/redact.py
REGEX_REDACTORS = [
    (r'\b[\w._%+-]+@[\w.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]'),
    (r'\b(?:\d[ -]*?){13,16}\b', '[CARD]'),
    (r'\b(?:0|\+84)[\s-]?\d{2,3}[\s-]?\d{3,4}[\s-]?\d{3,4}\b', '[PHONE_VN]'),
    (r'\bsk-[a-zA-Z0-9]{20,}\b', '[API_KEY]'),
    (r'\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b', '[JWT]'),
]
```

Test với 10 sample artifacts có PII đã đánh dấu trước. Redactor catch ≥ 90% là OK
cho MVP. Production-grade NER + entity allowlist → Phase 2.

---

## Inject pack vào AI (MVP distribution)

MVP không sync Confluence/Claude Project. Cách dùng pack đơn giản nhất:

### Cách 1 — Claude Code project file

```bash
# Symlink hoặc copy pack vào project
cp packs/mobile-dev/v0.1/manifest.md /path/to/test-project/CLAUDE.md
cp -r packs/mobile-dev/v0.1/skills /path/to/test-project/.claude/skills/
```

Claude Code đọc `CLAUDE.md` mỗi session → manifest tự inject. Skills load qua
trigger hook (nếu cần test trigger).

### Cách 2 — System prompt direct

```bash
.venv/bin/python scripts/build_prompt.py \
  --role mobile-dev \
  --task "implement payment schedule edit flow in Flutter" \
  > prompt.txt

# Paste prompt.txt vào Claude/ChatGPT
```

`build_prompt.py` đọc manifest + matching modules theo trigger, output 1 prompt
hoàn chỉnh.

### Cách 3 — Anthropic API call

```python
client.messages.create(
    model="claude-sonnet-4-7",
    system=load_pack("mobile-dev/v0.1") + base_system,
    messages=[{"role": "user", "content": task}]
)
```

Đủ 3 cách cho MVP validation. Không cần build extension/proxy.

---

## Một step cụ thể — ví dụ `extract.py`

```python
# scripts/extract.py (rút gọn)
import json, sqlite3
from pydantic import BaseModel
from anthropic import Anthropic

class Pattern(BaseModel):
    kind: str  # convention | template | anti-pattern | decision
    summary: str
    evidence_excerpt: str
    confidence: float

class Extraction(BaseModel):
    artifact_id: int
    task_type: str
    domain_tags: list[str]
    patterns: list[Pattern]
    files_touched: list[str]
    outcome_signal: str

def extract_one(client, artifact, blob):
    system = open("prompts/extract.system.md").read()
    user = f"Artifact:\n{json.dumps(artifact)}\n\nBlob:\n{blob[:8000]}"
    resp = client.messages.create(
        model=os.environ["LLM_MODEL"],
        max_tokens=2000,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    raw = extract_json(resp.content[0].text)
    return Extraction.model_validate(raw)  # raises if schema fail

def main(role):
    conn = sqlite3.connect("data/distill.db")
    top = conn.execute("""
        SELECT a.* FROM artifacts a
        JOIN scores s ON s.artifact_id = a.id
        WHERE s.role = ? AND s.score >= ?
        ORDER BY s.score DESC LIMIT 100
    """, (role, THRESHOLD[role])).fetchall()

    client = Anthropic()
    for art in top:
        try:
            ext = extract_one(client, art, load_blob(art))
            save_extraction(conn, ext)
        except Exception as e:
            log_failure(art, e)
```

Toàn bộ pipeline ~500–800 dòng Python. Không phải framework, là script.

---

## Limits / known shortcuts ở MVP

| Thứ bị cắt | Tại sao OK ở MVP | Phase 2 cần |
|---|---|---|
| No incremental sync | Chạy 1 lần đủ | Yes (cron + cursor) |
| No worker pool | < 100 artifacts/role | Yes nếu > 1k/ngày |
| No production redactor | Self-data, low risk | Strong NER + allowlist |
| No pack PR review | Bạn tự review | Multi-reviewer workflow |
| No rollback automation | Git revert đủ | Atomic publish + rollback |
| No usage logging | Validation manual | Telemetry per module |

MVP validate **hypothesis**, không validate **scale**. Đừng confuse 2 cái.

---

## Reproducibility

Cuối MVP, người khác có thể replicate bằng:

```bash
git clone <poc-repo>
cp .env.example .env  # fill in tokens
make setup
make all ROLE=mobile-dev WINDOW=90
# → packs/mobile-dev/v0.1/ identical (modulo LLM non-determinism)
```

LLM call dùng `temperature=0` + pin model version để giảm variance. Output
diff giữa 2 run < 5% là acceptable.
