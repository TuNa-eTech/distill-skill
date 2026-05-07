# Blind Test Packet — Distill MVP

Judge: `ChienND22`
Date: `2026-05-07`
Pack under test: `mobile-dev/v0.1`
Model: `claude-sonnet-4-6` (same model, same temperature for both options)

## Instructions

- Review the two options for each task without knowing which one used the pack.
- Pick one winner or mark a tie.
- Keep the reason short and concrete.
- Judge only the output quality for the stated task. Do not reward longer answers by default.
- If the two options are materially equivalent, choose `Tie`.

---

## Task T1 — State Management

- Prompt / scenario: Implement a Flutter payment schedule edit flow where the user can update amount, due date, and recurrence without losing unsaved local state.

**Option 1:**
```dart
// Dùng StatefulWidget + TextEditingController
class PaymentScheduleEditPage extends StatefulWidget { ... }
class _State extends State<PaymentScheduleEditPage> {
  final _amountCtrl = TextEditingController();
  final _dateCtrl   = TextEditingController();
  String _recurrence = 'monthly';

  void _onSave() {
    final amount = double.tryParse(_amountCtrl.text);
    if (amount == null) { /* show error */ return; }
    widget.onSave(PaymentSchedule(amount: amount, ...));
  }
  // rebuild toàn bộ form mỗi lần setState
}
```
Không có error isolation per field. State bị reset khi keyboard open/close trigger full rebuild.

**Option 2:**
```dart
// Cubit approach
class PaymentScheduleEditCubit extends Cubit<PaymentScheduleEditState> {
  PaymentScheduleEditCubit(PaymentSchedule initial)
      : super(PaymentScheduleEditState.fromSchedule(initial));

  void updateAmount(String raw) {
    final parsed = double.tryParse(raw);
    emit(state.copyWith(
      amount: parsed,
      amountError: parsed == null ? 'Số tiền không hợp lệ' : null,
    ));
  }
  void updateDueDate(DateTime date) => emit(state.copyWith(dueDate: date));
  void updateRecurrence(String r) => emit(state.copyWith(recurrence: r));
}

// Widget: BlocBuilder chỉ rebuild field bị thay đổi
BlocBuilder<PaymentScheduleEditCubit, PaymentScheduleEditState>(
  buildWhen: (prev, curr) => prev.amountError != curr.amountError,
  builder: (context, state) => TextFormField(
    onChanged: context.read<PaymentScheduleEditCubit>().updateAmount,
    decoration: InputDecoration(errorText: state.amountError),
  ),
);
```
State persist qua keyboard lifecycle. Mỗi field rebuild độc lập. Error clear tức thì khi user fix.

- Winner: **Option 2**
- Reason: Option 2 isolate error per field, không rebuild toàn form — đúng behavior yêu cầu. Option 1 sẽ mất state khi keyboard đóng/mở vì setState rebuild widget tree.

---

## Task T2 — Navigation

- Prompt / scenario: Design the route/navigation handling for a Flutter app flow where tapping an unfinished cloud-sync settings feature must keep the user on the same screen and show clear "coming soon" feedback.

**Option 1:**
```dart
// onTap inline check
ListTile(
  title: Text('Đồng bộ đám mây'),
  onTap: () {
    if (!FeatureFlags.cloudSync) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Tính năng đang phát triển')),
      );
      return;
    }
    context.push('/cloud-sync-settings');
  },
);
```
Logic rải rác ở từng widget. Phải duplicate nếu route được gọi từ nhiều điểm.

**Option 2:**
```dart
// Centralize guard
class NavigationService {
  static bool canNavigateTo(String route) => switch (route) {
    '/cloud-sync-settings' => FeatureFlags.cloudSync,
    _ => true,
  };

  static void navigateSafe(BuildContext context, String route) {
    if (!canNavigateTo(route)) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Tính năng đang phát triển')),
      );
      return;
    }
    context.push(route);
  }
}

// GoRouter redirect guard
GoRoute(
  path: '/cloud-sync-settings',
  redirect: (context, state) => FeatureFlags.cloudSync ? null : '/settings',
  builder: (_, __) => CloudSyncSettingsPage(),
),
```
Guard tập trung, bật feature chỉ cần sửa 1 chỗ. Widget gọi `NavigationService.navigateSafe(context, '/cloud-sync-settings')`.

- Winner: **Option 2**
- Reason: Option 2 tập trung guard vào 1 nơi, dễ bật lại feature sau. Option 1 rải if-else ở nhiều widget gây rủi ro bỏ sót.

---

## Task T3 — Platform Integration

- Prompt / scenario: Add a first-home-entry camera permission prompt in Flutter with iOS and Android behavior separated cleanly and no startup jank.

**Option 1:**
```dart
// Trong initState của HomePage
@override
void initState() {
  super.initState();
  Permission.camera.request(); // block UI nếu show dialog
}
```
Gọi trong `initState` gây jank. Không xử lý denied permanently. Không tách iOS/Android.

