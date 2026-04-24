# Artifact Representation for LLM Input

> Mục tiêu của tài liệu này: chốt cách biểu diễn artifact cho LLM trong MVP
> trước khi tối ưu pipeline `extract`.

---

## Vì sao cần tài liệu này

Hiện tại bước extract vẫn feed trực tiếp:

- metadata artifact dạng JSON
- blob text thô đã redact nhưng có thể bị truncate

Xem:

- [`src/distill_evolve/extract.py`](../../src/distill_evolve/extract.py)
- [`prompts/extract.user.md`](../../prompts/extract.user.md)

Thiết kế đó đủ để MVP chạy end-to-end, nhưng có 4 hạn chế rõ:

1. **Token efficiency kém** — raw JSON và blob thô chứa nhiều noise không giúp extraction.
2. **Signal bị cắt sớm** — truncate theo ký tự đầu dễ bỏ sót phần quan trọng nằm phía sau.
3. **Source heterogeneity** — GitLab, Jira, Confluence có shape rất khác nhau, model phải tự học lại cấu trúc mỗi lần.
4. **Format confusion** — chưa có rule rõ ràng lúc nào nên dùng JSON, JSONL, Markdown, hay TOON.

Tài liệu này chốt baseline để mọi optimize tiếp theo đi cùng một hướng.

---

## Decision Summary

**Quyết định cho giai đoạn hiện tại:**

- Giữ **raw JSON** làm source of truth cho ingest, audit, replay, trace.
- Dùng một lớp **canonical artifact card** làm input chính cho LLM extraction.
- Dùng **JSONL** cho append-only logs và chunk store.
- Dùng **TOON** chọn lọc cho các block tabular đồng nhất, không dùng để thay toàn bộ blob.
- Không migrate dữ liệu lịch sử sang format mới ở bước đầu tiên.

Nói ngắn gọn:

**`raw JSON -> canonical artifact card -> LLM`**

và

**`JSONL / TOON` chỉ là format phụ theo đúng bài toán của từng lớp.**

---

## Representation Layers

| Layer | Format | Vai trò | Ghi chú |
|---|---|---|---|
| Source of truth | `.json` | Lưu payload raw đã redact | Không thay |
| Index / graph | SQLite | Metadata, links, scores, extractions | Đã có |
| LLM input | Markdown + frontmatter | Input chính cho `extract` | Sẽ thêm |
| Chunk / retrieval | `.jsonl` | Append-only chunks, evidence cards | Optional bước đầu |
| Tabular sub-blocks | TOON | Nén các mảng object đồng nhất | Chỉ dùng chọn lọc |

---

## Format Rules

### 1. Raw JSON

**Dùng cho:**

- `data/blobs/**/*.json`
- mọi payload ingest từ GitLab, Jira, Confluence
- trace và replay

**Lý do giữ lại:**

- lossless
- machine-friendly
- dễ debug theo source gốc
- không làm mất provenance

**Không dùng raw JSON làm primary prompt input** trừ khi đang debug extractor.

### 2. Canonical Artifact Card

Đây là format chính model nên đọc.

Card phải:

- ngắn hơn raw blob nhiều
- thống nhất giữa các source
- ưu tiên signal, không ưu tiên completeness
- dễ cite ngược về artifact gốc

**Format khuyến nghị:** YAML frontmatter nhỏ + Markdown sections.

Ví dụ shape:

```md
---
artifact_id: 2188
kind: gitlab_mr
external_id: 2188!842
updated_at: 2026-04-24T03:10:09Z
jira_keys: [APP-123]
linked_artifacts: [APP-123, page:274698698]
---

# Summary
Integrate Adjust tracking events into vaccine suggestion flow.

## Intent
Track search, category view, and consultation events in the vaccine flow.

## Key Changes
- Added `searchProduct` tracking on keyword change.
- Added one-time `viewCategoryList` tracking after first successful load.
- Added consultation request tracking in the list widget.

## Important Files
- `lib/.../vaccine_suggestion_page2.dart`
- `lib/.../vaccine_list_widget.dart`

## Decisions / Patterns
- Track category view only once per screen load.
- Keep analytics calls near the user interaction that triggers them.

## Evidence Snippets
1. `bool _hasTrackedViewCategory = false`
2. `STCDTAdjust.searchProduct(...)`
3. `STCDTAdjust.viewCategoryList(...)`
```

