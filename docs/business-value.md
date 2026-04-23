# Distill — Bài toán kinh tế & Giá trị doanh nghiệp

> *"Distill không bán thêm một AI tool nữa — nó bán lớp tối ưu hoá trên các AI tool công ty đã trả tiền."*

**Related:** [idea.md](idea.md), [role-coverage.md](role-coverage.md), [architecture.md](architecture.md)

---

## 1. Chi phí đang "chảy máu" mà công ty không thấy

Khi công ty đã adopt AI coding assistant (Copilot, Cursor, Claude Code, ChatGPT Enterprise, ...), có 4 khoản chi phí ngầm mà CFO/CTO thường không đo được:

| Khoản lỗ ngầm | Bản chất | Cách Distill giảm |
|---|---|---|
| **Onboarding drag** | Dev mới cần 3–6 tháng để productive, lương vẫn trả đủ | Skill pack đẩy pattern của senior vào ngày đầu → rút còn vài tuần |
| **Senior turnover** | Khi senior nghỉ, tri thức đi theo, phải trả chi phí replace + retrain | Pattern của họ ở lại trong skill pack → giảm key-person risk |
| **AI subscription waste** | Trả $20–200/user/tháng nhưng 60–80% user dùng kém hiệu quả | Chuẩn hoá cách prompt → tăng ROI trên từng license |
| **Rework loop** | AI output kém → review nhiều vòng → bug production → hotfix | Pattern đã validate bởi PR merged → giảm tỉ lệ rework |

---

## 2. Công thức ROI

```
Annual Saving =
    (user_count × hours_saved_per_week × hourly_rate × 52)        // productivity
  + (reduced_onboarding_months × new_hires_per_year × hire_cost)  // onboarding
  + (avoided_senior_turnover_count × replacement_cost)            // retention
  + (AI_license_count × effective_utilization_gain)               // tool ROI
```

### Ví dụ minh hoạ — công ty 100 dev

| Nguồn tiết kiệm | Giả định | Giá trị / năm |
|---|---|---|
| Productivity | 2h/tuần/dev × $50/h × 100 dev × 52 tuần | **~$520K** |
| Onboarding | Rút từ 4 tháng → 2 tháng × 20 hires × $15K | **~$300K** |
| Retention | Giữ thêm 2 senior × $100K replacement cost | **~$200K** |
| **Tổng** | | **~$1M / năm** |

Payback thường dưới 6 tháng với team từ 50 dev trở lên.

---

## 3. Mô hình doanh thu (khi Distill là sản phẩm)

| Mô hình | Đối tượng | Giá tham khảo |
|---|---|---|
| **SaaS per-seat** | Startup, scale-up 10–500 người | $10–30/user/tháng |
| **Enterprise on-prem** | Bank, fintech, healthcare, gov | $50K–500K/năm |
| **Hybrid / Freemium** | Team nhỏ vào free → upsell khi scale | Free tier + paid tier |

Ví dụ ARR mô hình per-seat:
- Công ty 100 user × $20/tháng = **$24K/năm**
- Công ty 1,000 user × $20/tháng = **$240K/năm**
- Công ty 10,000 user × $20/tháng = **$2.4M/năm**

Mô hình on-prem phù hợp với khách hàng không cho data rời network — đây thường là deal value cao nhất.

---

## 4. Tại sao timing đang đúng

- **AI coding assistant đã $5B+ market** và đang tăng trưởng 2 con số/năm
- Các CTO bắt đầu hỏi: *"Tôi trả tiền cho Copilot/Cursor, ROI thực tế đo bằng gì?"* — Distill là câu trả lời
- Enterprise cần **AI governance & audit trail** cho compliance (SOC2, ISO, GDPR) → Distill có versioning + rollback sẵn
- Knowledge management thế hệ cũ (Notion, Confluence) đang bị đánh giá lại vì **tri thức chết** không auto-inject vào workflow

---

## 5. Positioning chiến lược

Distill không cạnh tranh với:
- ❌ AI coding assistant (Copilot, Cursor) — nó **nằm trên** các tool này
- ❌ Knowledge base (Notion, Confluence) — nó **executable**, không phải static docs
- ❌ Prompt library (PromptHub, ...) — nó **auto-learn**, không phải curated

Distill cạnh tranh trong category mới: **Enterprise AI Enablement Platform** — hạ tầng giúp công ty **đo, chuẩn hoá, và khuếch đại** giá trị AI đang dùng.

---

## 6. Câu chuyện bán cho từng stakeholder

| Stakeholder | Pain họ quan tâm | Distill pitch |
|---|---|---|
| **CEO** | ROI của AI, lợi thế cạnh tranh | "Biến AI license thành advantage có thể đo" |
| **CTO** | Code quality, dev productivity, onboarding | "Senior-level output từ ngày đầu của junior" |
| **CFO** | Chi phí AI subscription, TCO | "Tăng 2–3× hiệu quả trên mỗi license đã trả" |
| **CHRO** | Retention, onboarding cost, knowledge loss | "Tri thức không rời công ty khi người nghỉ" |
| **CISO** | Compliance, audit, data leak risk | "On-prem, versioned, audit-ready AI governance" |
| **Head of Eng** | Team velocity, consistency | "5 dev cùng task → 5 output nhất quán" |

---

## 7. Các giả định cần validate

Đây là những biến số quyết định bài toán kinh tế có đúng không — cần test ở Phase 1–2 của roadmap:

- Skill pack thật sự có **rút ngắn onboarding** đo được, không chỉ cảm tính?
- Quality signal (PR merged, review passed) có đủ **clean** để học không?
- Pattern distill ra có **generalize** giữa các dev khác nhau, hay quá personal?
- Adoption curve — dev có **thật sự để skill inject** hay disable?
- ROI có scale tuyến tính theo team size hay có threshold?

Xem thêm: [research/open-questions.md](research/open-questions.md) cho các câu hỏi mở chi tiết.

---

*Distill — biến AI từ chi phí thành lợi thế cạnh tranh đo được.*
