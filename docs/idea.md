# Distill Company — Tài liệu Ý tưởng

> *"Những gì nhân viên giỏi nhất học được trong năm làm việc, đừng để mất khi họ nghỉ việc — hãy mang nó vào AI của mọi người trong team."*

---

## Vấn đề

Mỗi dev trong công ty đang dùng AI theo cách riêng — level khác nhau, tool khác nhau, hiệu quả khác nhau. Có 3 lớp vấn đề chồng lên nhau:

- **Knowledge silos**: Người giỏi tìm ra workflow tốt nhưng không lan truyền được. Người mới bắt đầu từ zero.
- **Tribal knowledge**: Những cách làm hiệu quả nhất tồn tại trong đầu người. Khi họ nghỉ việc, mất hết.
- **Inconsistency**: Cùng một task, 5 dev làm 5 cách khác nhau, chất lượng output của AI cũng khác nhau hoàn toàn.

---

## Ý tưởng cốt lõi

Xây dựng một **"organizational brain"** — nơi tri thức thực chiến của từng role được capture, tổng hợp, và tái sử dụng.

Thay vì mỗi dev dạy AI từ đầu, hệ thống học từ toàn bộ team rồi cho mọi người dùng AI ở trình độ của người giỏi nhất.

> **Điểm mạnh nhất**: Distill giải quyết vấn đề *"AI chỉ tốt bằng người dùng nó"* bằng cách institutionalize tri thức của người dùng giỏi nhất — đây là leverage rất lớn cho cả công ty.

---

## Kiến trúc Pipeline

```
Raw behavior capture
        ↓
Quality scoring
(PR merged? Code review passed? Task completed?)
        ↓
Cross-user aggregation
(pattern xuất hiện ở nhiều người giỏi?)
        ↓
Role skill synthesis
        ↓
SKILL.md per role → inject vào mọi AI session
```

### Tầng 1 — Capture
Hook vào mọi AI interaction của dev: prompt, tool use, output. Cộng với Git history (PR, commit, code review). Không cần thay đổi workflow của bất kỳ ai.

**Nguồn data:**
- IDE hooks (Claude Code, Cursor, Windsurf)
- API proxy (intercept mọi AI call)
- Git/PR/Code review history
- Tài liệu nội bộ (Notion, Confluence, email)

### Tầng 2 — Evolve
Pipeline 3 bước chạy định kỳ trên shared storage:

1. **Summarize** — tóm tắt từng session
2. **Aggregate** — tổng hợp patterns từ nhiều người cùng role
3. **Execute** — output ra updated SKILL.md

Chỉ học từ **quality interactions**: PR merged = good signal, rejected = noise.

### Tầng 3 — Distribute
Skill packages được sync về mọi dev theo role. Khi họ mở IDE hoặc chat với AI, skill tự động được inject vào context — zero extra effort.

---

## Output: Role SKILL.md

Mỗi role trong công ty có một skill file, ví dụ `senior-backend-dev/SKILL.md`:

- Tech standards & coding conventions thực tế của công ty
- Workflow patterns hiệu quả nhất (không phải sách vở)
- Cách prompt AI hiệu quả cho từng loại task
- Common pitfalls và cách tránh
- Decision patterns cho các tình huống điển hình

---

## Tại sao phù hợp quy mô doanh nghiệp

| Tiêu chí | Giải thích |
|---|---|
| **Privacy-safe** | Không capture nội dung nhạy cảm, chỉ capture patterns. Deploy on-premise hoàn toàn. |
| **Opt-in friendly** | Dev không cần thay đổi gì, skill tự cải thiện trong background. |
| **Audit-able** | Mọi skill change đều có version history, có thể review và rollback. |
| **Role-scoped** | Skills theo role, không theo cá nhân — tránh privacy issue, dễ onboard nhân viên mới. |
| **Platform-agnostic** | Hoạt động với Claude Code, Cursor, Windsurf, Copilot — không lock-in. |

---

## Điểm khác biệt so với thị trường

Không có sản phẩm nào hiện tại kết hợp đủ 3 yếu tố:

- **Behavioral capture** — tự động, không cần effort từ người dùng
- **Collective synthesis** — học từ tập thể, không phải cá nhân
- **Role-scoped executable output** — inject trực tiếp vào AI workflow

| | Prompt libraries | AI coding guidelines | Knowledge mgmt | **Distill** |
|---|---|---|---|---|
| Tự động capture | ❌ | ❌ | ❌ | ✅ |
| Học từ tập thể | ❌ | ❌ | ⚠️ | ✅ |
| Executable output | ⚠️ | ✅ | ❌ | ✅ |
| Self-evolving | ❌ | ❌ | ❌ | ✅ |

---

## Nguồn cảm hứng kỹ thuật

| Repo | Học gì |
|---|---|
| **claude-mem** | Lifecycle hooks, capture → compress → inject pattern, progressive disclosure |
| **SkillClaw** | Collective evolution engine, Summarize → Aggregate → Execute pipeline, multi-user aggregation |
| **colleague-skill** | Intake flow qua chat, Correction layer, data source đa dạng (chat/email/doc/PR) |

---

## Lộ trình

| Phase | Thời gian | Làm gì | Validate gì |
|---|---|---|---|
| **1. Manual seed** | 2–4 tuần | Interview 2–3 dev giỏi nhất, viết tay SKILL.md đầu tiên | Skill có giúp dev khác làm tốt hơn không? |
| **2. Semi-auto** | 1–2 tháng | Deploy capture layer + evolve pipeline cơ bản | Skill tự update có đúng không? |
| **3. Full pipeline** | 3–6 tháng | Automated capture → evolve → distribute toàn công ty | ROI: onboarding time, code quality, AI output consistency |

---

*Distill Company — Your team's best work, distilled into every AI session.*