### 3. JSONL

**Dùng cho:**

- append-only logs như `extract_failures.jsonl`
- chunk store cho retrieval
- evidence cards đã normalize

**Không dùng JSONL cho:**

- raw source of truth
- prompt input chính của artifact hoàn chỉnh

JSONL mạnh khi cần:

- stream / append
- grep nhanh
- process từng record độc lập
- lưu các chunk nhỏ, đồng nhất

### 4. TOON

**Dùng cho:**

- các block tabular có field đồng nhất giữa các item

Ví dụ:

- `changed_files`
- `jira_events`
- `linked_artifacts`
- `review_comment_summaries`
- `evidence_cards`

Ví dụ block TOON nhúng trong artifact card:

```text
jira_events[3]{event_kind,from_value,to_value,occurred_at}:
  status_change,To Do,In Progress,2026-01-02T10:00:00Z
  scope_change,old summary,new summary,2026-01-05T08:30:00Z
  status_change,In Progress,Done,2026-01-08T15:00:00Z
```

**Không dùng TOON cho:**

- full GitLab/Jira/Confluence blob thô
- nested objects nhiều tầng
- narrative text dài
- source có shape không ổn định

---

## Per-Source Canonicalization

### GitLab MR

Giữ lại:

- project path
- title
- state
- source / target branch
- labels
- author
- changed files
- review / discussion highlights
- commit summary nếu hữu ích
- 3–8 evidence snippets từ diff hoặc discussion

Bỏ hoặc hạ ưu tiên:

- avatar URLs
- web URLs
- full system notes không liên quan
- metadata lặp lại
- raw diff toàn bộ nếu quá dài

### Jira Issue

Giữ lại:

- key
- summary
- issue type
- current status
- labels / components
- lifecycle events
- scope-change highlights
- comments summary
- linked artifacts

Bỏ hoặc hạ ưu tiên:

- field noise không giúp hiểu pattern
- full changelog nếu không tạo signal

### Confluence Page

Giữ lại:

- page title
- space
- version / updated_at
- short abstract
- headings quan trọng
- decisions
- action items
- referenced Jira keys

Bỏ hoặc hạ ưu tiên:

- HTML/raw storage noise
- presentational markup
- duplicated navigation text

---

## Immediate Recommendation for the Optimization Pass

### Phase 1

Làm ngay:

1. Thêm `canonicalize_gitlab_mr()`, `canonicalize_jira_issue()`, `canonicalize_confluence_page()`
2. Tạo artifact card **on the fly** trong `extract.py`
3. Đổi prompt extract để nhận `artifact_card` thay cho `blob_text` thô
4. Giữ `blob_path` để trace/debug như hiện tại

**Không làm ngay trong bước đầu:**

- persist một thư mục `data/llm_views/`
- vector DB
- retrieval runtime đầy đủ
- chuyển toàn bộ pipeline sang TOON

### Phase 2

Chỉ làm nếu Phase 1 cho kết quả tốt:

- persist `artifact_card` để review/debug
- tạo `data/chunks/*.jsonl`
- thêm retrieval cho long-tail references
- đo lợi ích của TOON trên từng source-specific block

---

## Evaluation Criteria

Optimize pass phải được đo bằng output thực, không chỉ bằng cảm giác prompt “đẹp hơn”.

Các chỉ số tối thiểu:

- token count của input vào `extract`
- `processed / inserted / failed / skipped`
- chất lượng extraction khi spot-check tay
- độ dễ trace ngược về raw artifact
- effort để debug khi output sai

Nếu token giảm nhưng extraction mơ hồ hơn hoặc trace khó hơn, optimize đó không đạt.

---

## Explicit Non-Goals

- Không thay SQLite.
- Không thay raw blob storage bằng TOON hoặc JSONL.
- Không build RAG system đầy đủ trong pass đầu.
- Không tối ưu cho mọi role cùng lúc.
- Không chase benchmark format trước khi chuẩn hóa content.

---

## Working Rule

Khi có nghi ngờ giữa “format nhỏ hơn” và “content rõ hơn”, ưu tiên:

**content rõ hơn cho model > format nhỏ hơn trên giấy**

Trong Distill hiện tại, chất lượng canonicalization quan trọng hơn việc tranh luận giữa JSON, JSONL, Markdown hay TOON ở mức lý thuyết.
