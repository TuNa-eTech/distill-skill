# Distill — Role Coverage Matrix

> Bảng tổng hợp các role trong doanh nghiệp có thể hưởng lợi từ Distill, giá trị tạo ra và KPI đo được.

**Related:** [idea.md](idea.md), [business-value.md](business-value.md), [research/multi-role-extension.md](research/multi-role-extension.md), [research/role-taxonomy.md](research/role-taxonomy.md)

---

## Nguyên lý

Distill áp dụng được cho **mọi role dùng AI để làm việc trí óc** — không bị giới hạn ở engineering. Điều kiện cần:

1. Có **digital artifact** để capture (code, doc, ticket, email, spreadsheet, chat, ...)
2. Có **quality signal** để chấm điểm pattern (PR merged, deal closed, CSAT cao, báo cáo được duyệt, ...)
3. Có **role peers** đủ để aggregation có ý nghĩa thống kê

Khi 3 điều kiện đủ, skill pack cho role đó là hoàn toàn khả thi.

---

## 1. Engineering & Technical

| Role | Skill pack học được | Giá trị tạo ra | KPI đo được |
|---|---|---|---|
| **Backend Engineer** | API design pattern, DB migration, error handling, testing convention | Code nhất quán, ít regression, onboard nhanh | PR review cycle, bug rate, time-to-first-commit |
| **Frontend Engineer** | Component pattern, state mgmt, accessibility, perf optimization | UI đồng bộ, giảm design drift | Lighthouse score, component reuse rate |
| **Mobile Engineer** | Platform-specific pattern (iOS/Android), release checklist | Release ổn định, ít crash production | Crash-free rate, release cadence |
| **DevOps / SRE** | IaC pattern, incident runbook, alerting heuristic | MTTR giảm, on-call đỡ stress | MTTR, incident count, alert noise ratio |
| **Data Engineer** | Pipeline pattern, schema evolution, data quality check | Pipeline ít break, data trust cao hơn | Pipeline SLA, data incident count |
| **ML / AI Engineer** | Model eval pattern, prompt engineering, experiment tracking | Model iteration nhanh, reproducible | Time-to-prod, model regression rate |
| **QA / Test Engineer** | Test case generation, edge case catalog, regression pattern | Coverage cao hơn, bug leak thấp | Escaped defect rate, test creation time |
| **Security Engineer** | Threat modeling, vuln triage, secure code review | Vuln phát hiện sớm, compliance đạt | MTTD vulnerability, audit pass rate |

---

## 2. Product & Design

| Role | Skill pack học được | Giá trị tạo ra | KPI đo được |
|---|---|---|---|
| **Product Manager** | PRD structure, user research synthesis, prioritization framework | Spec rõ ràng, giảm rework với eng | Spec clarity score, eng clarification count |
| **Product Designer** | Design system convention, critique pattern, interaction spec | Design đồng bộ brand, handoff mượt | Design-to-dev iteration, component consistency |
| **UX Researcher** | Interview guide, synthesis framework, insight format | Insight chất lượng đồng đều | Research-to-decision time, insight adoption |
| **Design Systems Lead** | Token pattern, doc convention, migration playbook | Hệ thống lan toả nhanh | Token adoption rate, design debt |

---

## 3. Go-to-Market

| Role | Skill pack học được | Giá trị tạo ra | KPI đo được |
|---|---|---|---|
| **Marketing Content** | Tone of voice, SEO pattern, content structure đã perform | Content chuẩn brand, SEO tốt hơn | Organic traffic, engagement rate |
| **Growth Marketer** | Experiment framework, funnel analysis, channel pattern | Test chất lượng cao, insight học nhanh | CAC, experiment velocity |
| **Product Marketer** | Positioning framework, launch playbook, competitor teardown | Launch nhất quán, message rõ | Launch NPS, sales enablement usage |
| **SDR / BDR** | Outreach template, discovery question, objection catalog | Pipeline chất lượng, meeting booked rate cao | Reply rate, meeting-to-opp rate |
| **AE / Account Exec** | Discovery framework, demo script, negotiation pattern | Deal velocity, win rate cao hơn | Win rate, cycle time, ACV |
| **Customer Success** | Onboarding playbook, QBR structure, churn signal detection | Retention cao, expansion tốt | NRR, churn rate, time-to-value |
| **Customer Support** | Response template theo persona, escalation rule, tone | CSAT cao, handle time ngắn | CSAT, first-response time, deflection rate |

---

## 4. Operations & Business

