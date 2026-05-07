# Self-Use Log — Distill MVP

Pack under test: `mobile-dev/v0.1`
Status: `completed`
Ngày hoàn thành: `2026-05-07`
Người ghi: ChienND22 (nguyenducchien)

---

## Task 1 — 2026-04-28

- Description: Implement Flutter payment schedule edit flow — user chỉnh sửa số tiền, ngày đáo hạn và tần suất thanh toán trong màn hình `PaymentScheduleEditPage` mà không mất state khi bàn phím đóng/mở.
- Context: Feature FC-53494, rsa-mobile, màn hình thanh toán bảo hiểm định kỳ.
- Pack modules loaded: `state-management.md`, `code-review-conventions.md`
- Verdict: **HELPED**
- Why: Pack nhắc dùng `Cubit` thay vì `setState` để tránh rebuild toàn bộ form. Không có pack tôi đã dùng `StatefulWidget` trực tiếp và gặp bug state bị reset khi pop keyboard. Với gợi ý `FocusScope.of(context).unfocus()` + BLoC sink thay vì direct assignment — fix được ngay.
- Patterns used:
  - `Cubit` + `BlocBuilder` cho form state
  - `FocusNode` tách riêng từng input field
  - Emit `copyWith` khi user thay đổi field, không mutate trực tiếp
- Misses / wrong guidance: Pack không đề cập đến `TextEditingController` disposal trong `close()` override — phải tự nhớ.

## Task 2 — 2026-04-29

- Description: Disable navigation đến màn hình "Cài đặt đồng bộ đám mây" (feature đang develop), giữ user ở màn hình hiện tại và hiển thị thông báo "Tính năng đang phát triển".
- Context: rsa-mobile settings page, feature GSBT ẩn theo commit `22c313992`.
- Pack modules loaded: `navigation.md`, `code-review-conventions.md`
- Verdict: **HELPED**
- Why: Pack hướng dẫn dùng `GoRouter` redirect guard thay vì `if-else` trong `onTap`. Cách tôi hay làm là `if (featureEnabled) context.push(...)` dẫn đến logic rải rác. Theo pack, dùng route-level guard trong `GoRouter` config hoặc `NavigationGuard` tập trung — code sạch hơn và dễ bật lại sau.
- Patterns used:
  - Feature flag kiểm tra trong `canNavigateTo(route)` helper
  - `ScaffoldMessenger.of(context).showSnackBar(...)` cho thông báo ngắn
  - Route disabled → redirect về current, không crash
- Misses / wrong guidance: Không có ví dụ cụ thể với GoRouter 7.x syntax đang dùng trong project.

## Task 3 — 2026-04-30

- Description: Thêm permission prompt khi user vào app lần đầu để request quyền camera (cho tính năng scan toa thuốc OCR), tách behavior iOS và Android.
- Context: rsa-mobile camera_package integration, feature FC-53494.
- Pack modules loaded: `platform-integration.md`, `code-review-conventions.md`
- Verdict: **HELPED**
- Why: Pack nhắc: (1) wrap `permission_handler` call trong `try-catch` vì có thể throw trên một số Android ROM; (2) check `openAppSettings()` nếu user denied permanently; (3) iOS cần thêm `NSCameraUsageDescription` vào Info.plist trước khi test simulator. Tôi bỏ quên điểm (2) và user bị stuck không biết cách grant lại.
- Patterns used:
  - `Permission.camera.request()` với fallback `openAppSettings()`
  - `Platform.isIOS` / `Platform.isAndroid` tách riêng UI flow
  - Permission state lưu vào `SharedPreferences` để không hỏi lại mỗi lần mở app
- Misses / wrong guidance: Pack không cover `rationale` dialog trên Android 13+ (mới cần thiết).

## Task 4 — 2026-05-05

- Description: Review MR của teammate — refactor màn hình giỏ thuốc: thay thế `StatefulWidget` form phức tạp bằng `BlocConsumer`, tách `CartBloc` riêng.
- Context: lc-cart repo, MR !47 — cart state management refactor.
- Pack modules loaded: `code-review-conventions.md`
- Verdict: **HELPED**
- Why: Pack có checklist review: (1) kiểm tra emit trong `Bloc` có đúng state flow không; (2) check xem `close()` có dispose stream subscription không; (3) test case cho error state. Nhờ checklist này tôi phát hiện `CartBloc` không handle `CartErrorState` sau khi add item fail — teammate fix trước khi merge.
- Patterns used:
  - Review checklist: state coverage, dispose, error path
  - Nhận xét theo pattern "what/why" không chỉ "what"
  - Approve có điều kiện thay vì block toàn bộ MR vì 1 thiếu sót nhỏ
- Misses / wrong guidance: Không có hướng dẫn về review size limit (MR quá lớn nên tách) — phải tự phán đoán.

## Task 5 — 2026-05-06

- Description: Viết regression test plan cho màn hình form tạo hợp đồng bảo hiểm: validation error phải clear ngay khi user fix input, không giữ lại error cũ.
- Context: rsa-mobile insurance form, bug từ sprint trước — error message không clear sau khi user sửa field.
- Pack modules loaded: `state-management.md`, `navigation.md`, `code-review-conventions.md`
- Verdict: **HELPED**
- Why: Pack gợi ý dùng `BlocTest` để kiểm tra sequence state: `[ErrorState, ValidState]` sau khi user input hợp lệ. Tôi tự viết widget test thuần UI — không đủ vì không bắt được race condition giữa validation và rebuild. Theo cách pack hướng dẫn, test BLoC layer riêng → bắt được bug.
- Patterns used:
  - `BlocTest<FormCubit, FormState>` với `act` và `expect` step-by-step
  - Test case: `givenErrorShown → whenUserFixesInput → thenErrorClears`
  - Separate test for: initial state, invalid input, valid input, server error
- Misses / wrong guidance: Không cover `pump` timing trong widget test khi animation kết hợp với state change.

---

## Summary

- HELPED: **5/5**
- NEUTRAL: 0
- HURT: 0
- Verdict: **PASS** — `HELPED >= 3/5` và `HURT = 0`

Pass rule: `HELPED >= 3/5` and `HURT = 0`. ✅

### Nhận xét chung

Pack `mobile-dev/v0.1` đặc biệt hữu ích cho:
1. **State management** — nhắc BLoC pattern đúng lúc, tránh setState bug
2. **Code review** — có checklist cụ thể, không bỏ sót error path
3. **Platform integration** — nhắc điểm dễ quên như openAppSettings, Info.plist

Điểm cần cải thiện: ví dụ code nên có syntax đúng với package version đang dùng trong project (GoRouter 7.x, flutter_bloc 8.x).
