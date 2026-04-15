# Role Taxonomy — Research Notes

> Làm sao mô hình hoá "role" trong Distill sao cho scale được từ 5 role lên 50 role mà không rối?

**Status:** Research — xác định được khung, còn nhiều chỗ chưa chốt.
**Related:** [multi-role-extension.md](multi-role-extension.md), [architecture.md](../architecture.md)

---

## Vì sao taxonomy quan trọng

Role là **đơn vị scope** của toàn bộ Distill:
- Aggregation chạy per role
- Skill pack tồn tại per role
- Quality signal định nghĩa per role
- Capture source cấu hình per role

Nếu taxonomy sai, mọi thứ sai theo. Cụ thể, các failure mode:

| Taxonomy quá coarse | Taxonomy quá fine |
|---|---|
| Mọi "dev" chung 1 pack → frontend junior bị inject database migration patterns | "senior-react-dev-ecommerce" vs "senior-react-dev-fintech" là 2 role → không bao giờ đủ data để aggregate |
| BA và PM chung 1 pack → confused signal | "BA ngân hàng retail" khác "BA ngân hàng corporate" khác "BA ngân hàng private" → explosion |
| Không phân biệt seniority → junior bị inject pattern senior không hiểu | Skill pack chỉ dùng được 1 người → mất ý nghĩa "collective" |

**Mục tiêu**: Tìm granularity **đủ chi tiết để pack có signal, nhưng đủ rộng để aggregation có đủ data**.

---

## What we know

### Rule of thumb từ statistics

Aggregation cần **data density** — một pattern phải xuất hiện qua nhiều người × nhiều session để trở thành "collective signal". Từ đây suy ra:

- **Minimum viable role size**: ước tính 5–10 người cùng role trong cùng window 30 ngày. Dưới mức này, aggregation output gần như noise.
- **Healthy role size**: 15–30 người. Đủ đa dạng pattern nhưng vẫn tập trung signal.
- **Over-populated role**: >100 người. Không còn vấn đề aggregation, nhưng có nguy cơ "average out" — pattern của top performer bị hoà tan vào đám đông. Cần substratify.

→ Taxonomy phải linh hoạt theo **số lượng người**. Công ty 20 người có taxonomy khác công ty 2000 người.

### SECI / knowledge work frame

Role không chỉ là "chức danh công việc" — nó là **bối cảnh knowledge work**. 2 BA làm ở 2 domain khác hẳn (banking vs ecommerce) có thể có 30% skill chung, 70% skill domain-specific. Taxonomy phải phản ánh được điều này.

---

## Đề xuất mô hình: 4 tầng

Đề xuất taxonomy 4 tầng, từ rộng đến hẹp:

```
FUNCTION       →   ROLE        →   LEVEL       →   SPECIALIZATION
(bộ phận)         (nghề)          (thâm niên)     (chuyên sâu)

Engineering   →   Backend Dev →   Senior      →   Payments domain
Product       →   BA          →   Mid         →   Banking retail
QA            →   Tester      →   Junior      →   Mobile
Finance       →   Accountant  →   Senior      →   Tax compliance
```

### Tầng 1 — Function (bộ phận)

**Unit**: ~6–12 function cho một công ty trung bình.

**Ví dụ**: Engineering, Product, Design, QA, Data, Marketing, Sales, Finance, HR, Operations, Legal, Customer Success.

**Dùng để**:
- Phân quyền access (BA không thấy event của kế toán)
- Shared pack ở level này: "engineering-wide", "finance-wide"
- Compliance scope (dữ liệu HR tách biệt với dữ liệu engineering)

### Tầng 2 — Role (nghề)

**Unit**: ~2–6 role trong mỗi function.

**Ví dụ** (Engineering): Frontend Dev, Backend Dev, Mobile Dev, DevOps, Data Engineer, SRE.

**Đây là đơn vị chính của Distill** — skill pack sống ở tầng này. Khi ta nói "BA skill pack" thì là tầng này.

**Threshold**: Role chỉ tồn tại nếu có ≥5 người cùng role. Dưới 5 → merge lên function ("engineering-generic") hoặc wait.

### Tầng 3 — Level (thâm niên)

**Unit**: Junior / Mid / Senior / Staff+ (hoặc theo title internal của công ty).

**Dùng để**:
- Lọc pattern theo level (junior không nên được inject architectural decision pattern)
- Modulate pack manifest ("load module X chỉ cho senior")

**Implementation option**:
- **Option A**: Level là role riêng → `senior-backend-dev`, `mid-backend-dev`, `junior-backend-dev` là 3 pack khác nhau
- **Option B**: Level là **filter** trên 1 pack chung → cùng pack nhưng manifest khác nhau theo level

A đơn giản nhưng explode số pack. B clean hơn nhưng phức tạp injection logic.

**Recommendation tạm thời**: Option B — 1 pack per role, manifest có section `level_filter` quyết định module nào load cho level nào.

### Tầng 4 — Specialization (chuyên sâu)

**Unit**: Mở, tuỳ domain. Ví dụ: "payments", "auth", "banking-retail", "tax-vn".

**Dùng để**: Sub-cluster trong aggregation. Senior backend dev làm payments và senior backend dev làm search có skill khác nhau đáng kể.

**Implementation**: Specialization là **tag** trên event và skill, không phải pack riêng. Runtime injector có thể ưu tiên module matching specialization của user hiện tại.

---

## Identity model

Mỗi nhân viên được gán:

```yaml
user:
  id: u-1234
  function: engineering
  role: backend-dev
  level: senior
  specializations: [payments, fraud]
  secondary_roles:            # optional, multi-role
    - role: tech-lead
      level: mid
```

