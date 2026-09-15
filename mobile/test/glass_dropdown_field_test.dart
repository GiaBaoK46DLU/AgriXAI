import 'package:agrixai_farmer/widgets/inputs.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

/// Kiểm tra lỗi lọc diễn đàn: chọn lại "Tất cả ..." (tuỳ chọn `null`) sau khi
/// đã chọn một mục cụ thể phải gọi `onChanged(null)` — trước khi sửa,
/// `_open()` coi việc sheet trả về `null` (đóng không chọn gì) và việc chọn
/// tuỳ chọn `null` là một, nên `onChanged` không bao giờ được gọi trong
/// trường hợp thứ hai.
void main() {
  testWidgets('chọn lại tuỳ chọn "Tất cả" gọi onChanged(null)', (WidgetTester tester) async {
    String? current = 'a';
    String? lastChanged = 'unset';

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: StatefulBuilder(
            builder: (BuildContext context, StateSetter setState) {
              return GlassDropdownField<String?>(
                label: current == null ? 'Tất cả' : current!,
                value: current,
                options: const <String?>[null, 'a', 'b'],
                optionLabel: (String? v) => v ?? 'Tất cả',
                onChanged: (String? v) {
                  setState(() {
                    current = v;
                    lastChanged = v;
                  });
                },
              );
            },
          ),
        ),
      ),
    );

    // Mở sheet, hiện đang chọn 'a'.
    await tester.tap(find.text('a'));
    await tester.pumpAndSettle();

    // Chọn "Tất cả" (tuỳ chọn null).
    await tester.tap(find.text('Tất cả').last);
    await tester.pumpAndSettle();

    expect(lastChanged, isNull);
    expect(current, isNull);

    // Mở lại sheet, chọn lại "Tất cả" một lần nữa — trước khi sửa, việc này
    // sẽ không gọi onChanged vì sheet trả về null cho cả hai trường hợp
    // "chọn null" và "đóng không chọn gì".
    lastChanged = 'sentinel-not-called';
    await tester.tap(find.text('Tất cả'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Tất cả').last);
    await tester.pumpAndSettle();

    expect(lastChanged, isNull, reason: 'onChanged phải được gọi lại dù value không đổi');
  });
}
