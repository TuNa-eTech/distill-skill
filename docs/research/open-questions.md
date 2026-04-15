# Open Questions — Consolidated Tracker

> Tổng hợp mọi câu hỏi chưa có câu trả lời, để tracking qua Phase 1 và 2. Mỗi câu hỏi có owner, deadline (khi nào cần trả lời), và dependencies.

**Status:** Living document — update khi research có kết quả mới.
**Related:** Đây là index cho các file research khác.

---

## Cách đọc tài liệu này

Mỗi open question có:
- **ID** — tham chiếu cố định (OQ-xx)
- **Category** — Architecture / Product / Signal / Privacy / Scale / Org
- **Question** — câu hỏi cụ thể
- **Why it matters** — impact nếu trả lời sai
- **Blocking what** — phase/deliverable nào bị block
- **Current hypothesis** — giả định tạm thời để unblock
- **How to answer** — cách validate / research
- **Source** — file research nào raise câu hỏi này

**Priority labels**:
- 🔴 **P0** — phải trả lời trước Phase 1
- 🟡 **P1** — phải trả lời trước Phase 2
- 🟢 **P2** — có thể defer, revisit sau

---

## Architecture

### OQ-01 — Plugin interface boundary 🟡
**Question**: Role = 1 plugin monolith hay role = nhiều mini-plugin (source / signal / schema tách riêng)?
**Why it matters**: Quyết định API surface core engine phải maintain. Sai thì refactor lớn khi có role thứ 5.
**Blocking**: Thiết kế core engine skeleton
**Current hypothesis**: Monolith cho Phase 1 (đơn giản), mini-plugin khi có ≥5 role
**How to answer**: Paper-spec cho 3 role, đếm số extension point thực sự dùng chung
**Source**: [multi-role-extension.md](multi-role-extension.md)

### OQ-02 — Role inheritance 🟢
**Question**: senior-backend-dev có inherit từ backend-dev không?
**Why it matters**: Simplifies seed pack authoring, nhưng phức tạp override logic
**Blocking**: Skill pack format (mức độ nested)
**Current hypothesis**: Không inheritance — flat roles với duplicate
**How to answer**: Đếm DRY violation khi có 5-10 role, nếu >30% thì xem xét
**Source**: [role-taxonomy.md](role-taxonomy.md)

### OQ-03 — Level: pack riêng hay filter? 🟡
**Question**: Junior / mid / senior là 3 pack khác nhau hay 1 pack với manifest filter?
**Why it matters**: Affect identity model, injector logic, pack registry design
**Blocking**: Distribute layer design
**Current hypothesis**: 1 pack với filter
**How to answer**: Thử cả hai trên seed pack, đo context size + cache hit rate
**Source**: [role-taxonomy.md](role-taxonomy.md)

### OQ-04 — Multi-role injection strategy 🟡
**Question**: Fullstack dev (nhiều role cùng lúc) inject thế nào? A: 1 primary role / B: N primary / C: dynamic theo task
**Why it matters**: Ảnh hưởng context budget và accuracy của injection
**Blocking**: Injector design
**Current hypothesis**: 1 primary + N secondary với weight thấp
**How to answer**: Survey % multi-role user trong target company; nếu <10% thì giữ giả định
**Source**: [role-taxonomy.md](role-taxonomy.md)

### OQ-05 — Core engine: evolve layer chạy local hay central? 🟡
**Question**: Pipeline Summarize/Aggregate/Execute chạy ở server trung tâm hay trên máy dev?
**Why it matters**: Privacy vs. simplicity tradeoff. Local = privacy-first nhưng khó aggregate. Central = ngược lại.
**Blocking**: Deployment model
**Current hypothesis**: Central với redaction-at-edge (đã có trong architecture.md)
**How to answer**: Interview 2-3 enterprise target về privacy constraint
**Source**: [architecture.md](../architecture.md)

### OQ-06 — Cross-role skill sharing 🟢
**Question**: Skill dùng chung (ví dụ "stakeholder alignment" cho cả PM và BA) — duplicate hay có shared layer?
**Why it matters**: DRY vs. simplicity. YAGNI applies.
**Blocking**: Skill pack format mở rộng
**Current hypothesis**: Duplicate (YAGNI)
**How to answer**: Đo overlap thực tế sau khi có ≥3 role seed pack
**Source**: [multi-role-extension.md](multi-role-extension.md)

