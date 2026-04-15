# Prior Art — Cross-Industry Knowledge Capture

> Distill không phải là người đầu tiên cố gắng capture và tái phân phối tri thức thực chiến của người giỏi. Học từ các ngành đã thử.

**Status:** Research — overview, chưa deep-dive từng case.
**Related:** [idea.md](../idea.md), [tacit-knowledge-capture.md](tacit-knowledge-capture.md), [multi-role-extension.md](multi-role-extension.md)

---

## Vì sao nên học từ cross-industry

Docs hiện tại ([idea.md](../idea.md)) chỉ reference 3 project dev-tool (claude-mem, SkillClaw, colleague-skill). Đây là inspiration kỹ thuật tốt nhưng đều trong cùng domain AI-for-dev. Để mở rộng ra non-dev role, cần học từ các ngành đã làm knowledge capture lâu hơn:

- **Management consulting** — McKinsey, BCG, Bain đã build knowledge management system từ 30+ năm
- **Medical** — clinical decision support, UpToDate, DynaMed
- **Law** — legal precedent and brief mining, Westlaw, Lexis
- **Call center / CX** — QA mining, conversation analytics
- **Manufacturing** — lean, kaizen, SOP evolution (Toyota Production System)
- **Military** — After-Action Review (AAR) practice
- **Academic KM research** — Nonaka SECI, communities of practice

Mỗi ngành đã giải quyết 1-2 vấn đề mà Distill sẽ gặp. Tài liệu này điểm qua những bài học chính.

---

## 1. Management Consulting — Knowledge Management Systems

### Ai
McKinsey's "Knowledge Resource Directory", BCG's "Knowledge Navigator", Bain's "Global Experience Center".

### Làm gì
- Mọi dự án kết thúc phải deposit deliverable vào knowledge base
- Phân loại theo industry × function × framework
- Reviewer human cho mỗi deposit
- Consultant mới tra cứu trước khi design approach

### Bài học tốt
- **Framework + example hybrid** — không chỉ ship framework trừu tượng, luôn kèm 2-3 real case
- **Curation quality matters more than quantity** — thà ít deliverable tốt còn hơn nhiều deliverable loose
- **Role-scoped retrieval** — consultant junior nhìn khác senior, partner nhìn khác nữa
- **Cross-industry pattern** — pattern "cost reduction" có thể transfer từ retail sang manufacturing

### Bài học xấu (Distill tránh)
- **Deposit fatigue** — consultant lười deposit cuối dự án, khi họ đã move on → quality giảm
- **Staleness** — KB lớn dần, pattern cũ không bao giờ được garbage collect
- **Search-centric vs injection-centric** — KB chờ bạn tìm, không chủ động inject. Người bận không tìm.
- **Over-formalization** — template chặt quá → nhân viên không muốn deposit

### Implication cho Distill
- Distill's auto-capture solves "deposit fatigue" (không cần manual deposit)
- Distill's inject-at-use solves "search-centric" (không cần bạn chủ động tìm)
- Distill phải có garbage collection strategy — pattern cũ expire
- Seed pack phải có example, không chỉ abstract rule

---

## 2. Medical — Clinical Decision Support (UpToDate, DynaMed)

### Ai
UpToDate, DynaMed, BMJ Best Practice. Subscription service cho bác sĩ.

### Làm gì
- Team biên tập là physician trong field
- Mỗi topic có "author + peer reviewer + editor"
- Update theo schedule (topic cập nhật mỗi 4-6 tháng)
- Evidence-graded — mỗi recommendation có link về literature
- Delivered at point-of-care — tích hợp vào EMR workflow

### Bài học tốt
- **Evidence grading** — không chỉ nói "làm X", mà nói "làm X (strong evidence, n=1200 trial)"
- **Update cadence có thật** — có schedule chính thức
- **Provenance chain** — mọi khuyến nghị trace về source
- **Point-of-care delivery** — không bắt doctor tra cứu, tích hợp vào workflow hiện có

### Bài học xấu (tránh)
- **Human-authored không scale** — chi phí biên tập rất cao
- **Latency cập nhật** — research mới nhất không kịp vào, 4-6 tháng
- **One-size-fits-all** — không personalize theo patient population của bác sĩ

