# Getting Started — Distill MVP POC

> Hướng dẫn setup + chạy pipeline end-to-end trên laptop trong < 30 phút.
> Vision tổng quan của Distill xem [README.md](README.md). Architecture chi tiết
> xem [docs/mvp/architecture.md](docs/mvp/architecture.md).

---

## Project là gì

Distill là **organizational brain** cho engineering team dùng AI coding
assistant. POC này validate hypothesis cốt lõi:

> Có thể trích xuất pattern chất lượng cao từ artifact thực (GitLab MR, Jira
> issue, Confluence page) và tổng hợp thành **role-scoped skill pack** mà AI
> assistant có thể inject để nâng chất lượng output.

POC hiện chốt pilot trên 1 role duy nhất là `mobile-dev` với window 90 ngày.
`business-analyst` giữ ở mức reference docs cho phase sau. Output là 1 skill
pack `packs/mobile-dev/v0.1/` + validation report.

---

## Architecture (tóm tắt)

```
ingest → link → score → extract → cluster → synthesize → validate
GitLab    Jira    composite   LLM       manual     LLM         citation +
Jira      key     quality     pattern   theme      skill       budget check
Confluence match  formula     JSON      grouping   module
```

Stack: **Python 3.10+ · SQLite · Anthropic Claude · Makefile**. Không cron,
không service nền, không cloud. Layout chi tiết xem
[architecture.md](docs/mvp/architecture.md#folder-layout).

Dashboard web shell hiện nằm ở `apps/web/`, dùng **React + TypeScript + Vite +
Yarn** cho control-plane UI nội bộ.

---

## Prerequisites

| Thứ | Yêu cầu |
|---|---|
| Python | 3.10+ (`python --version`) |
| Token | GitLab personal token, Jira API token, Anthropic API key |
| Quyền | Read access vào project GitLab + Jira + Confluence space |
| OS | macOS / Linux (Windows dùng WSL) |
| Disk | ~500 MB cho blobs + DB |
| LLM budget | ~$50–100 cho 1 role × 90 ngày |

---

## Setup (5 phút)

```bash
# 1. Clone repo và vào thư mục
cd "Distill Skill"

# 2. Copy env template, điền token thật
cp .env.example .env
$EDITOR .env

# 3. Tạo venv + cài deps + init SQLite schema
make setup
```

Verify:

```bash
.venv/bin/python -c "import sqlite3, distill_core; \
  print('distill_core', distill_core.__version__); \
  print('tables:', [r[0] for r in sqlite3.connect('data/distill.db') \
    .execute(\"SELECT name FROM sqlite_master WHERE type='table'\")])"
```

Phải in ra `distill_core 0.1.0` và 6 tables: `artifacts, links, jira_events,
scores, extractions, clusters`.

## Run dashboard web shell

```bash
make web-install
make web-api
make web-dev
```

Chạy ở 2 terminal:

```bash
# terminal 1
make web-api

# terminal 2
cd apps/web
yarn dev
```

Build production:

```bash
make web-build
```

---

## Run pipeline end-to-end

```bash
# Chạy toàn bộ cho role mobile-dev, window 90 ngày
make all ROLE=mobile-dev WINDOW=90
```

Hoặc từng bước (debug dễ hơn):

| Step | Command | Output |
|---|---|---|
| 1 | `make ingest WINDOW=90` | Artifacts crawled vào `data/distill.db` + `data/blobs/` |
| 2 | `make link` | Cross-source links populated |
| 3 | `make score ROLE=mobile-dev` | Composite score per artifact |
| 4 | `make extract ROLE=mobile-dev` | LLM extractions (top-scored only) |
| 5 | `make cluster ROLE=mobile-dev` | **Interactive** — gõ tên cluster cho mỗi extraction |
| 6 | `make synthesize ROLE=mobile-dev` | Skill modules → `packs/mobile-dev/v0.1/skills/*.md` |
| 7 | `make validate ROLE=mobile-dev` | Citation + size budget check |

Pack final: `packs/mobile-dev/v0.1/` (manifest + skills + pack.yaml).

---

## Sử dụng pack với AI assistant

3 cách inject pack vào AI session — chi tiết xem
[architecture.md §Inject](docs/mvp/architecture.md#inject-pack-vào-ai-mvp-distribution):

1. **Claude Code project file** — copy `manifest.md` thành `CLAUDE.md` trong
   project test, copy `skills/` vào `.claude/skills/`.
2. **System prompt direct** — `.venv/bin/distill-build-prompt --role mobile-dev
   --task "implement payment schedule edit flow in Flutter" > prompt.txt` →
   paste vào Claude/ChatGPT.
3. **Anthropic API call** — load pack làm `system` parameter.

---

## Debug

| Vấn đề | Lệnh |
|---|---|
| Module có claim lạ — từ artifact nào? | `make trace MODULE=packs/mobile-dev/v0.1/skills/state-management.md` |
| Score distribution | `sqlite3 data/distill.db "SELECT role, COUNT(*), AVG(score) FROM scores GROUP BY role"` |
| Top artifacts theo score | `sqlite3 data/distill.db "SELECT a.kind, a.external_id, s.score FROM artifacts a JOIN scores s ON s.artifact_id=a.id WHERE s.role='mobile-dev' ORDER BY s.score DESC LIMIT 20"` |
| Reset toàn bộ data | `make clean && make init-db` |

---

## Folder layout (sau khi setup)

```
.
├── .env                          # secrets (gitignored)
├── pyproject.toml                # deps + console_scripts entry points
├── Makefile                      # thin wrapper around console_scripts
├── apps/
│   └── web/                      # React dashboard shell (Yarn + Vite)
├── data/
│   ├── distill.db                # SQLite (gitignored)
│   └── blobs/                    # raw artifact payloads (gitignored)
├── src/
│   ├── distill_core/             # config, db, schemas, llm, cli (shared primitives)
│   ├── distill_capture/          # ingest_gitlab/jira/confluence, link, redact
│   ├── distill_evolve/           # score, extract, cluster, synthesize, validate, trace
│   └── distill_distribute/       # build_prompt, pack loader (+ mcp_server later)
├── prompts/                      # extract.system.md, synthesize.system.md, ...
├── packs/<role>/v0.1/            # output skill pack
├── validation/                   # reviewer ratings, blind test, self-use log
└── docs/                         # vision + design notes
```

**Layer boundaries**: capture/evolve/distribute import từ `distill_core` only —
không cross-import giữa 3 layer cuối. Khi nào tách repo: xem
[architecture.md §Layers](docs/architecture.md).

---

## Definition of done (cho 1 lần chạy POC)

- [ ] `make all ROLE=<role>` chạy ok không lỗi
- [ ] `packs/<role>/v0.1/` có manifest + ≥ 3 skill modules + `pack.yaml`
- [ ] `make validate` báo PASS toàn bộ modules
- [ ] `validation/mvp_report.md` đã viết (V1 + V2 + V3 results)

---

## Tham khảo

- [README.md](README.md) — vision + business value
- [docs/mvp/plan.md](docs/mvp/plan.md) — 10-day execution plan
- [docs/mvp/architecture.md](docs/mvp/architecture.md) — design chi tiết
- [docs/mvp/skill-pack-spec.md](docs/mvp/skill-pack-spec.md) — pack output format
- [docs/mvp/validation.md](docs/mvp/validation.md) — V1/V2/V3 protocols