---

## Product / UX

### OQ-10 — Authoring experience cho seed pack 🔴
**Question**: Phase 1 viết tay seed pack, cần editor / linter gì? Tool-less Markdown hay custom format?
**Why it matters**: Friction của Phase 1 quyết định Phase 1 có tạo ra pack đủ tốt không
**Blocking**: Phase 1 kick-off
**Current hypothesis**: Plain Markdown với YAML frontmatter, JSON schema validation
**How to answer**: Dogfood viết 1 seed pack thực tế, note friction point
**Source**: [architecture.md — Open questions section](../architecture.md)

### OQ-11 — Success measurement 🔴
**Question**: Làm sao đo "pack có thực sự giúp dev" khách quan?
**Why it matters**: Không đo được = không biết nên invest Phase 2 không
**Blocking**: Phase 1 validation criteria
**Current hypothesis**: Kết hợp quantitative (onboarding time, PR cycle time, review comment count) + qualitative (self-reported usefulness)
**How to answer**: Pre-register metric trước khi chạy pilot Phase 1
**Source**: [architecture.md](../architecture.md)

### OQ-12 — Dashboard / observability UI 🟢
**Question**: Admin / user có cần UI để xem pack hiện tại, xem pattern, override không? Nếu có, UI nào?
**Why it matters**: Ship UI đắt, nhưng không có UI thì trust khó build
**Blocking**: Phase 2 distribution
**Current hypothesis**: Phase 1 không UI (chỉ Markdown files trong git). Phase 2 basic web view.
**How to answer**: Xin feedback từ Phase 1 pilot user — họ có muốn UI không, muốn xem gì?
**Source**: [tacit-knowledge-capture.md](tacit-knowledge-capture.md) (correction mode)

---

## Signal / Quality

### OQ-20 — Non-dev signal sufficiency 🔴
**Question**: Non-dev role có đủ objective signal để aggregation có ý nghĩa không?
**Why it matters**: Nếu không → phải fallback active intake toàn phần → kiến trúc khác hẳn
**Blocking**: Quyết định role thứ 2 sau dev
**Current hypothesis**: Tester đủ signal. BA khả thi nhưng mượt. PM không đủ.
**How to answer**: Validation exercise (mô tả ở [non-dev-signals.md § What to validate](non-dev-signals.md))
**Source**: [non-dev-signals.md](non-dev-signals.md)

### OQ-21 — Minimum role size để aggregation có signal 🟡
**Question**: Bao nhiêu người cùng role × bao nhiêu session là sàn để pattern không bị noise?
**Why it matters**: Quyết định công ty bao lớn thì Distill mới hoạt động
**Blocking**: Go-to-market targeting
**Current hypothesis**: 5-10 người, ≥30 session/người trong 30 ngày window
**How to answer**: Simulation trên dev data trước; rồi test thực
**Source**: [role-taxonomy.md](role-taxonomy.md), [architecture.md](../architecture.md)

### OQ-22 — Time window per role 🟡
**Question**: Nightly aggregation hợp với dev. Kế toán (monthly close) thì sao? Window adaptive per role?
**Why it matters**: Sai window → tất cả session bị average out hoặc không đủ data trong window
**Blocking**: Evolve layer scheduler
**Current hypothesis**: Configurable per role, default nightly
**How to answer**: List 5 role và natural cadence của công việc họ → map sang window
**Source**: [non-dev-signals.md](non-dev-signals.md)

### OQ-23 — Attribution problem 🟡
**Question**: Khi 1 outcome (ví dụ feature ship thành công) có nhiều người contribute (BA + dev + tester + PM), signal đó attribute về ai?
**Why it matters**: Sai attribution → ranking sai → pack reward người sai
**Blocking**: Signal computation
**Current hypothesis**: Equal split trong Phase 1, advanced attribution (Shapley-like) sau
**How to answer**: Thử cả 2 trên data thực, đo pack quality
**Source**: [non-dev-signals.md](non-dev-signals.md)

### OQ-24 — Signal gaming 🟢
**Question**: Khi user biết signal nào được reward, họ có game nó không? Cách detect?
**Why it matters**: Goodhart's law — signal trở thành target là signal chết
**Blocking**: Không phải blocking ngay, nhưng phải aware
**Current hypothesis**: Multi-signal combination + anomaly detection trên signal distribution
**How to answer**: Red team sau khi pack sản xuất đi vào production
**Source**: [non-dev-signals.md](non-dev-signals.md)

