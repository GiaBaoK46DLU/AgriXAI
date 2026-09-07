import 'dart:convert';

import 'package:agrixai_farmer/data/demo_data.dart';
import 'package:agrixai_farmer/main.dart';
import 'package:agrixai_farmer/models/models.dart';
import 'package:agrixai_farmer/screens/app_shell.dart';
import 'package:agrixai_farmer/services/api_client.dart';
import 'package:agrixai_farmer/services/auth_service.dart';
import 'package:agrixai_farmer/services/session.dart' as session;
import 'package:agrixai_farmer/services/token_store.dart';
import 'package:agrixai_farmer/widgets/chips.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

/// Token giả, không lưu gì thật — thay `SecureTokenStore` để không đụng
/// platform channel của `flutter_secure_storage` (không chạy được trong
/// `flutter test`, chỉ có trên thiết bị thật).
class _FakeTokenStore implements TokenStore {
  String? _token;

  @override
  Future<void> delete() async => _token = null;

  @override
  Future<String?> read() async => _token;

  @override
  Future<void> write(String token) async => _token = token;
}

Map<String, dynamic> _diseaseJson(Disease d) => <String, dynamic>{
      'key': d.key,
      'name_vi': d.name,
      'name_en': d.en,
      'pathogen': d.pathogen,
      'is_healthy': d.type == PathogenType.healthy,
      'symptoms': d.symptoms,
      'visual_cue': d.cue,
      'favorable_conditions': d.conditions,
      'treatments': d.treatments,
      'prevention': d.prevention,
      'products': const <dynamic>[],
      'video_url': null,
    };

/// `http.Response(String, ...)` mã hoá thân bằng latin1 theo mặc định — chữ
/// tiếng Việt sẽ hỏng và `ApiClient._decode` (giải bằng UTF-8) ném lỗi. Dùng
/// `.bytes` để tự mã hoá UTF-8, không phụ thuộc mặc định của gói `http`.
http.Response _jsonResponse(Object data) {
  return http.Response.bytes(
    utf8.encode(jsonEncode(data)),
    200,
    headers: <String, String>{'content-type': 'application/json'},
  );
}

/// Server giả — không gọi mạng thật. Trả đúng hình dạng JSON mà
/// `ApiClient`/các model `fromJson` mong đợi, dựng từ chính [DemoData] để
/// không phải chép tay một bộ dữ liệu thứ hai.
http.Client _fakeBackend() {
  return MockClient((http.Request request) async {
    final String path = request.url.path;

    if (path.endsWith('/auth/login')) {
      return _jsonResponse(<String, dynamic>{'access_token': 'fake-token'});
    }
    if (path.endsWith('/auth/me')) {
      return _jsonResponse(<String, dynamic>{
        'id': 1,
        'username': 'nongdan',
        'full_name': 'Nông dân thử nghiệm',
        'role': 'farmer',
      });
    }
    if (path.endsWith('/diseases')) {
      return _jsonResponse(DemoData.diseases.map(_diseaseJson).toList());
    }
    if (path.endsWith('/plots')) {
      return _jsonResponse(const <dynamic>[]);
    }
    return http.Response('Not found', 404);
  });
}

void _installFakeSession() {
  session.apiClient = ApiClient(httpClient: _fakeBackend());
  session.authService = AuthService(
    apiClient: session.apiClient,
    tokenStore: _FakeTokenStore(),
  );
}

Future<void> _login(WidgetTester tester) async {
  final Finder fields = find.byType(TextField);
  await tester.enterText(fields.at(0), 'nongdan');
  await tester.enterText(fields.at(1), 'nongdan123');
  await tester.tap(find.text('Đăng nhập'));
  await tester.pumpAndSettle();
}

void main() {
  setUp(_installFakeSession);

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

    await _login(tester);

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
    await _login(tester);

    await tester.tap(find.text('Lịch sử'));
    await tester.pumpAndSettle();

    expect(find.text('6 lần chẩn đoán'), findsOneWidget);

    // Chữ "Nặng" xuất hiện hai chỗ: chip lọc và chip mức độ của hàng 101.
    // Phải chỉ đúng chip lọc, nếu không `tap` gặp hai kết quả và ném lỗi.
    await tester.tap(find.widgetWithText(SelectableChip, 'Nặng'));
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
