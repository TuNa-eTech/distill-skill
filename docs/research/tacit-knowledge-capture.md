# Tacit Knowledge Capture — Research Notes

> Một phần lớn "skill" của nhân viên giỏi nằm trong đầu họ, không có trong bất kỳ tool nào. Làm sao kéo nó ra?

**Status:** Research — đây là vùng đòi hỏi nghiên cứu nhiều nhất từ human-computer interaction và knowledge management.
**Related:** [non-dev-signals.md](non-dev-signals.md), [multi-role-extension.md](multi-role-extension.md), [prior-art-cross-industry.md](prior-art-cross-industry.md)

---

## Khái niệm cốt lõi

Knowledge management cổ điển (Nonaka 1995, SECI model) phân biệt 2 loại tri thức:

| Loại | Mô tả | Ví dụ |
|---|---|---|
| **Explicit** (tri thức hiện) | Đã được mã hoá thành văn bản, code, công thức, checklist | API doc, SOP, commit message, Confluence page |
| **Tacit** (tri thức ngầm) | Tồn tại trong đầu, trong thói quen, trong cảm giác — không dễ mã hoá | "Tôi biết khi nào hoá đơn này có vấn đề", "Tôi cảm giác client này sắp churn" |

**Observation quan trọng**: Tỷ lệ tacit/explicit khác nhau theo role.

| Role | % tacit knowledge ước tính | Vì sao |
|---|---|---|
| Junior dev | ~20% | Phần lớn work là code, leave digital trace |
| Senior dev | ~40% | Quyết định kiến trúc thường không được viết ra |
| BA | ~50% | Nhiều "sense" về khi nào requirement clear/unclear |
| Tester | ~40% | Intuition về edge case |
| PM | ~60% | Hầu hết decision-making ở trong đầu |
| Accountant (senior) | ~50% | Biết case nào phải hỏi thêm, biết rủi ro ngầm |
| Sales | ~70% | "Reading the room" là core skill, không log được |
| HR | ~70% | Cảm nhận con người, conflict reading |

Con số trên là ước lượng qualitative, không có research back. Nhưng trend rõ: **càng xa code, càng nhiều tacit**.

**Implication**: Distill hiện tại capture được 100% explicit trace cho dev, nhưng với non-dev, **passive capture** chỉ thấy phần nhỏ. Cần thêm **active intake**.

---

## 4 phương thức capture

### Phương thức 1 — Passive capture (đang có)

Hook vào tool, thu thập artifact tự động. Không cần effort.

**Ưu**:
- Zero friction
- Scale tốt
- Objective

**Nhược**:
- Chỉ thấy explicit
- Miss rationale (why) → chỉ thấy what
- Non-dev có ít digital trace hơn

**Dùng khi**: tool digital có audit log đầy đủ, role có explicit work product cao.

### Phương thức 2 — Journaling (daily log)

Mỗi ngày nhân viên viết 2-3 câu: "Hôm nay tôi xử lý X, quyết định Y, vì Z". Gửi vào hệ thống.

**Ưu**:
- Rẻ (vài phút/ngày)
- Capture được rationale, không chỉ action
- Tạo habit tốt cho chính nhân viên
- Timely — capture khi memory còn fresh

**Nhược**:
- Friction — đòi hỏi discipline
- Self-report bias
- Dễ trở thành ritual vô hồn

**Implementation idea**:
- Slack bot hỏi cuối ngày "3 điều bạn làm hôm nay?"
- LLM guide conversation để kéo ra rationale: "vì sao bạn chọn approach đó?"
- Output có cấu trúc: `{what, why, outcome_so_far}`
- Optional: user tag session liên quan trong tool (link Jira, Confluence)

**Dùng khi**: role có rationale phức tạp không hiện ra trong artifact. Mọi role non-dev đều hợp.

### Phương thức 3 — Shadowing / Apprenticeship

Người mới ngồi cùng người cũ, ghi lại (hoặc LLM transcribe) cách người cũ xử lý real-time case.

**Ưu**:
- Capture được tacit ở mức sâu nhất
- Đồng thời là hoạt động onboarding / mentoring có giá trị