### OQ-25 — Survivorship bias 🟡
**Question**: Distill học từ top performer. Nhưng pattern của họ có phải nhân quả với outcome, hay là correlation + lucky?
**Why it matters**: Nếu học sai thì pack dạy team làm theo lucky pattern
**Blocking**: Aggregation algorithm
**Current hypothesis**: Cross-check pattern với negative sample (bottom performer cùng situation). Pattern chỉ pass nếu positive có, negative không có.
**How to answer**: Thử trên historical data, holdout test set
**Source**: [prior-art-cross-industry.md — Call Center section](prior-art-cross-industry.md)

---

## Privacy / Security

### OQ-30 — Redaction completeness 🔴
**Question**: Redaction at edge có thực sự bắt được mọi PII/secret trong mọi role? Non-dev content có PII nhiều hơn dev.
**Why it matters**: Leak PII vào shared pack = incident nghiêm trọng
**Blocking**: Phase 2 (khi redaction gặp non-dev content)
**Current hypothesis**: Pluggable redaction, per-role rules, fail-closed
**How to answer**: Test trên sample non-dev content, red team
**Source**: [architecture.md](../architecture.md)

### OQ-31 — Role-scoped access control 🟡
**Question**: BA không nên thấy skill pack của kế toán (hoặc có nên?). Cross-role visibility policy?
**Why it matters**: Có thể là blocking cho enterprise deployment
**Blocking**: Pack registry design
**Current hypothesis**: Default private per function, opt-in cross-function
**How to answer**: Interview 2 enterprise về access policy expectations
**Source**: [role-taxonomy.md](role-taxonomy.md)

### OQ-32 — Journal privacy guarantee 🟡
**Question**: Active intake (journal) chứa user opinion thô. Làm sao guarantee không leak raw content, chỉ leak pattern?
**Why it matters**: Không guarantee được thì không ai journal thật
**Blocking**: Active intake rollout (Phase 2+)
**Current hypothesis**: LLM distill tại edge → chỉ pattern (không raw) rời máy
**How to answer**: Security review, threat model
**Source**: [tacit-knowledge-capture.md](tacit-knowledge-capture.md)

### OQ-33 — Failure mode: bad pack poisoning 🟡
**Question**: Nếu pack chứa pattern sai systematically, toàn team làm sai theo. Guardrail?
**Why it matters**: Catastrophic failure mode
**Blocking**: Production deployment
**Current hypothesis**: Canary channel, human review gate cho pack diff lớn, fast rollback
**How to answer**: Design review, incident response playbook
**Source**: [architecture.md](../architecture.md)

---

## Scale / Ops

### OQ-40 — Pack update cadence 🟡
**Question**: Daily / weekly / on-demand? Cadence ảnh hưởng prompt cache và freshness.
**Why it matters**: Quá dense → cache busting liên tục. Quá thưa → stale.
**Blocking**: Distribute layer scheduler
**Current hypothesis**: Module update weekly, manifest update monthly
**How to answer**: Measure prompt cache hit rate ở các cadence khác nhau
**Source**: [skill-pack.md](../skill-pack.md)

### OQ-41 — Pack size budget 🟡
**Question**: Manifest ≤ 1.5k tokens, module ≤ 3k, total ≤ 50k — đã đúng chưa?
**Why it matters**: Quá lớn → context bloat quay lại
**Blocking**: Skill pack format
**Current hypothesis**: Soft cap đã đề xuất, enforcement bằng linter
**How to answer**: Thử với seed pack thực tế
**Source**: [skill-pack.md](../skill-pack.md)

### OQ-42 — Trigger granularity 🟢
**Question**: Manifest-level trigger hay sub-section trigger trong module?
**Why it matters**: Sub-trigger hoạt động precise hơn nhưng phức tạp injector
**Blocking**: Không blocking — optimization later
**Current hypothesis**: Manifest-level cho Phase 1
**Source**: [skill-pack.md](../skill-pack.md)

