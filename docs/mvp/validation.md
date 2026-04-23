# Validation — MVP

> 3 validation methods nhẹ thay cho A/B formal. Tổng thời gian: **2–3 ngày**.
> Đủ rigor để decide có scale ra Phase 2 (team rollout) hay không.

---

## Tại sao không A/B formal ở MVP?

A/B treatment vs control cần ≥ 10 người trong 2 tuần để có signal đáng tin.
Quá đắt cho MVP. MVP chỉ cần biết **pack có chứa giá trị thật hay không** —
không cần biết "team-wide adoption sẽ ra sao" (đó là việc của Phase 2).

3 validation methods dưới đây trade-off rigor lấy speed, nhưng vẫn evidence-based.

---

## V1 — Expert Reviewer Rating (1 ngày)

**Hỏi**: "Pack này có đủ tốt để onboard new hire không?"

### Setup

- Mời **2 senior** trong role đó (senior dev nếu pack là dev, lead BA nếu là BA)
- Mỗi reviewer dành 30 phút đọc qua: manifest + 3–5 modules
- Cho họ rubric (bên dưới), tránh gut-feel rating

### Rubric (1–5 mỗi câu, ẩn danh nếu được)

| # | Câu hỏi | Anchor 1 | Anchor 5 |
|---|---|---|---|
| R1 | Hard rules trong manifest có phản ánh đúng convention team? | Sai/lạc | Đúng 100%, không thiếu |
| R2 | Patterns trong modules có actionable không? | Generic, sách vở | Specific, áp dụng được ngay |
| R3 | Pack có miss pattern quan trọng nào không? | Miss nhiều thứ critical | Cover được đủ patterns |
| R4 | Citation đầy đủ và trace được không? | Nhiều claim không có nguồn | Mọi claim cite được |
| R5 | Bạn có dùng pack này onboard new hire không? | Tuyệt đối không | Có, ngay lập tức |

### Pass threshold

- Điểm trung bình tất cả câu × tất cả reviewer ≥ **4.0/5**
- Không có câu nào ≤ 2 từ bất kỳ reviewer

### Anti-cheating

- Đừng giải thích bias trước khi review
- Đừng có mặt khi họ rate
- Reviewer có quyền nói "pack vô dụng" — phải accept feedback đó

### Cost
2 người × 30 phút = **1 hour total**.

---

## V2 — Blind Taste Test (1 ngày)

**Hỏi**: "Output AI có pack có thực sự tốt hơn không pack — khi judge không
biết cái nào là cái nào?"

### Setup

1. Chọn **5 task realistic** từ backlog (3 cũ đã done + 2 sắp làm)
   - Dev: "implement endpoint X", "viết test cho module Y", "review MR Z"
   - BA: "viết spec cho feature X", "draft AC cho story Y", "viết retro X"

2. Cho mỗi task, generate **2 outputs**:
   - **A**: AI (Claude/ChatGPT) prompt thường, không pack
   - **B**: AI cùng prompt + pack v0.1 inject vào system

3. Random A/B order per task (đừng luôn A-trước-B)

4. Chuẩn bị document: "Task X — Option 1 vs Option 2", **không nói cái nào là cái nào**

### Judge

- 3 người (mix senior + mid level), không phải bạn
- Mỗi người chấm tất cả 5 task
- Mỗi task chọn 1 trong 3:
  - "Option 1 tốt hơn"
  - "Option 2 tốt hơn"
  - "Bằng nhau / khác nhau không đáng kể"
- Kèm 1 dòng lý do

### Pass threshold

```
win_rate = (số lần pack-injected wins) / (số lần có winner rõ ràng)
        = wins / (5 tasks × 3 judges - ties)
```

Pass nếu **win_rate ≥ 60%** (clear majority, không phải just-better-than-coin-flip).

### Sanity check

- Nếu tie ≥ 70% → pack không tạo difference đủ rõ → fail soft
- Nếu pack-injected lose ≥ 40% → pack có thể đang gây harm → fail hard

### Cost
3 judges × 20 phút = **1 hour total** + bạn 1–2 giờ chuẩn bị tasks.

---

## V3 — Self-Use Reality Check (5 ngày, parallel)