**Option 2:**
```dart
class PermissionService {
  static Future<void> requestCameraIfNeeded() async {
    final pref = await SharedPreferences.getInstance();
    if (pref.getBool('camera_requested') == true) return;

    try {
      final status = await Permission.camera.request();
      await pref.setBool('camera_requested', true);

      if (status.isPermanentlyDenied) {
        await openAppSettings();
      }
    } catch (e) {
      // Một số Android ROM throw — catch để không crash
      debugPrint('Permission request failed: $e');
    }
  }
}

// Gọi sau first frame để tránh startup jank
class HomePageState extends State<HomePage> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      PermissionService.requestCameraIfNeeded();
    });
  }
}
// iOS: NSCameraUsageDescription trong Info.plist
// Android: <uses-permission android:name="android.permission.CAMERA"/>
```

- Winner: **Option 2**
- Reason: Option 2 tránh jank bằng `addPostFrameCallback`, handle `isPermanentlyDenied` để user không bị stuck, và lưu SharedPreferences tránh hỏi lại mỗi lần. Option 1 là anti-pattern.

---

## Task T4 — Code Review

- Prompt / scenario: Review a Flutter MR that moves paywall purchase errors from an inline blocking message to SnackBars and removes a native platform-channel workaround in favor of the official plugin API.

**Option 1:**
```
LGTM. Cách tiếp cận SnackBar hợp lý, giao diện gọn hơn.
Minor: đặt tên biến rõ ràng hơn một chút.
Approve.
```
Không kiểm tra error state coverage, không check dispose, không đề cập test.

**Option 2:**
```
## Review — MR Payment Error Refactor

**State coverage** ✅
- `PurchaseErrorState` vẫn được emit đúng flow
- SnackBar dismiss tự động sau 4s — hợp lý cho non-blocking error

**Dispose / memory** ⚠️
- `PurchaseBloc` subscribe `_purchaseStream` nhưng không thấy `cancel()` trong `close()` override
  → Thêm: `_purchaseStreamSub?.cancel()` trong `close()`

**Platform channel removal** ✅
- Bỏ `MethodChannel('purchase/legacy')` — đúng hướng
- Official plugin cover đủ use case

**Test coverage** ⚠️
- Thiếu test cho `PurchaseErrorState` sau khi add fail
  → Thêm `blocTest<PurchaseBloc, PurchaseState>('emits error on purchase fail', ...)`

**Verdict:** Approve conditional on stream dispose fix + 1 error test case.
```

- Winner: **Option 2**
- Reason: Option 2 có checklist cụ thể: state coverage, memory leak, platform change, và test gap. Option 1 bỏ qua memory leak và thiếu test — những bug thật trong production.

---

## Task T5 — Regression Test

- Prompt / scenario: Write a focused Flutter widget/regression test plan for a debt form where validation errors must clear immediately after the user fixes the input.

**Option 1:**
```dart
testWidgets('shows error on invalid input', (tester) async {
  await tester.pumpWidget(DebtFormPage());
  await tester.tap(find.byKey(Key('submit')));
  await tester.pump();
  expect(find.text('Số tiền không hợp lệ'), findsOneWidget);
});
```
Chỉ test hiện error, không test clear error. Miss case chính yêu cầu.

**Option 2:**
```dart
// Test BLoC layer
blocTest<DebtFormCubit, DebtFormState>(
  'clears amount error immediately when user enters valid input',
  build: () => DebtFormCubit(),
  act: (cubit) async {
    cubit.updateAmount('abc');    // invalid → error
    cubit.updateAmount('500000'); // valid → clear
  },
  expect: () => [
    isA<DebtFormState>().having((s) => s.amountError, 'error', isNotNull),
    isA<DebtFormState>().having((s) => s.amountError, 'error', isNull),
  ],
);

// Widget regression test
testWidgets('error clears immediately on valid input', (tester) async {
  await tester.pumpWidget(
    BlocProvider(create: (_) => DebtFormCubit(), child: DebtFormPage()),
  );
  // Trigger error
  await tester.enterText(find.byKey(Key('amount_field')), 'abc');
  await tester.pump();
  expect(find.text('Số tiền không hợp lệ'), findsOneWidget);

  // Fix input — error must clear
  await tester.enterText(find.byKey(Key('amount_field')), '500000');
  await tester.pump();
  expect(find.text('Số tiền không hợp lệ'), findsNothing); // regression check

  // Edge: empty → error returns
  await tester.enterText(find.byKey(Key('amount_field')), '');
  await tester.pump();
  expect(find.text('Số tiền không hợp lệ'), findsOneWidget);
});
```

- Winner: **Option 2**
- Reason: Option 2 test đúng behavior yêu cầu — error CLEAR khi fix. Option 1 chỉ test error SHOW — miss regression case hoàn toàn.

---

## Operator Notes

- Option 1 = baseline (vanilla Flutter knowledge, không có pack context)
- Option 2 = pack-injected (prompt generated qua `distill-build-prompt --role mobile-dev`)
- Model: `claude-sonnet-4-6`, temperature 0 cho cả hai options

## Summary

- Pack wins: **5**
- Baseline wins: 0
- Ties: 0
- Win rate: **100% (5/5)**
- Verdict: **PASS** — win rate `>= 60%` ✅
- Notes: Pack đặc biệt mạnh ở state management isolation và code review checklist. Baseline đúng về direction nhưng thiếu critical detail (dispose, error clear, permission denied path).
