# Distill MVP

> **Mục tiêu**: Trong **2 tuần** chứng minh local rằng pipeline distill từ
> Confluence/Jira/GitLab tạo ra skill pack có ích — đủ để quyết định có scale
> ra team hay không.
>
> Đây là **MVP** của project Distill — chạy local trên 1 laptop, 1 person.
> Không có "MVP team-wide" riêng; nếu MVP pass, bước tiếp theo là **Phase 2 — team rollout**.
>
> **Stack**: Python + SQLite + LLM API. Không Postgres, không cron, không VM.
> Chạy hết trên 1 laptop.

---

## Cấu trúc tài liệu

| File | Nội dung | Đọc khi |
|---|---|---|
| [scope.md](scope.md) | Phạm vi MVP, decision gate, 1 role focus | Bắt đầu |
| [architecture.md](architecture.md) | Stack local: SQLite + scripts + Makefile | Trước khi code |
| [skill-pack-spec.md](skill-pack-spec.md) | Output spec — pack structure cho role | Khi build distill pipeline |
| [implementation.md](implementation.md) | Code-level implementation (schemas, prompts, scripts) | Khi viết code từng phase |
| [validation.md](validation.md) | 3 validation methods nhẹ (no formal A/B) | Cuối tuần 2 |
| [plan.md](plan.md) | 10 dev-days breakdown | Hàng ngày |

---

## Nguyên tắc MVP

1. **Local-only** — SQLite + filesystem, không cloud infra
2. **1 person, 1 role** — không phân tán effort, chọn role có nhiều data
3. **Manual-friendly** — clustering bằng tay, review bằng mắt là OK
4. **Throwaway-OK** — code MVP không cần production quality, chỉ cần reproducible
5. **Evidence > opinion** — dù validation nhẹ, vẫn phải có data, không "feels good"
6. **Provenance bắt buộc** — mọi claim trong pack phải cite source

---

## Decision gate sau MVP

Cuối tuần 2:
- ✅ Pack pass ≥ 2/3 validation methods → propose Phase 2 (team rollout)
- ⚠️ 1/3 pass → iterate MVP 1 tuần
- ❌ 0/3 pass → pivot data sources hoặc abandon hypothesis

Phase 2 (team rollout) plan sẽ tham khảo lại pattern trong tài liệu này, mở rộng
storage thành Postgres + cron + Confluence/Claude Project distribution.

---

## Quan hệ với tài liệu gốc

| Tài liệu | Liên hệ |
|---|---|
| [`../idea.md`](../idea.md) | Vision. MVP test cốt lõi của vision. |
| [`../architecture.md`](../architecture.md) | Full target architecture (sau Phase 2). MVP implement ~10% của cái đó. |
| [`../skill-pack.md`](../skill-pack.md) | Pack design canonical. MVP follow nhưng bỏ `references/` + vector retrieval + auto pack PR workflow. |

---

## Status

🟡 **Design phase**. Implementation chưa bắt đầu.

Next action: review `scope.md` + `plan.md`, chọn role (dev hoặc BA), bắt đầu Day 1.