**Hỏi**: "Bản thân tôi dùng pack trong real work, có thấy ích lợi không?"

### Setup

- Tuần 2 (parallel với V1+V2), bạn dùng pack cho **5 task thật** trong work
- Mỗi task xong, log ngay vào `validation/self_use_log.md`

### Log format

```markdown
## Task 1 — 2026-04-XX
**Mô tả**: implement /api/orders/refund endpoint
**Pack modules loaded**: api-design.md, error-handling.md
**Verdict**: HELPED | NEUTRAL | HURT
**Vì sao**: [1–2 dòng]
**Pattern dùng được**: [list]
**Pattern miss / sai**: [list nếu có]
```

### Verdict definitions

| Verdict | Khi nào |
|---|---|
| **HELPED** | Pack rule/template áp dụng được, tiết kiệm thời gian thật, hoặc catch lỗi sớm |
| **NEUTRAL** | Pack load nhưng không tạo difference, hoặc bạn đã biết pattern đó |
| **HURT** | Pack nói sai, dẫn bạn đi nhầm hướng, phải undo |

### Pass threshold

- HELPED ≥ **3/5** (60%)
- HURT = **0**

### Honesty rules

- Đừng cherry-pick task dễ
- Đừng skip log task mà pack không help
- HURT = 1 cũng nên log + analyze (trace ngược tại sao pack có pattern sai)

### Cost
0 effort thêm — bạn đang làm task thật, chỉ thêm 5 phút log mỗi cái.

---

## Decision matrix (cuối tuần 2)

| V1 | V2 | V3 | Verdict |
|---|---|---|---|
| ✅ ≥4.0 | ✅ ≥60% | ✅ ≥60% HELPED | **3/3 — Strong go Phase 2** |
| ✅ | ✅ | ❌ | **2/3 — Go Phase 2**, nhưng improve module trigger |
| ✅ | ❌ | ✅ | **2/3 — Go Phase 2**, nhưng pack quality cao chưa generalizable |
| ❌ | ✅ | ✅ | **2/3 — Go Phase 2**, nhưng review reviewer set lại |
| ✅ | ❌ | ❌ | **1/3 — Iterate**: experts thích nhưng không actually useful |
| ❌ | ✅ | ❌ | **1/3 — Iterate**: chỉ test environment work |
| ❌ | ❌ | ✅ | **1/3 — Iterate**: only-you-like-it bias |
| ❌ | ❌ | ❌ | **0/3 — Pivot or stop**: hypothesis chưa được prove |

---

## Reporting

Cuối tuần 2, viết `validation/mvp_report.md`:

```markdown
# MVP Validation Report — Distill v0.1

## Summary
[1 paragraph: pass/fail outcome + recommendation]

## V1 — Expert Review
- Reviewers: [names]
- Scores: R1=X, R2=Y, R3=Z, R4=W, R5=V (avg)
- Notable feedback: [quotes]
- **Pass / Fail**: [✅/❌]

## V2 — Blind Taste Test
- Tasks: [5 mô tả ngắn]
- Win rate: pack X / no-pack Y / tie Z
- **Pass / Fail**: [✅/❌]

## V3 — Self-Use
- 5 task logs (full version trong self_use_log.md)
- HELPED: X, NEUTRAL: Y, HURT: Z
- **Pass / Fail**: [✅/❌]

## Recommendation
[ ] Go Phase 2 (team rollout) — full plan trong follow-up doc
[ ] Iterate MVP 1 tuần (target: improve V?)
[ ] Pivot data sources / role
[ ] Abandon hypothesis

## Lessons learned
- What worked
- What didn't
- What surprised us

## Cost actuals
- LLM API spent: $XX
- Person-days: X
- Calendar days: X
```

Stakeholder review trong meeting 30 phút end of week 2. Decision logged.

---

## Honesty checklist trước khi tuyên bố pass

- [ ] Reviewer của V1 không phải người đã đóng góp content (bias)
- [ ] V2 task có cả task pack được expect tốt + task neutral (không cherry-pick)
- [ ] V2 judge không biết cái nào là pack-injected (real blind)
- [ ] V3 log trung thực, có ghi cả failure
- [ ] Không có claim "pass" mà không có data file commit vào repo