### Implication cho Distill
- **Provenance** là must-have — mỗi skill module trace về events/sessions contributed. Đã có trong design hiện tại.
- **Evidence grading** — thêm field "pattern strength" vào skill module (số PR, số người, recency)
- **Point-of-care = progressive disclosure at inject time** — đã là design của skill pack
- **Auto-curation** là thế mạnh của Distill vs UpToDate — tận dụng

---

## 3. Law — Legal Precedent Systems (Westlaw, Lexis)

### Ai
Westlaw, LexisNexis, Bloomberg Law.

### Làm gì
- Database của case law, statute, secondary source
- Classification taxonomy phức tạp (key number system)
- Citation network — case cite case, tạo graph
- LLM overlay gần đây (CoCounsel, Harvey) — retrieve + summarize

### Bài học tốt
- **Citation graph là quality signal tự nhiên** — case được cite nhiều = có ảnh hưởng
- **Taxonomy stable** — key number system tồn tại 100 năm
- **Use case-specific retrieval** — luật sư hỏi theo fact pattern, không theo keyword

### Bài học xấu (tránh)
- **Taxonomy rigidity** — khó add category mới → new domain (crypto, AI law) chậm vào
- **Depth over breadth** — rất mạnh về trọng trường hợp, yếu về chiến lược thực tế

### Implication cho Distill
- **Citation graph tương đương**: "module này được trigger bao nhiêu lần × outcome kết quả" → quality ranking
- **Taxonomy stability** — role taxonomy (xem [role-taxonomy.md](role-taxonomy.md)) cần stable nhưng cũng phải flexible. Học cách balance.
- **Retrieval by fact pattern** — injector dùng context (files, prompt) tương tự

---

## 4. Call Center / CX — Conversation Analytics

### Ai
Gong, Chorus.ai, Observe.ai, CallMiner.

### Làm gì
- Record tất cả call (sales / support)
- Transcribe + diarize
- LLM tagging: sentiment, topic, objection, outcome
- "Best call" identification — call dẫn đến deal won
- Aggregate pattern across top performer
- Coach junior: "play the top 5 calls in situation X"

### Bài học tốt
- **Passive capture như Distill** — zero friction, tự động
- **Outcome correlation** — deal won = signal, deal lost = signal
- **Pattern mining from raw transcript** — LLM extract được pattern
- **Coaching delivery** — "your call hôm nay sai ở minute 3, top performer xử lý thế này"

### Bài học xấu (tránh)
- **Privacy concerns** — customer interaction luôn nhạy cảm
- **Survivorship bias** — học từ top performer không đồng nghĩa pattern của họ là nhân quả với success
- **Over-simplification** — pattern "nói X ở phút Y" quá cơ học, không transfer được

### Implication cho Distill
- **Call-center setup gần giống nhất với vision của Distill** — đáng nghiên cứu sâu cách Gong mining pattern
- **Survivorship bias là rủi ro lớn** — Distill phải có guard: negative example training, test set validation
- **Pattern granularity** — không nên học câu-by-câu mà học decision pattern

---

## 5. Manufacturing — Lean, Kaizen, SOP Evolution (Toyota)

### Ai
Toyota Production System, lean manufacturing community.

### Làm gì
- Standard Work — mỗi công việc có SOP
- Kaizen — mỗi nhân viên propose cải tiến nhỏ
- A3 report — 1 trang problem + analysis + countermeasure
- SOP được cập nhật sau mỗi kaizen được accept
- Andon — dừng line khi gặp vấn đề bất thường

### Bài học tốt
- **SOP là living document** — cập nhật liên tục chứ không frozen
- **Bottom-up improvement** — nhân viên line phát hiện và propose, không chờ management
- **Standard work = floor for continuous improvement** — có chuẩn thì mới có cải tiến
- **A3 format** — 1 trang, có cấu trúc → nhiều nhân viên viết được

### Bài học xấu (tránh)
- **Culture-dependent** — không phải công ty nào cũng có kỷ luật Toyota
- **Physical context** — khó transfer thẳng sang knowledge work

### Implication cho Distill
- **Skill pack = living SOP** — đây là framing tốt để pitch cho non-tech company
- **A3 report format** có thể inspire journal format trong [tacit-knowledge-capture.md](tacit-knowledge-capture.md)
- **Bottom-up** — kaizen validates "collective learning" idea

---

## 6. Military — After-Action Review (AAR)

### Ai
US Army Center for Army Lessons Learned (CALL).

