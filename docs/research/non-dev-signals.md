# Non-Dev Quality Signals — Research Notes

> Dev có "PR merged" — signal vàng. Non-dev có gì tương đương?

**Status:** Research — đây có thể là rủi ro lớn nhất của Distill khi mở rộng ra non-dev.
**Related:** [architecture.md](../architecture.md), [multi-role-extension.md](multi-role-extension.md), [tacit-knowledge-capture.md](tacit-knowledge-capture.md)

---

## Vấn đề

Distill học từ **quality interactions**, không học từ mọi interactions. Với dev, quality được định nghĩa bằng signal khách quan có sẵn:

- PR merged → pattern trong session đó là "tốt"
- PR rejected → pattern là "xấu"
- Commit reverted → pattern là "rất xấu"
- Review approved → pattern là "tốt"
- Test passed → pattern có khả năng "tốt"

Non-dev role **không có** các signal này. Nếu không giải quyết được vấn đề này, pipeline Aggregate sẽ aggregate cả pattern tốt và pattern xấu như nhau → output là trung bình cộng, không phải top performance. Đó là thất bại hoàn toàn của ý tưởng gốc.

Tài liệu này map từng role → source có thể lấy → signal có thể derive → độ mạnh của signal.

---

## Signal taxonomy

Trước khi đi vào từng role, phân loại signal theo 2 trục:

### Trục 1 — Objectivity (khách quan)

| Loại | Mô tả | Ví dụ (dev) |
|---|---|---|
| **Ground-truth** | Trạng thái thực tế, không bàn cãi | Commit reverted |
| **Consensus** | Nhiều người đồng ý | Review approved |
| **Auto-measured** | Tool đo được | Test coverage |
| **Self-reported** | Người đó tự claim | "Task done" |
| **Inferred** | LLM đoán từ behavior | "Code looks clean" |

Từ trên xuống dưới: độ mạnh signal giảm dần. Dev có nhiều signal ở top; non-dev thường chỉ có signal ở middle/bottom.

### Trục 2 — Latency (độ trễ)

| Loại | Mô tả | Ví dụ |
|---|---|---|
| **Immediate** | Trong cùng session | Test pass |
| **Short (hours–days)** | Cùng day hoặc tuần | PR merged |
| **Medium (weeks)** | Sprint-level | Story delivered |
| **Long (months)** | Quarter-level | Feature hit metric |
| **Very long (years)** | Sau nhiều năm | Career outcome |

Dev hưởng lợi vì có nhiều signal ở Immediate/Short. Non-dev nhiều signal ở Medium/Long → aggregation cần chờ lâu hơn → loop feedback chậm hơn.

---

## Role 1 — Business Analyst

### Source có sẵn
- Confluence / Notion page history
- Jira issue lifecycle
- Meeting transcript (nếu công ty record họp)
- Email thread với stakeholder
- Figma / Miro board history

### Signal khả thi

| Signal | Source | Objectivity | Latency | Mạnh / yếu |
|---|---|---|---|---|
| Story accepted by dev first time (không cần refine) | Jira transition log | Consensus | Short | **Strong positive** |
| Story needs N rounds of refinement | Jira comment count | Consensus | Short | Negative (scaled by N) |
| UAT passed no defect | Jira UAT status | Ground-truth | Medium | **Strong positive** |
| Post-release bug traced to requirement gap | Bug root cause field | Ground-truth | Long | **Strong negative** |
| Story delivered on sprint | Sprint burndown | Auto-measured | Medium | Medium positive |
| Stakeholder satisfaction rating | Survey | Self-reported | Long | Weak (noisy) |
| Document has many readers | Confluence analytics | Auto-measured | Short | Weak (popularity ≠ quality) |

### Đánh giá tổng thể
BA **có** signal mạnh (story accepted, UAT pass, post-release bug trace) nhưng:
- Dependency vào quy trình công ty — nhiều công ty không log Jira đầy đủ
- Latency trung bình (sprint-level, không phải session-level)
- Post-release bug trace phụ thuộc root cause analysis culture — hiếm công ty làm tốt

**Verdict**: Khả thi nhưng cần config nhiều per-company.

---

## Role 2 — Tester (QA)

### Source có sẵn
- TestRail / Zephyr / Xray test execution
- Jira bug lifecycle
- CI pipeline test run logs
- Production bug reports (Sentry, Datadog, PagerDuty)