**Nhược**:
- Rất expensive (2 người thay vì 1)
- Không scale
- Privacy với customer interaction

**Implementation idea**:
- Recording session với consent (internal meeting only)
- LLM diarize và annotate "moment of decision"
- Extracted pattern được senior review trước khi vào skill pack

**Dùng khi**: high-value role, kickoff của một skill module mới, không thay thế được bằng phương thức khác.

### Phương thức 4 — Post-mortem / Retrospective mining

Sau mỗi sự cố, project, quarter — retro có chủ đích để extract pattern.

**Ưu**:
- Đã có culture sẵn ở nhiều công ty
- Có context rõ ràng (success/failure)
- Rationale thường được nói ra trong retro

**Nhược**:
- Low frequency (retro định kỳ)
- Bias về negative (retro thường focus vào failure)
- Cần facilitation

**Implementation idea**:
- Tích hợp với tool retro (FunRetro, EasyRetro, Notion template)
- LLM summarize retro note thành pattern candidate
- Pattern candidate vào queue review

**Dùng khi**: cần nắm context lớn (dự án), cần mix success+failure, role có văn hoá retro.

---

## Active intake là gì

"Active intake" là thuật ngữ mình dùng cho mọi phương thức **yêu cầu effort từ nhân viên**, ngược với passive capture. Phương thức 2, 3, 4 ở trên đều là active intake ở các mức độ khác nhau.

**Friction tradeoff**:

```
Effort       │                   Shadowing ●
required     │
             │              Post-mortem ●
             │
             │         Journaling ●
             │
             │  Passive capture ●
             └────────────────────────────→
              Explicit only            Deep tacit
                    Knowledge depth
```

Càng sâu tacit càng đòi hỏi effort. Không có bữa trưa miễn phí.

**Design principle của Distill**:
1. **Default passive** — không đòi hỏi gì nếu không cần
2. **Graduated active** — role nào passive không đủ thì ramp lên journaling
3. **Targeted deep** — shadowing chỉ khi có high-value case cụ thể
4. **Retro-friendly** — tích hợp vào retro đã có sẵn, không tạo ritual mới

---

## Correction layer

Dù capture kiểu gì, LLM distill ra pattern có thể sai. Cần một layer cho nhân viên **correct** lại:

- "Pattern này không đúng với role của tôi"
- "Pattern này thiếu context"
- "Pattern này chỉ áp dụng cho domain X"

Correction có 2 mode:

### Mode A — Passive correction
- Skill pack được inject vào AI session
- Nếu user override / reject suggestion từ pack → log event
- Nếu nhiều user reject cùng pattern → pattern bị downgrade

**Nguồn cảm hứng**: colleague-skill correction layer.

### Mode B — Active correction
- Dashboard cho user xem pack của role mình
- Vote / comment trên từng module
- Flag pattern sai

**Recommendation**: Ship Mode A trước (zero-friction), Mode B khi có maturity cao.

---

## Prompting for tacit extraction

Khi dùng LLM để distill tacit knowledge qua journaling hay shadowing, prompt rất quan trọng. Vài pattern:

### "5 whys" chain
Sau mỗi câu trả lời của user, LLM hỏi "vì sao?" 3-5 lần để xuống đến rationale gốc.

### "What would go wrong?"
Hỏi "nếu làm ngược lại thì sao?" — thường ép user phát biểu cái mà họ coi là hiển nhiên.

### "Who else would disagree?"
Hỏi "ai trong team sẽ làm khác?" — lộ ra câu chuyện về pattern cá nhân vs team consensus.

### "What did you consider and reject?"
Hỏi option không chọn — quan trọng hơn option được chọn.

### Reference specific artifact
"Mở Jira ticket JIRA-123 ra — lúc bạn viết comment này, bạn đang suy nghĩ gì?" — anchor vào thực tế thay vì ký ức trừu tượng.

---

## Rủi ro của active intake

### Rủi ro 1 — Survey fatigue
Nhân viên ngán, bỏ qua, trả lời qua loa → data chất lượng thấp → feed GIGO vào pipeline.