### Làm gì
- Sau mỗi mission/exercise, team họp AAR
- 4 câu hỏi chuẩn:
  1. What was supposed to happen?
  2. What actually happened?
  3. Why were there differences?
  4. What can we learn?
- Output được format chuẩn, gửi lên CALL database
- CALL mine pattern, publish "lessons learned"

### Bài học tốt
- **Ritual chuẩn hoá** — AAR là bắt buộc, không optional
- **Blame-free culture** — AAR tập trung learning, không performance
- **4-question framework** — cực kỳ đơn giản, ai cũng trả lời được
- **Central aggregation với human curation**

### Bài học xấu (tránh)
- **Effort cao cho mỗi AAR** — không scale cho daily work
- **Bureaucratic drift** — theo thời gian AAR có thể trở thành paperwork

### Implication cho Distill
- **4-question framework** có thể thành journal template
- **Blame-free guarantee** là contract với user (xem [tacit-knowledge-capture.md](tacit-knowledge-capture.md))
- **Ritual cadence** — Distill có thể propose retro hook thay AAR

---

## 7. Academic — SECI, Communities of Practice

### Key authors
- Nonaka & Takeuchi (1995) — SECI model, "The Knowledge-Creating Company"
- Wenger (1998) — Communities of Practice
- Polanyi (1966) — Tacit Dimension

### Bài học chính

**SECI model** — 4 transition của knowledge:

| From → To | Tên | Mô tả | Distill equivalent |
|---|---|---|---|
| Tacit → Tacit | Socialization | Học qua quan sát, apprenticeship | Shadowing (chưa có) |
| Tacit → Explicit | Externalization | Viết ra, articulate | Journaling + LLM distill |
| Explicit → Explicit | Combination | Kết hợp nhiều doc | Aggregation step |
| Explicit → Tacit | Internalization | Đọc, học, nội hoá | Skill pack injection |

**Implication**: Distill hiện tại mạnh ở Combination + Internalization (explicit-centric). Yếu ở Externalization và Socialization. Điều này khớp với observation rằng non-dev role cần active intake.

**Communities of Practice**: Knowledge không transfer bằng document, transfer bằng tương tác người-người trong community. Implication: skill pack không thay thế được community, chỉ augment.

---

## Synthesis — 6 bài học cho Distill

1. **Pattern + example + provenance** (từ consulting + medical). Module nào cũng cần 3 thành phần này.
2. **Citation graph làm quality signal** (từ legal). "Module được trigger và outcome tốt" = ranking cao.
3. **Call-center là analogy gần nhất** (từ CX). Đáng research sâu Gong/Chorus về pattern mining.
4. **Living SOP framing** (từ lean). Dùng để pitch cho công ty non-tech.
5. **SECI model** (từ academic). Distill phải explicit cover cả 4 quadrant, không chỉ 2.
6. **Blame-free contract** (từ military). Phải là guarantee kỹ thuật và chính sách, không chỉ văn hoá.

---

## What we don't know

1. **Call-center analytics** — cần research thực tế hơn. Gong có paper/blog nào về pattern mining algorithm?
2. **Legal AI (CoCounsel, Harvey)** — những người làm LLM-over-legal đã học được bài gì? Có relevant không?
3. **Academic research gần đây** — sau Nonaka có gì? Có research về AI-mediated knowledge capture không?
4. **Failed attempts** — ngành nào đã cố và thất bại với KM? Vì sao?
5. **Distill vs Stack Overflow for Teams** — SO for Teams là explicit KB. Distill là implicit/automated. Có data về ROI của cả hai không?

---

## What to research next

1. **Gong / Chorus deep-dive** — 2 tuần research, viết report riêng về conversation analytics architecture
2. **SOP evolution case study** — tìm 1 công ty dùng lean với SOP thực sự living
3. **UpToDate editorial workflow** — tham khảo cách họ peer review vì Distill phase 2 có thể cần tương tự
4. **Failed KM systems retrospective** — đọc HBR / Knowledge Management Journal về KM failure

---

## References

- Nonaka I. & Takeuchi H. (1995) — *The Knowledge-Creating Company*
- Polanyi M. (1966) — *The Tacit Dimension*
- Wenger E. (1998) — *Communities of Practice*
- [idea.md](../idea.md) — 3 dev-tool inspiration gốc
- [tacit-knowledge-capture.md](tacit-knowledge-capture.md)
- [multi-role-extension.md](multi-role-extension.md)