- Primary role xác định skill pack chính
- Secondary role cho phép multi-role (xem dưới)
- Specialization là tag, dùng cho ranking

---

## Multi-role handling

Đây là **open question** lớn. 3 case điển hình:

### Case 1 — Fullstack dev
Cùng lúc làm frontend và backend. Option:
- **A**: Tạo role "fullstack-dev" riêng → cần đủ người fullstack để aggregate
- **B**: User có 2 primary role → inject cả 2 pack → context bloat
- **C**: User có 1 primary role (role nào họ làm nhiều hơn) + 1 secondary (inject ít hơn)
- **D**: Dynamic — detect từ task hiện tại, inject pack phù hợp

**Recommendation**: C cho đơn giản. D cho maturity cao.

### Case 2 — BA kiêm PM
2 role hoàn toàn khác function. Cùng người nhưng 2 context công việc.
- Có thể giải quyết bằng **context-aware injection**: khi user làm task loại A thì inject pack A, task loại B thì pack B
- Signal context: active document type, active Jira project, active meeting title

### Case 3 — Transition
User đang chuyển role (junior → mid, backend → ML). Pack cũ vẫn còn relevant một phần, pack mới chưa full context.
- Soft transition: 2 pack cùng load trong N tuần với pack cũ có weight giảm dần
- Không cần giải quyết ngay, nhưng cần aware khi thiết kế identity model

---

## Role inheritance (có hay không?)

Câu hỏi: "senior-backend-dev" có nên **inherit** từ "backend-dev" không?

### Pro inheritance
- DRY — hard rule chung không phải duplicate qua N level
- Seed pack có thể dùng chung cho cả role family
- Update skill ở tầng cao tự động lan xuống

### Con inheritance
- Phức tạp override rule
- Tạo dependency graph → khó debug "skill này từ đâu ra"
- Hiếm khi skill thực sự giống nhau qua level — junior không nên được inject senior pattern

### Recommendation
**Không inheritance trong Phase 1.** Flat roles với duplicate. YAGNI. Nếu thấy pain rõ rệt sau khi có 10+ role thì mới thêm inheritance.

---

## Role discovery vs role declaration

2 cách biết "user X role nào":

### Option A — Declaration
- Admin map user → role trong config
- Đơn giản, chắc chắn
- Phải maintain khi org thay đổi

### Option B — Discovery
- Infer từ behavior: file types edit, tool used, meeting attended
- Auto-adapt khi người đổi role
- Noisy, khó verify

**Recommendation**: A cho Phase 1. Discovery là tính năng cho sau, cần research riêng.

---

## Org-specific taxonomy vs universal taxonomy

Câu hỏi: Distill có ship "universal role taxonomy" hay để mỗi công ty tự define?

### Universal
- Ship ra-of-the-box một bộ function/role chuẩn công nghiệp
- Plug-and-play, không cần config
- Nhưng không fit với công ty có cách đặt role khác

### Org-specific
- Mỗi công ty define taxonomy riêng trong config
- Flexible, match reality
- Khó ship pre-built seed pack

**Recommendation**:
- Ship một **reference taxonomy** như example
- Cho phép customer override bằng config
- Seed pack ship theo reference taxonomy; customer tự map role của họ sang reference role để dùng seed

---

## What we don't know

1. **Ngưỡng minimum 5 người/role** có đúng không? Cần validate bằng simulation hoặc case study thực.
2. **Option A vs B cho level** — chưa test trên dữ liệu thực.
3. **Multi-role** có thực sự là 10% use case hay 50%? Phụ thuộc structure từng công ty.
4. **Specialization threshold** — bao nhiêu specialization là đủ chi tiết, bao nhiêu là over-engineering?
5. **Cross-function skill** — ví dụ "data-driven decision making" là skill cả PM, BA, Data Analyst đều dùng. Mỗi pack copy riêng hay có shared layer?
6. **Role evolution over time** — công ty thay đổi, role mới sinh, role cũ mất → taxonomy phải migrate. Chưa có strategy.

---

## What to validate

1. **Paper-design taxonomy cho 1 công ty thật** (ví dụ: IT services company 150 người, có dev + BA + tester + PM + operations). Xem 4 tầng có fit không.
2. **Đếm headcount per role** của công ty đó, xem bao nhiêu role đạt ngưỡng 5 người.
3. **List các multi-role case thực tế** xem tỷ lệ bao nhiêu.
4. **Hỏi 2-3 engineering manager / HR** về cách họ nghĩ về role internal — mô hình mental của họ có match 4 tầng không.

---

## Decisions needed (để unblock Phase 1)

| # | Decision | Phải chốt khi nào | Tạm đề xuất |
|---|---|---|---|
| T1 | 4 tầng có đủ không? | Trước khi design identity schema | 4 tầng |
| T2 | Level là pack riêng hay filter? | Trước khi design skill pack format | Filter |
| T3 | Có inheritance không? | Trước khi design core engine | Không |
| T4 | Multi-role strategy? | Trước khi design injector | C (1 primary + N secondary) |
| T5 | Role declaration hay discovery? | Trước khi design admin UI | Declaration |
| T6 | Universal hay org-specific taxonomy? | Trước khi viết seed pack | Reference + override |

---

## References

- [multi-role-extension.md](multi-role-extension.md) — vì sao cần taxonomy để extend ra non-dev
- [architecture.md](../architecture.md) — layer nào của hệ thống bị ảnh hưởng bởi taxonomy
- [open-questions.md](open-questions.md) — tổng hợp các unknown