**Mitigation**:
- Frequency thấp (weekly cho junior, monthly cho senior)
- Reward loop visible — cho user thấy skill pack của role mình cải thiện nhờ input của họ
- Cho phép skip không penalty

### Rủi ro 2 — Performance theatre
Nhân viên viết journal để trông giỏi chứ không phải để phản ánh thực tế.

**Mitigation**:
- Journal không dùng cho performance review — cam kết rõ ràng
- Cho phép private journal (chỉ pattern extracted mới đi vào pool)
- Manager không thấy raw journal

### Rủi ro 3 — Privacy
Tacit knowledge thường gắn với story cá nhân, customer specifics, internal politics.

**Mitigation**:
- Redaction at source giống passive capture
- User preview trước khi gửi
- Opt-out per entry

### Rủi ro 4 — Junior capture senior inauthentic
Shadowing có thể tạo cảm giác "bị giám sát" cho senior → họ perform khác thường.

**Mitigation**:
- Chỉ shadow khi senior consent và buy-in
- Không ghi âm, chỉ note
- Senior review trước khi pattern được publish

---

## Distill sẽ tích hợp active intake thế nào

### Layer mới: Intake Layer

Thêm một layer mới giữa Capture và Shared Event Store:

```
Capture layer
├── Passive capture (hiện tại)
└── Active intake (mới)
    ├── Daily journal bot
    ├── Retro mining
    └── Shadow session upload

        ↓

Shared Event Store (chung schema)

        ↓

Evolve layer (không đổi)
```

Active intake output cùng event schema → evolve layer không biết sự khác biệt.

### Event schema mở rộng

```yaml
event:
  ...
  capture_mode: passive | journal | retro | shadow
  rationale: "..."         # chỉ có với active intake
  confidence: 0.9          # active intake thường có confidence cao hơn
```

Aggregation có thể weight active-intake event cao hơn passive (vì có rationale).

---

## What we don't know

1. **Friction threshold** — bao nhiêu phút/ngày là giới hạn trước khi nhân viên drop off?
2. **Correction loop impact** — active correction có đủ để làm pack tốt hơn không, hay chỉ là placebo?
3. **Journal quality distribution** — 10% senior viết tốt, 90% junior viết qua loa? Aggregation cần handle outlier.
4. **Shadow session scale** — có thể auto hoá partially bằng screen recording + LLM hay cần human trong loop?
5. **LLM bias khi distill tacit** — LLM có tendency generalize về "best practice" sách vở thay vì capture pattern thực tế riêng của team. Cần guard.
6. **Culture dependency** — active intake có work ở công ty có culture "bận quá" không? Có thể chỉ hợp với công ty đã có learning culture.

---

## What to validate

1. **Pilot journaling với 3 senior** — bất kỳ role nào — trong 2 tuần. Đo:
   - Tỷ lệ ngày có journal
   - Length trung bình
   - LLM extract được bao nhiêu pattern có nghĩa
   - User feedback về friction
2. **Compare: passive-only vs passive+journal** — với cùng role, xem skill pack nào chất lượng hơn (đánh giá qua review của senior trong role).
3. **Retro mining trial** — lấy 10 retro note quá khứ của team, xem LLM extract pattern được không.

---

## Decisions

| # | Decision | Tạm đề xuất |
|---|---|---|
| I1 | Phase 1 có active intake không? | Không cho dev. Có journaling cho 1 non-dev role pilot. |
| I2 | Journal frequency | Weekly cho non-dev; optional daily |
| I3 | Correction mode | Passive trước (log reject), active sau |
| I4 | Shadow scope | Chỉ dùng khi kick-off role mới, không hàng ngày |
| I5 | LLM prompt chain | 5-why + "considered and rejected" — iterate theo feedback pilot |

---

## References

- Nonaka & Takeuchi, *The Knowledge-Creating Company* (1995) — SECI model
- Polanyi, *The Tacit Dimension* — khái niệm gốc
- [non-dev-signals.md](non-dev-signals.md) — khi signal passive không đủ, fallback sang tacit capture
- [prior-art-cross-industry.md](prior-art-cross-industry.md) — cách industry khác giải quyết
- [open-questions.md](open-questions.md)
