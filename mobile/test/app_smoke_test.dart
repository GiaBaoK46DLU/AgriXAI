import 'package:agrixai_farmer/main.dart';
import 'package:agrixai_farmer/screens/app_shell.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('mở app vào màn đăng nhập', (WidgetTester tester) async {
    await tester.pumpWidget(const AgriXaiFarmerApp());
    await tester.pump();

    expect(find.text('AgriXAI'), findsOneWidget);
    expect(find.text('Đăng nhập'), findsOneWidget);
    expect(
      find.text('Tra cứu bệnh mà không cần đăng nhập'),
      findsOneWidget,
    );
  });

  testWidgets('đăng nhập xong vào trang chủ, có thanh tab',
      (WidgetTester tester) async {
    await tester.pumpWidget(const AgriXaiFarmerApp());
    await tester.pump();

    await tester.tap(find.text('Đăng nhập'));
    await tester.pumpAndSettle();

    expect(find.byType(AppShell), findsOneWidget);
    expect(find.text('Chào anh Học'), findsOneWidget);
    expect(find.text('Lô đất của bạn'), findsOneWidget);
    // Năm ô của thanh tab: bốn nhãn + nút camera ở giữa.
    expect(find.text('Lô đất'), findsOneWidget);
    expect(find.text('Danh mục'), findsOneWidget);
  });

  testWidgets('lọc lịch sử theo mức độ', (WidgetTester tester) async {
    await tester.pumpWidget(const AgriXaiFarmerApp());
    await tester.pump();
    await tester.tap(find.text('Đăng nhập'));
    await tester.pumpAndSettle();

    await tester.tap(find.text('Lịch sử'));
    await tester.pumpAndSettle();

    expect(find.text('6 lần chẩn đoán'), findsOneWidget);

    await tester.tap(find.text('Nặng'));
    await tester.pumpAndSettle();

    expect(find.text('1 lần chẩn đoán ở mức nặng'), findsOneWidget);
  });

  testWidgets('danh mục bệnh lọc được theo tên', (WidgetTester tester) async {
    await tester.pumpWidget(const AgriXaiFarmerApp());
    await tester.pump();
    await tester.tap(find.text('Tra cứu bệnh mà không cần đăng nhập'));
    await tester.pumpAndSettle();

    expect(find.text('Mốc sương muộn'), findsOneWidget);

    await tester.enterText(find.byType(TextField).first, 'nhện');
    await tester.pumpAndSettle();

    expect(find.text('Nhện đỏ hai chấm'), findsOneWidget);
    expect(find.text('Mốc sương muộn'), findsNothing);
  });
}