### Signal khả thi

| Signal | Source | Objectivity | Latency | Mạnh / yếu |
|---|---|---|---|---|
| Bug found pre-release in their coverage area | Bug report + test area mapping | Ground-truth | Short | **Strong positive** |
| Production bug escaped in their coverage area | Sentry + coverage mapping | Ground-truth | Long | **Strong negative** |
| Test case hit edge case found by someone else later | Cross-reference test case vs bug | Consensus | Medium | Medium positive |
| Test automation reduces manual regression time | CI metrics | Auto-measured | Long | Weak (lagging, multi-factor) |
| Test case reusable (cited by others) | Reference count | Auto-measured | Long | Weak |
| Bug report quality (one-shot fix vs back-and-forth) | Bug comment count | Consensus | Short | Medium positive |

### Đánh giá
Tester **có signal mạnh nhất trong non-dev** vì gần nhất với dev:
- Bug là ground-truth khách quan
- Production escape rate là KPI rõ ràng

Khó khăn:
- Mapping "coverage area" to individual tester cần infrastructure
- Production escape rate có latency dài (weeks to months)

**Verdict**: Khả thi nhất trong non-dev. Recommended là role thử nghiệm thứ 2 sau dev.

---

## Role 3 — Product Manager

### Source có sẵn
- Jira epic / roadmap tool
- Notion / Confluence spec docs
- Analytics dashboard (Amplitude, Mixpanel, GA)
- OKR tracking tool
- User research transcripts
- Meeting transcript / 1-1 notes

### Signal khả thi

| Signal | Source | Objectivity | Latency | Mạnh / yếu |
|---|---|---|---|---|
| Feature hit success metric | Analytics + pre-set target | Ground-truth | Very long | **Strong positive** (nếu target được set trước) |
| Feature killed / reverted after launch | Release notes | Ground-truth | Long | **Strong negative** |
| Sprint goal achieved | Sprint review outcome | Consensus | Medium | Medium positive |
| Spec shipped without major scope change | Spec diff vs ship state | Auto-measured | Medium | Medium positive |
| Stakeholder NPS / satisfaction | Survey | Self-reported | Long | Weak |
| Roadmap item delivered on time | Roadmap tracking | Auto-measured | Long | Weak (delivery ≠ quality) |

### Đánh giá
PM **signal rất yếu và rất trễ**:
- Feature success có latency rất dài và bị confound bởi 100 yếu tố khác (market, engineering, timing)
- Rất khó attribute "quality của spec" tách biệt với "quality của execution"
- Self-reported signal nhiều, ground-truth ít

**Verdict**: Khó nhất trong 5 role xét ở đây. Có thể cần hybrid với active intake (xem [tacit-knowledge-capture.md](tacit-knowledge-capture.md)).

---

## Role 4 — Accountant (Kế toán)

### Source có sẵn
- ERP transaction log (SAP, Oracle, Misa, Bravo, Fast)
- Excel / Sheets version history
- Email approval workflow
- Audit report (internal + external)
- Month-end close checklist

### Signal khả thi

| Signal | Source | Objectivity | Latency | Mạnh / yếu |
|---|---|---|---|---|
| Month-end close on time | Close date vs deadline | Ground-truth | Medium | **Strong positive** |
| No audit adjustment on their work area | Audit report | Ground-truth | Very long | **Strong positive** |
| Post-close reclassification | ERP reversal entries | Ground-truth | Medium | **Strong negative** |
| Reconciliation variance low | ERP reconciliation log | Auto-measured | Short | Medium positive |
| Compliance finding (tax/regulatory) | Regulatory report | Ground-truth | Long | **Strong negative** |
| Task turnaround (AP voucher processing time) | Workflow log | Auto-measured | Short | Weak (speed ≠ quality) |

### Đánh giá
Kế toán **có signal rất mạnh** nhưng lệch về trục latency:
- Audit finding là ground-truth cực mạnh nhưng latency năm
- Close on time và reconciliation variance là short-latency signal khả thi
- Compliance là đặc trưng của ngành → schema cần field `regulation_ref`

**Verdict**: Khả thi, nhưng tập aggregation cần window dài hơn dev (quarterly thay vì nightly).

---

## Role 5 — Sales / Account Manager

