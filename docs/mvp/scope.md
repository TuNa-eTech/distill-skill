# Scope — MVP

> MVP = local POC. Không có MVP version riêng cho team — bước team là Phase 2.

## Mục tiêu (1 câu)

Chứng minh trong **2 tuần** rằng pipeline distill từ Confluence/Jira/GitLab,
chạy 100% local trên 1 laptop, tạo ra **1 skill pack v0.1 có ích đủ để
justify đầu tư Phase 2 (team rollout)**.

---

## Hypothesis cần test

> Lấy 60–90 ngày data từ 3 hệ thống → score → cluster → LLM synthesize có
> citation, kết quả pack v0.1 đủ tốt để:
> 1. Senior reviewer rate ≥ 4/5 "would onboard new hire with this"
> 2. Pack-injected AI output thắng baseline ≥ 60% trong blind test
> 3. Bản thân tôi dùng pack thấy có ích ≥ 60% trong real tasks

Nếu fail cả 3 → hypothesis sai, không phải implementation sai. Stop hoặc pivot.

---

## In scope

- [x] **1 role duy nhất** — pilot đã chốt là **Mobile Dev**, không chạy cả 2 role trong MVP
- [x] **1 person execute** (tech lead hoặc bạn tự làm)
- [x] **1 product/repo** với data đủ giàu (≥ 50 closed tickets / 30 MRs / 20 specs trong 90 ngày)
- [x] Local stack: Python + SQLite + LLM API
- [x] Manual cluster (đọc bằng mắt, group thủ công)
- [x] Pack output dạng file local (không sync Confluence ở MVP)
- [x] 3 validation methods nhẹ (xem [validation.md](validation.md))

---

## Out of scope (MVP)

Đẩy hết sang Phase 2 (team rollout):

- ❌ **Cả 2 roles cùng lúc** — chọn 1 để focus
- ❌ **Postgres / S3** — SQLite + filesystem đủ
- ❌ **Cron / scheduled jobs** — chạy `make` thủ công
- ❌ **Confluence / Claude Project sync** — pack đọc local file là đủ test
- ❌ **A/B treatment vs control formal** — validation lightweight thay
- ❌ **Pack PR review workflow** — bạn tự review, commit thẳng
- ❌ **CHANGELOG, versioning chỉn chu** — tag v0.1, đủ
- ❌ **Multi-team / multi-repo** — 1 repo
- ❌ **Real-time** — batch run khi cần
- ❌ **On-call / monitoring** — bạn ngồi xem console output

---

## Pilot role đã chốt cho MVP

Role pilot hiện tại là **Mobile Dev**.

Ý nghĩa của quyết định này:

- MVP chỉ build, run, validate pack `mobile-dev`
- `business-analyst` giữ ở mức reference docs/paper-spec cho phase sau
- Mọi ví dụ vận hành trong tài liệu MVP từ đây mặc định dùng `mobile-dev`

---

## Success criteria (decision gate cuối tuần 2)

| Validation | Threshold |
|---|---|
| **V1**: Reviewer rating (1–2 senior) | avg ≥ **4.0/5** |
| **V2**: Blind taste test win rate | pack-injected wins ≥ **60%** |
| **V3**: Self-use reality check | ≥ **60%** "đã giúp" trên 5 real tasks |

Decision matrix:

| Pass count | Action |
|---|---|
| 3/3 | ✅ Strong signal → đề xuất Phase 2 với confidence cao |
| 2/3 | ✅ Đủ tin → đề xuất Phase 2 |
| 1/3 | ⚠️ Iterate MVP thêm 1 tuần (fix bottleneck rõ nhất) |
| 0/3 | ❌ Pivot: đổi data source / đổi pilot repo / abandon |

Chi tiết measure trong [validation.md](validation.md).

---

## Anti-goals

Đừng tối ưu cho:

- **Code quality** — MVP code throwaway. Pylint score 5/10 là OK miễn reproducible
- **Test coverage** — chỉ test 1–2 critical functions (citation validator, redactor)
- **Performance** — 90 ngày data ingest 1h cũng được
- **Pretty output** — pack là markdown file, không cần render đẹp
- **Coverage rộng** — 3 modules đúng > 8 modules tạm
- **Auto-everything** — manual là OK ở MVP

---

## Assumption cần verify Day 1

| # | Assumption | Cách verify |
|---|---|---|
| A1 | GitLab personal token đọc được MR + discussions | `curl` test |
| A2 | Jira account đọc được project pilot | API test |
| A3 | Confluence / wiki có đủ mobile specs, ADR, retro pages linked tới pilot work | CQL query |
| A4 | Mobile repo pilot có ≥ 30 merged MRs / 90d | GitLab API |
| A5 | LLM API key + budget OK | `anthropic` SDK test |

Nếu A1–A2 fail → MVP blocked. Nếu A3 hoặc A4 fail → re-scope data window hoặc pilot repo, không đổi khỏi `mobile-dev` trong MVP này.

---

## Resource

| Item | Estimate |
|---|---|
| Effort | **0.5 FTE × 2 tuần** ≈ 5 dev-days actual coding |
| Reviewer time (V1) | 2 senior × 30 phút = 1 hour total |
| Blind test (V2) | 3 colleagues × 20 phút = 1 hour total |
| LLM cost | **~$50–100** (small batch, 60–90d data) |
| Infra cost | **$0** (local) |
| **Tổng** | **~$100, ~6 person-days** |

So với Phase 2 team rollout ước tính ($1k + 30+ person-days): MVP nhẹ hơn **5–10×**,
đủ để biết có nên đầu tư cái lớn hay không.
