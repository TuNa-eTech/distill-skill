# Multi-Role Extension — Research Notes

> Làm sao generalize kiến trúc dev-centric hiện tại của Distill ra mọi role trong công ty (BA, Tester, PM, Kế toán, HR, Sales, ...)?

**Status:** Research — nhiều câu hỏi, ít câu trả lời chắc chắn.
**Related:** [architecture.md](../architecture.md), [role-taxonomy.md](role-taxonomy.md), [non-dev-signals.md](non-dev-signals.md)

---

## Vì sao cần tài liệu này

Toàn bộ docs hiện tại ([idea.md](../idea.md), [architecture.md](../architecture.md), [skill-pack.md](../skill-pack.md)) đều giả định **user là developer**:

- Capture source: IDE hook, API proxy, Git/PR crawler
- Quality signal: PR merged, review passed, test passed, commit reverted
- Skill pack example: `senior-backend-dev/` với các module `api-design`, `db-migration`, `testing`
- Trigger: file path (`migrations/**`), keyword (`openapi`), tool use (database tool)

Đây là môi trường **cực kỳ thuận lợi**: dev làm việc trong digital artifact (code), mỗi thao tác đều để lại log có cấu trúc, và có quality gate khách quan (PR merge). Non-dev role không có đặc quyền này.

Câu hỏi trung tâm của tài liệu này: **kiến trúc nào sẽ không phải viết lại khi ta thêm role thứ N?**

---

## What we know

### Những thứ generalize được (core engine giữ nguyên)

Đây là các invariant của Distill, không phụ thuộc vào role:

1. **3-layer separation** — Capture → Evolve → Distribute. Tách biệt này không phụ thuộc loại người dùng.
2. **Event store chuẩn hoá** — miễn là mọi source đưa về chung một event schema thì evolve layer không quan tâm nguồn là Git hay Jira hay Excel.
3. **Summarize → Aggregate → Execute pipeline** — logic distill pattern từ nhiều người cùng role là bài toán chung, không đặc thù nghề.
4. **Progressive disclosure skill pack** — `manifest + modules + references` là container format, role nào cũng xài được.
5. **Role-scoped aggregation** — aggregation theo role, không theo cá nhân, là property không đổi.
6. **Quality-gated learning** — chỉ học từ signal tốt. Điều kiện "tốt" thay đổi theo role, nhưng nguyên lý không đổi.

### Những thứ KHÔNG generalize được (cần plugin hoá)

Phần này phải tách ra thành **role plugin**:

| Khía cạnh | Dev | BA | Kế toán | Ghi chú |
|---|---|---|---|---|
| Capture source | IDE, Git, PR | Confluence, Jira, meeting transcript | ERP, Excel, email duyệt | Hoàn toàn khác |
| Raw artifact | code, prompt, tool call | document, diagram, user story | voucher, journal entry, spreadsheet formula | Cấu trúc khác |
| Quality signal | PR merged | story accepted, UAT passed | kết toán cân, audit clean | Khác hẳn |
| Trigger signal (runtime) | file path, keyword, tool use | document type, meeting agenda | document kind, account code | Khác |
| Skill module taxonomy | api-design, db-migration, testing | requirement-elicitation, flow-modeling | tax-compliance, reconciliation | Domain khác |
| Distill prompt | "làm sao coding task này tốt hơn" | "làm sao requirement clearer" | "làm sao close book nhanh hơn" | Prompt engineering riêng |

Kết luận: **6 điểm trên là extension point**. Core engine phải không biết gì về 6 điểm này — nó gọi plugin.

---

## Đề xuất kiến trúc plugin-based

### Role plugin interface

Mỗi role là một folder:

```
roles/
├── senior-backend-dev/
│   ├── plugin.yaml          # metadata: name, version, inherits
│   ├── sources/             # source adapters riêng cho role
│   │   ├── ide-hook.ts
│   │   ├── git-crawler.ts
│   │   └── pr-crawler.ts
│   ├── signals.yaml         # quality signal definitions
│   ├── schema.yaml          # role-specific skill schema extensions
│   ├── distill-prompt.md    # prompt template cho summarize step
│   └── seed-pack/           # optional: hand-authored seed pack
├── business-analyst/
│   ├── plugin.yaml
│   ├── sources/
│   │   ├── confluence-sync.ts
│   │   ├── jira-crawler.ts
│   │   └── meeting-transcript.ts
│   ├── signals.yaml
│   ├── schema.yaml
│   ├── distill-prompt.md
│   └── seed-pack/
├── tester/
├── accountant/
└── ...
```

