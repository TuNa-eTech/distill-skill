# Plan — 2 tuần MVP

> 10 working days. 1 person. Mỗi day có deliverable check-able.
> Demo mini cuối mỗi tuần (tự ghi lại để track progress).

---

## Day 0 — Setup (½ ngày, trước Day 1)

| # | Task | Deliverable |
|---|---|---|
| 0.1 | Verify A1–A5 (xem [scope.md](scope.md#assumption-cần-verify-day-1)) | Tất cả token API work |
| 0.2 | Chốt pilot role = `mobile-dev` | Decision noted |
| 0.3 | `git init` repo MVP, `.env`, `Makefile`, folder structure | Layout giống [architecture.md](architecture.md#folder-layout) |
| 0.4 | `pip install` deps + `python scripts/init_db.py` | SQLite schema created |

**Gate**: `make setup` chạy ok, có thể query empty SQLite. → Day 1.

---

## Tuần 1 — Pipeline build

### Day 1 — Ingestion

| Time | Task |
|---|---|
| AM | `ingest_gitlab.py` — crawl 90d MRs + discussions + commits |
| PM | `ingest_jira.py` — crawl 90d issues + changelog + comments |
| EOD | Verify: `SELECT count(*) FROM artifacts GROUP BY kind` ≥ 50 mỗi loại |

### Day 2 — Ingestion (cont.) + Linking

| Time | Task |
|---|---|
| AM | `ingest_confluence.py` cho ADR/spec/retro pages liên quan mobile work |
| PM | `link.py` — match Jira key trong MR title/branch + Confluence body |
| EOD | Spot-check 20 random links → accuracy ≥ 80% |

### Day 3 — Scoring

| Time | Task |
|---|---|
| AM | Implement composite score formula cho `mobile-dev` (xem [validation.md](validation.md) cũ — đã merge vào breakdown logic dưới) |
| PM | Run `score.py`, inspect distribution, tune threshold để top quartile có 30–60 artifacts |
| EOD | `SELECT * FROM artifacts a JOIN scores s ON s.artifact_id=a.id WHERE s.score >= threshold ORDER BY score DESC LIMIT 30` → đọc tay 5–10 cái → confirm "đây là MR/spec tốt" |

### Day 4 — Extract

| Time | Task |
|---|---|
| AM | Viết `prompts/extract.system.md` + `extract.user.md`, test với 3 artifacts |
| PM | Run `extract.py` cho top 30–50 artifacts, validate JSON schema |
| EOD | Đọc 10 random extractions → confirm hợp lý, không hallucinate |

### Day 5 — Cluster (manual)

| Time | Task |
|---|---|
| AM | Đọc tất cả extractions, list theme nổi (state-management, navigation, testing, offline-data, platform-integration, ...) |
| PM | `cluster.py` — interactive script: hiển thị extraction, gõ cluster name → save vào `clusters` table |
| EOD | 4–6 clusters identified, mỗi cluster có ≥ 5 extractions |

**Friday demo (self)**: SQLite có data đủ, top quartile sensible, clusters defined.
Nếu < 4 clusters → mở rộng window 90→120d hoặc lower threshold.

---

## Tuần 2 — Synthesize + Validate

### Day 6 — Synthesize

| Time | Task |
|---|---|
| AM | Viết `prompts/synthesize.system.md` với citation enforcement strict |
| PM | Run `synthesize.py` cho từng cluster → output `packs/<role>/v0.1/skills/*.md` |
| EOD | Đọc qua 1 module, kiểm citation manually |

### Day 7 — Validate (citation + size) + Manifest

| Time | Task |
|---|---|
| AM | `validate.py` — check mọi rule có `[src: ...]`, module size < 3000 tokens, total pack < 20k tokens |
| AM | Reject + regenerate modules fail validation |
| PM | Hand-author `manifest.md` với hard rules từ aggregated review comments / retro action items |
| EOD | `pack.yaml` filled, pack v0.1 frozen, git tag |

### Day 8 — Validation V1 + V2 (parallel)

| Time | Task |
|---|---|
| AM | **V1**: Send pack tới 2 senior reviewer + rubric, async (cho họ 24h) |
| PM | **V2**: Chuẩn bị 5 tasks + generate A/B outputs (no-pack vs with-pack) |
| EOD | Send V2 packets tới 3 judges (cho họ 24h) |

### Day 9 — Self-use (V3) + collect V1/V2 results

| Time | Task |
|---|---|
| AM | Bạn dùng pack trên 2 task thật, log vào `self_use_log.md` |
| PM | Collect V1 ratings + V2 judgments, compute scores |
| EOD | 3 task tự use trong tuần này thì đủ rồi (V3 cần 5 task, có thể continue Day 10) |

### Day 10 — Report + Decision

| Time | Task |
|---|---|
| AM | Hoàn thành 2 task self-use cuối, finalize V3 log |
| AM | Compile `validation/mvp_report.md` |
| PM | 30-min stakeholder meeting: present results + recommendation |
| EOD | Decision logged: Phase 2 / Iterate / Pivot / Stop |

---

## Resource

| Item | Cost |
|---|---|
| Person | 0.5 FTE × 2 tuần = ~5 actual coding days + 2 days validation/admin |
| Reviewer (V1) | 2 × 30 min = **1 hour** |
| Judge (V2) | 3 × 20 min = **1 hour** |
| LLM API | ~**$50–100** (60–90d data, ~50 extracts × ~3k tokens + ~6 synthesizes × ~10k tokens) |
| Infra | **$0** |
| **Total** | **~$100, ~7 person-days, ~2 hours stakeholder time** |

---

## Critical path

```
Day 0 (setup) → Day 1-2 (ingest) → Day 3 (score) → Day 4 (extract)
                                                          ↓
Day 10 (decision) ← Day 8-9 (validate) ← Day 6-7 (synthesize) ← Day 5 (cluster)
```

**Bottleneck nguy hiểm nhất**: Day 5 (cluster). Nếu extractions không cluster
được rõ → có thể signal là data chưa đủ giàu hoặc role chọn sai. Không cố ép.

---

## Definition of done (MVP)

- [ ] `make all ROLE=<chọn>` chạy end-to-end ok trên laptop sạch
- [ ] Pack v0.1 commit vào repo: manifest + 3–5 modules + pack.yaml
- [ ] Validation report `validation/mvp_report.md` viết xong
- [ ] V1, V2, V3 raw data files trong `validation/`
- [ ] Decision meeting đã họp + decision logged
- [ ] Repo có README giải thích reproduce trong < 30 phút setup

---

## Buffer + cắt scope nếu chậm

Plan này giả định "happy path". Nếu chậm:

| Slip | Cắt |
|---|---|
| Day 1-2 ingest chậm | Giảm window 90→60d |
| Day 3 score nhiều noise | Giảm scope artifact nhưng vẫn giữ `mobile-dev` là role duy nhất |
| Day 5 cluster không ra | Mở rộng window hoặc đổi pilot repo, nhưng vẫn giữ `mobile-dev` |
| Day 7 module fail validation lặp | Hand-edit module thay vì auto-regenerate |
| Day 8-10 reviewer busy | Giảm V1 còn 1 reviewer; V2 còn 2 judges |

**Không** extend timeline. MVP > 2 tuần là dấu hiệu hypothesis có vấn đề, không
phải estimate sai.

---

## Anti-pattern khi chạy MVP

| Anti-pattern | Hệ quả |
|---|---|
| "Để tôi clean code chút trước khi…" | Day 10 không xong, không có decision |
| "Module này chưa hoàn hảo, redo lần nữa" | Tuần 2 hết mà chưa validate |
| "Tôi tự rate V1 vì đỡ phiền reviewer" | Bias, validation vô nghĩa |
| "V2 này hơi unfair với baseline, để tôi tweak prompt" | P-hacking |
| "Pack chưa pass V3 nhưng tôi feel nó tốt" | Decision không evidence-based |

MVP quality = **honest evidence**, không phải **pretty pack**.