### Source có sẵn
- CRM (Salesforce, HubSpot)
- Call recording (Gong, Chorus)
- Email thread
- Deal pipeline history

### Signal khả thi

| Signal | Source | Objectivity | Latency | Mạnh / yếu |
|---|---|---|---|---|
| Deal won | CRM | Ground-truth | Long | **Strong positive** |
| Deal lost | CRM | Ground-truth | Long | Negative (tuỳ reason) |
| Retention / renewal | CRM | Ground-truth | Very long | Strong positive |
| Win rate cá nhân vs team average | CRM aggregation | Auto-measured | Long | Strong (lọc top performer) |
| Customer satisfaction (CSAT/NPS) | Survey | Self-reported | Long | Medium |

### Đánh giá
Sales **có signal KPI rõ ràng** (revenue, win rate) — đây là ngành có metric culture sẵn nên đo được. Nhưng:
- Win/loss bị confound rất mạnh bởi chất lượng lead, product-market fit, pricing
- "Top performer trong 1 quarter" không bằng "top performer ổn định" → cần multi-window smoothing

**Verdict**: Khả thi, nhưng skill có thể bị dominated bởi luck signal nếu aggregation không cẩn thận.

---

## Signal combination & scoring

Không bao giờ dùng 1 signal đơn. Mọi role đều phải combine multi-signal thành 1 session score:

```
session_score = w1*signal1 + w2*signal2 + ... - w_neg*negative_signal
```

Thuộc tính cần:
1. **Decay theo thời gian** — signal cũ nhẹ hơn signal mới
2. **Confidence weighting** — ground-truth signal weight cao hơn self-reported
3. **Per-role weight** — BA weight story-acceptance cao, tester weight bug-escape cao
4. **Threshold cut-off** — chỉ session trên threshold mới vào aggregation

Threshold cần tuning per role dựa trên distribution thực tế → cần data trước khi chốt.

---

## What we don't know

1. **Signal có đủ mạnh để distill không?** — câu hỏi sinh tử. Có thể với PM thì câu trả lời là "không" và phải fallback qua active intake.
2. **Attribution problem** — "session nào contribute bao nhiêu vào outcome?" rất khó với non-dev vì nhiều người cùng tác động (BA viết spec, dev code, tester test, PM release → bug là của ai?). Dev có luxury là 1 PR = 1 tác giả.
3. **Negative signal per role** — ta đã list positive khá rõ nhưng negative (cái gì là "noise") chưa rõ bằng.
4. **Signal gaming** — khi user biết signal nào được reward, họ có game nó không? "Story accepted first time" có thể game bằng cách viết story vague để dev không refine được.
5. **Time window** — nightly aggregation hợp với dev nhưng có thể sai với kế toán (monthly close) hoặc sales (quarterly quota).
6. **Signal quality vs signal quantity tradeoff** — 1 signal rất mạnh và rare vs 5 signal yếu và common. Cái nào cho output aggregation tốt hơn?

---

## What to validate

1. **Pick 1 non-dev role** (đề xuất: Tester vì signal gần dev nhất) và thực sự **kết nối source, kéo event về, compute signal** — trước khi đầu tư xây full pipeline.
2. **Measure signal distribution** — bao nhiêu % session có signal? distribution có skew tốt không? có threshold tự nhiên không?
3. **Ground-truth check** — lấy 20 session được score cao nhất, nhờ một senior trong role đó review manually. Họ có đồng ý đó là "session tốt" không?
4. **Negative test** — lấy 20 session score thấp nhất, check xem có thực sự là noise/bad không, hay có false negative.

---

## Decisions

| # | Decision | Tạm đề xuất |
|---|---|---|
| S1 | Signal schema có thống nhất across role? | Có — abstract `SignalDefinition` chung, per-role weight |
| S2 | Threshold fixed hay adaptive? | Adaptive — percentile-based per role |
| S3 | Window aggregation | Configurable per role (dev daily, kế toán monthly) |
| S4 | Role nào không thể đáp ứng signal quality thì làm sao? | Fallback sang active intake ([tacit-knowledge-capture.md](tacit-knowledge-capture.md)) |

---

## References

- [architecture.md — Quality signals section](../architecture.md)
- [multi-role-extension.md](multi-role-extension.md)
- [tacit-knowledge-capture.md](tacit-knowledge-capture.md) — fallback khi passive signal không đủ
- [open-questions.md](open-questions.md)