### Core engine interface

Core engine chỉ biết các abstract interface, không biết role cụ thể:

```typescript
interface RolePlugin {
  name: string;
  version: string;
  inherits?: string;              // role hierarchy (xem role-taxonomy.md)

  sources: SourceAdapter[];        // nguồn dữ liệu
  signals: QualitySignalSet;       // quality scoring function
  schema: SkillSchemaExtension;    // optional field mở rộng
  distillPrompt: PromptTemplate;   // prompt cho Summarize step
}

interface SourceAdapter {
  name: string;
  fetch(since: Date): Promise<RawEvent[]>;
  redact(event: RawEvent): RawEvent | null;  // null = drop
}

interface QualitySignalSet {
  score(session: Session): number;  // 0..1
  signals: SignalDefinition[];
}
```

Core engine:
1. Load tất cả role plugins từ `roles/`
2. Với mỗi role: chạy source adapters để fetch events
3. Redact tại edge
4. Score sessions bằng `QualitySignalSet`
5. Cho high-quality sessions qua pipeline `Summarize (với distillPrompt) → Aggregate → Execute`
6. Output skill pack vào registry

**Tính chất quan trọng**: thêm role thứ N chỉ cần tạo folder mới. Core không đụng.

---

## Case study: 3 role không phải dev

### Case 1 — Business Analyst

**Source:**
- Confluence page history (create / edit / link)
- Jira issue lifecycle (story written → refined → accepted)
- Meeting transcript (Zoom/Teams/Google Meet recording → transcription)
- Email thread với client
- Figma/Miro collaboration log

**Raw event:**
- `requirement_written` — BA tạo user story
- `requirement_refined` — BA update story sau refinement session
- `story_accepted` — dev confirm story clear đủ để estimate
- `story_rejected` — dev yêu cầu BA làm lại
- `uat_passed` — feature pass UAT
- `post_release_bug` — bug sau release do miss requirement

**Quality signal:**
- Strong positive: story accepted first time + UAT passed + no post-release bug
- Strong negative: story needs multiple refinements + UAT fail + post-release bug traced to requirement gap

**Skill module examples:**
- `requirement-elicitation.md` — pattern hỏi client
- `edge-case-discovery.md` — framework tìm edge case
- `acceptance-criteria-writing.md`
- `stakeholder-alignment.md`

**Trigger signal (runtime):**
- Document kind = "user story" → load `acceptance-criteria-writing`
- Meeting type = "refinement" → load `edge-case-discovery`

### Case 2 — Tester (QA)

**Source:**
- TestRail / Zephyr test case history
- Jira bug lifecycle
- CI test run logs
- Test plan documents

**Quality signal:**
- Strong positive: bug found pre-release in coverage bạn viết
- Strong negative: bug escape to production in area bạn đã test

**Skill module:**
- `test-case-design.md` — boundary, equivalence, combinatorial
- `exploratory-testing.md`
- `bug-report-quality.md`
- `regression-strategy.md`

### Case 3 — Kế toán

**Source:**
- ERP transaction log (SAP, Misa, Bravo, ...)
- Excel file version history (OneDrive/SharePoint audit log)
- Email approval chain
- Month-end close checklist

**Quality signal:**
- Strong positive: month-end close on time + no audit finding + no reclassification
- Strong negative: audit adjustment + post-close reclassification + late close

**Skill module:**
- `month-end-close.md`
- `vat-reconciliation.md`
- `fixed-asset-depreciation.md`
- `audit-prep.md`

**Lưu ý**: domain kế toán cực kỳ regulated, skill phải trace về legal reference (Thông tư, Chuẩn mực kế toán VN). Đây là field mở rộng `regulation_ref` trong schema — không có trong dev.

---

## What we don't know

Các câu hỏi mở cần nghiên cứu thêm:

1. **Source adapter boundary** — Nên viết adapter riêng cho từng tool (Jira, Confluence, SAP, ...) hay 1 adapter generic cho 1 class tool (webhook-based, polling-based)? Tradeoff: specific = chất lượng, generic = tốc độ mở rộng.