### OQ-43 — Source heterogeneity per customer 🟡
**Question**: Khách hàng A dùng Jira, khách hàng B dùng Linear. Cùng 1 role adapter thế nào?
**Why it matters**: Determines config complexity at deployment time
**Blocking**: Deployment story cho Phase 2
**Current hypothesis**: Adapter per tool, config declares which adapter per customer
**How to answer**: Inventory top 10 tool trong target market
**Source**: [multi-role-extension.md](multi-role-extension.md)

---

## Organization / Rollout

### OQ-50 — Phase 1 pilot role 🔴
**Question**: Role đầu tiên cho pilot là gì? Dev là default nhưng không stress-test multi-role design.
**Why it matters**: Role nào pilot quyết định những gì ta học được
**Blocking**: Phase 1 kick-off
**Current hypothesis**: Dev cho Phase 1 (validate pipeline). Role thứ 2 là Tester (validate multi-role design).
**How to answer**: Decision trong team
**Source**: [non-dev-signals.md](non-dev-signals.md)

### OQ-51 — Who owns pack quality 🟡
**Question**: Human review loop cần người review. Ai? Manager? Senior trong role? Dedicated curator?
**Why it matters**: Không có owner → pack quality rơi
**Blocking**: Phase 2 process design
**Current hypothesis**: Senior trong role, asynchronous review, thời lượng <1h/tuần
**How to answer**: Prototype với 1 team, đo effort thực tế
**Source**: [prior-art-cross-industry.md — Consulting](prior-art-cross-industry.md)

### OQ-52 — Dev vs non-dev rollout order 🟡
**Question**: Phase 1 dev → Phase 2 non-dev. Hay Phase 1 làm cả hai?
**Why it matters**: Làm cả hai từ đầu buộc core engine generalize sớm. Tách phase dễ nhưng risk over-fit core engine vào dev.
**Blocking**: Roadmap
**Current hypothesis**: Phase 1 chỉ dev. Phase 1.5 paper-spec non-dev (không code). Phase 2 implement non-dev.
**How to answer**: Risk assessment trong design review
**Source**: [multi-role-extension.md](multi-role-extension.md)

### OQ-53 — Seed pack provenance khi không có historical data 🟡
**Question**: Cold start cho role mới — không có session history. Seed pack hand-author hay generate từ tài liệu hiện có?
**Why it matters**: Role mới join muộn bị penalize
**Blocking**: Phase 2
**Current hypothesis**: Hybrid — hand-author skeleton, LLM enrich từ existing Confluence/Notion của team
**How to answer**: Thử cold start cho 1 role
**Source**: [multi-role-extension.md](multi-role-extension.md)

---

## Câu hỏi phải trả lời trước Phase 1 (🔴 P0)

Tóm tắt: 5 câu hỏi không thể ship Phase 1 mà chưa trả lời.

| ID | Question | Current hypothesis |
|---|---|---|
| OQ-10 | Authoring experience cho seed pack | Markdown + YAML frontmatter |
| OQ-11 | Success measurement | Onboarding time + PR cycle + survey |
| OQ-20 | Non-dev signal sufficiency (cho role thứ 2) | Test first on Tester role |
| OQ-30 | Redaction completeness | Pluggable, fail-closed |
| OQ-50 | Phase 1 pilot role | Dev primary, Tester paper-spec |

---

## Câu hỏi phải trả lời trước Phase 2 (🟡 P1)

15 câu hỏi. Xem từng category ở trên.

---

## Câu hỏi có thể defer (🟢 P2)

OQ-02, OQ-06, OQ-12, OQ-24, OQ-42 — can revisit sau khi có dữ liệu thực.

---

## Cập nhật tài liệu này

Khi một câu hỏi được trả lời:
1. Move từ current section sang section "Resolved" (sẽ tạo khi có item đầu tiên)
2. Ghi resolution + source
3. Giữ history — không xoá

Khi một câu hỏi mới xuất hiện từ research:
1. Thêm ID tiếp theo trong category phù hợp
2. Link back về source file
3. Update priority labels

---

## References

- [multi-role-extension.md](multi-role-extension.md)
- [role-taxonomy.md](role-taxonomy.md)
- [non-dev-signals.md](non-dev-signals.md)
- [tacit-knowledge-capture.md](tacit-knowledge-capture.md)
- [prior-art-cross-industry.md](prior-art-cross-industry.md)
- [architecture.md](../architecture.md)
- [skill-pack.md](../skill-pack.md)
- [idea.md](../idea.md)