| Role | Skill pack học được | Giá trị tạo ra | KPI đo được |
|---|---|---|---|
| **Data Analyst** | SQL pattern theo domain, viz convention, insight framing | Analysis nhất quán, actionable hơn | Time-to-insight, report reuse |
| **Business Analyst** | Process mapping, requirement doc, stakeholder comms | Scope rõ, giảm misalignment | Project on-time rate |
| **Finance / FP&A** | Forecast model pattern, variance analysis, board deck format | Số liệu đáng tin, close nhanh | Close cycle time, forecast accuracy |
| **Legal / Compliance** | Contract review heuristic, risk flag pattern, redline convention | Review nhanh, consistent | Review turnaround, risk flag recall |
| **HR / People Ops** | Policy explainer, screening pattern, feedback framework | Experience nhất quán cho nhân viên | eNPS, time-to-hire |
| **Recruiter** | JD writing, screening question, candidate comms | Pipeline quality cao, bias thấp | Offer accept rate, diversity metric |
| **Executive Assistant** | Calendar heuristic, meeting prep, comms drafting | Exec productivity tăng | Exec time saved |
| **Ops Manager** | Vendor eval, process doc, SOP writing | SOP chuẩn, ít thất thoát tri thức | Process compliance rate |

---

## 5. Leadership

| Role | Skill pack học được | Giá trị tạo ra | KPI đo được |
|---|---|---|---|
| **Engineering Manager** | 1:1 framework, perf review, scoping playbook | Team throughput, ít attrition | Team eNPS, delivery predictability |
| **Product Leader** | Roadmap framework, stakeholder update, trade-off doc | Strategy clarity, alignment cao | Roadmap hit rate, exec trust |
| **C-Suite / Founder** | Board update, investor comm, strategic memo | Comms sắc, decision nhanh | Board feedback quality |

---

## 4 giá trị cốt lõi xuyên suốt mọi role

Bất kể role nào, Distill đều tạo ra cùng một bộ giá trị:

1. **Onboarding compression** — rút 40–60% thời gian để nhân sự mới đạt productive
2. **Knowledge retention** — tri thức không rời công ty khi nhân sự nghỉ việc
3. **Quality consistency** — output đồng đều, giảm variance giữa cá nhân
4. **AI ROI amplification** — mỗi license AI (Copilot, Cursor, ChatGPT Enterprise, ...) tạo ra nhiều giá trị hơn

---

## Network effect giữa các skill pack

Các role không làm việc cô lập. Khi nhiều skill pack cùng tồn tại trong một công ty, giá trị **nhân lên** qua liên thông:

- PM viết PRD theo format mà **Eng pack biết cách parse** → giảm clarification
- Design pack biết **constraint của Eng pack** → mockup khả thi hơn
- Support pack feedback bug pattern về **Eng pack** → Eng học được edge case thật từ user
- Sales pack học **positioning từ PMM pack** → pitch nhất quán

→ Tri thức tổ chức trở thành **hạ tầng chạy nền**, không còn nằm chết trong Notion/Confluence.

---

## Chiến lược triển khai (Land & Expand)

Không nên deploy cho tất cả role cùng lúc. Playbook đề xuất:

| Giai đoạn | Mục tiêu | Role | Lý do |
|---|---|---|---|
| **Land** | 1 beachhead với ROI đo được | Engineering | Quality signal rõ (PR, commit), log có cấu trúc |
| **Expand (gần)** | Role đã tương tác nhiều với Eng | PM, Designer, QA | Đã có network effect với Eng pack |
| **Expand (xa)** | Role có pattern nhưng signal khó hơn | Sales, Support, Marketing | Cần custom quality signal (deal closed, CSAT, ...) |
| **Company-wide** | Toàn doanh nghiệp | Mọi role dùng AI | C-suite đã thấy số, muốn scale |

Đây là playbook giống Slack, Notion, Linear — vào từ 1 team, lan ra toàn công ty.

---

## Điều kiện để một role mới được support

Checklist quyết định có làm skill pack cho role X không:

- [ ] Có ≥ 5 người cùng role để aggregation có ý nghĩa?
- [ ] Có digital artifact để capture (không phải thao tác vật lý)?
- [ ] Có quality signal đo được (binary hoặc có thang)?
- [ ] Có peer feedback loop (reviewer, approver, customer)?
- [ ] Output của role này có tái sử dụng được qua AI không?

Nếu ≥ 4/5 câu trả lời là có → role này khả thi. Xem thêm [research/role-taxonomy.md](research/role-taxonomy.md) cho framework phân loại chi tiết.

---

*Distill — biến tri thức tổ chức thành hạ tầng, không phải document chết.*