2. **Skill pack cross-role sharing** — BA skill `stakeholder-alignment` có chung một phần với PM skill cùng tên. Nên:
   - Duplicate trong 2 pack?
   - Tạo `shared/` pack mà mọi role inherit?
   - Symlink / reference cross-pack?

3. **Role hierarchy inheritance** — "senior-backend-dev" có inherit từ "backend-dev" không? Nếu có thì override rule thế nào? Xem [role-taxonomy.md](role-taxonomy.md).

4. **Distill prompt per role hay per task** — Một prompt distill chung cho role BA có đủ tốt không, hay cần prompt riêng cho từng loại artifact (user story vs meeting note vs email)?

5. **Multi-tenant per department** — Cùng là BA nhưng BA ngân hàng và BA ecommerce có skill rất khác. Role có nên scope theo department/domain không?

6. **Human review load** — Non-dev skill ít objective signal hơn → cần human review nhiều hơn → ai review? Reviewer là ai trong org?

7. **Cold start** — Role mới chưa có seed pack, chưa đủ historical data, pipeline output gì? Có fallback nào?

8. **Tool heterogeneity trong cùng role** — Không phải kế toán nào cũng dùng SAP. Cùng role nhưng 2 công ty dùng tool khác → source adapter config phải per-deployment.

---

## What to validate (trước khi code)

Trước khi bắt tay implement, cần validate 4 giả định sau:

1. **Giả định**: Plugin interface 4 thành phần (sources, signals, schema, distillPrompt) là đủ cover mọi role.
   **Cách validate**: Thiết kế paper-spec cho 5 role khác nhau (dev, BA, tester, PM, kế toán) và check có field nào không fit interface không.

2. **Giả định**: Non-dev role có đủ objective quality signal để aggregation tạo ra pattern có giá trị.
   **Cách validate**: Chọn 1 role thử, list signal có thể thu thập từ tool thực tế, xem có signal nào đủ mạnh như "PR merged" không. Xem chi tiết ở [non-dev-signals.md](non-dev-signals.md).

3. **Giả định**: Skill pack format `manifest + modules + references` fit cho mọi role.
   **Cách validate**: Hand-author seed pack cho 1 non-dev role (ví dụ BA), xem format có gượng ép không.

4. **Giả định**: Capture đủ dữ liệu tacit của non-dev role chỉ từ digital artifact. (Có thể sai — xem [tacit-knowledge-capture.md](tacit-knowledge-capture.md).)
   **Cách validate**: Shadow 1 BA senior trong 1 tuần, so sánh "những gì BA thực sự làm" với "những gì có trace trong tool". Tỷ lệ gap sẽ cho biết ta cần active intake không.

---

## Decision points

Các quyết định cần chốt trước khi Phase 1 dev-only kết thúc (để khi thêm non-dev role không phải refactor):

| # | Decision | Option A | Option B | Recommendation |
|---|---|---|---|---|
| D1 | Plugin API boundary | Role = 1 plugin monolith | Role = nhiều mini-plugin (source / signal / schema tách riêng) | A cho đơn giản ban đầu |
| D2 | Role inheritance | Flat roles | Hierarchy với inheritance | Flat trước, add hierarchy khi cần |
| D3 | Cross-role skill sharing | Duplicate | Shared layer | Duplicate trước (YAGNI) |
| D4 | Distill prompt location | In-code | In plugin folder | In plugin (hot-swappable) |
| D5 | Human review workflow | Sync (block publish) | Async (publish canary, review sau) | Async + canary |

---

## Next steps

1. Viết xong 5 file research còn lại để có bức tranh đầy đủ
2. Paper-spec cho 1 non-dev role (đề xuất: **Business Analyst** — vì có nhiều digital artifact sẵn nhưng vẫn khác dev đủ để stress-test architecture)
3. So sánh paper-spec đó với dev plugin hiện tại → tìm gap trong core engine
4. Refine kiến trúc trong [architecture.md](../architecture.md) với các điểm generalization vừa phát hiện

---

## References

- [architecture.md](../architecture.md) — kiến trúc hiện tại (dev-centric)
- [role-taxonomy.md](role-taxonomy.md) — mô hình role chi tiết
- [non-dev-signals.md](non-dev-signals.md) — quality signal cho non-dev
- [tacit-knowledge-capture.md](tacit-knowledge-capture.md) — capture tri thức ngầm
- [open-questions.md](open-questions.md) — tổng hợp unknown
