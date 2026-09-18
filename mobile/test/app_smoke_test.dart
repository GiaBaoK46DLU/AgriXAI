import 'dart:convert';

import 'package:agrixai_farmer/data/demo_data.dart';
import 'package:agrixai_farmer/main.dart';
import 'package:agrixai_farmer/models/models.dart';
import 'package:agrixai_farmer/screens/app_shell.dart';
import 'package:agrixai_farmer/services/api_client.dart';
import 'package:agrixai_farmer/services/auth_service.dart';
import 'package:agrixai_farmer/services/diagnosis_service.dart';
import 'package:agrixai_farmer/services/disease_service.dart';
import 'package:agrixai_farmer/services/forum_service.dart';
import 'package:agrixai_farmer/services/session.dart' as session;
import 'package:agrixai_farmer/services/token_store.dart';
import 'package:agrixai_farmer/services/weather_service.dart';
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
  String? _refreshToken;

  @override
  Future<void> delete() async => _token = null;

  @override
  Future<String?> read() async => _token;

  @override
  Future<void> write(String token) async => _token = token;

  @override
  Future<void> deleteRefresh() async => _refreshToken = null;

  @override
  Future<String?> readRefresh() async => _refreshToken;

  @override
  Future<void> writeRefresh(String token) async => _refreshToken = token;
}

/// Sáu bản ghi chẩn đoán giả — đủ để kiểm được cả tổng số lẫn lọc theo mức độ
/// ("lọc lịch sử theo mức độ" cần đúng 6 bản ghi, 1 bản ở mức "severe").
final List<Map<String, dynamic>> _fakeDiagnoses = <Map<String, dynamic>>[
  <String, dynamic>{
    'id': 101,
    'disease_key': 'late_blight',
    'disease_name': 'Mốc sương muộn',
    'severity': 'severe',
    'confidence': 0.94,
    'plot_id': 1,
    'plot_name': 'Vườn nhà trên',
    'plot_puc': 'PUC-2608-0142',
    'created_at': '2026-01-01T07:12:00Z',
  },
  <String, dynamic>{
    'id': 102,
    'disease_key': 'septoria_leaf_spot',
    'disease_name': 'Đốm lá Septoria',
    'severity': 'mild',
    'confidence': 0.81,
    'plot_id': 1,
    'plot_name': 'Vườn nhà trên',
    'plot_puc': 'PUC-2608-0142',
    'created_at': '2025-12-31T16:40:00Z',
  },
  <String, dynamic>{
    'id': 103,
    'disease_key': 'leaf_mold',
    'disease_name': 'Mốc lá',
    'severity': 'moderate',
    'confidence': 0.88,
    'plot_id': 2,
    'plot_name': 'Nhà màng số 2',
    'plot_puc': 'PUC-2607-0088',
    'created_at': '2025-12-29T08:05:00Z',
  },
  <String, dynamic>{
    'id': 104,
    'disease_key': 'spider_mites',
    'disease_name': 'Nhện đỏ hai chấm',
    'severity': 'mild',
    'confidence': 0.87,
    'plot_id': 2,
    'plot_name': 'Nhà màng số 2',
    'plot_puc': 'PUC-2607-0088',
    'created_at': '2025-12-27T15:22:00Z',
  },
  <String, dynamic>{
    'id': 105,
    'disease_key': 'healthy',
    'disease_name': 'Lá khoẻ mạnh',
    'severity': 'none',
    'confidence': 0.97,
    'plot_id': 3,
    'plot_name': 'Ruộng ven suối',
    'plot_puc': 'PUC-2605-0031',
    'created_at': '2025-12-25T09:30:00Z',
  },
  <String, dynamic>{
    'id': 106,
    'disease_key': 'early_blight',
    'disease_name': 'Đốm vòng (đốm nâu)',
    'severity': 'moderate',
    'confidence': 0.90,
    'plot_id': 1,
    'plot_name': 'Vườn nhà trên',
    'plot_puc': 'PUC-2608-0142',
    'created_at': '2025-12-23T17:10:00Z',
  },
];

Map<String, dynamic> _fakeWeatherJson() => <String, dynamic>{
      'location': 'Đà Lạt',
      'temp': 22,
      'description': 'mây rải rác',
      'detail': 'Độ ẩm 70% · gió nhẹ · trời quang',
      'advisory': null,
      'forecast': <dynamic>[
        <String, dynamic>{'day': 'T5', 'temp': 22, 'is_now': true},
      ],
    };

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

    final Map<String, dynamic> user = <String, dynamic>{
      'id': 1,
      'username': 'nongdan',
      'full_name': 'Nông dân thử nghiệm',
      'role': 'farmer',
    };

    if (path.endsWith('/auth/login')) {
      return _jsonResponse(<String, dynamic>{
        'access_token': 'fake-token',
        'refresh_token': 'fake-refresh-token',
        'user': user,
      });
    }
    if (path.endsWith('/auth/me')) {
      return _jsonResponse(user);
    }
    if (path.endsWith('/diseases')) {
      return _jsonResponse(DemoData.diseases.map(_diseaseJson).toList());
    }
    if (path.endsWith('/weather')) {
      return _jsonResponse(_fakeWeatherJson());
    }
    if (path.endsWith('/diagnoses')) {
      final Map<String, String> query = request.url.queryParameters;
      final String? severity = query['severity'];
      final int pageSize = int.tryParse(query['page_size'] ?? '') ?? 20;
      final List<Map<String, dynamic>> filtered = _fakeDiagnoses
          .where((Map<String, dynamic> d) => severity == null || d['severity'] == severity)
          .toList();
      return _jsonResponse(<String, dynamic>{
        'items': filtered.take(pageSize).toList(),
        'total': filtered.length,
        'page': 1,
        'page_size': pageSize,
      });
    }
    if (path.endsWith('/plots')) {
      return _jsonResponse(const <dynamic>[]);
    }
    return http.Response('Not found', 404);
  });
}

/// Dựng lại TOÀN BỘ service dùng chung bằng cùng một `ApiClient` giả — thiếu
/// một cái nào đó vẫn giữ `ApiClient` thật mặc định của `session.dart` (dùng
/// `http.Client()` mạng thật), khiến test lặng lẽ gọi ra backend thật đang
/// chạy trên máy thay vì `MockClient` ở trên (đã từng xảy ra với
/// `diseaseService`/`diagnosisService`/`weatherService` trước khi sửa).
void _installFakeSession() {
  final ApiClient fakeApi = ApiClient(httpClient: _fakeBackend());
  session.apiClient = fakeApi;
  session.authService = AuthService(apiClient: fakeApi, tokenStore: _FakeTokenStore());
  session.diseaseService = DiseaseService(apiClient: fakeApi);
  session.diagnosisService = DiagnosisService(apiClient: fakeApi);
  session.forumService = ForumService(apiClient: fakeApi);
  session.weatherService = WeatherService(apiClient: fakeApi);
  session.currentUser = null;
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
    await tester.pumpAndSettle();

    expect(find.text('AgriXAI'), findsOneWidget);
    expect(find.text('Đăng nhập'), findsOneWidget);
    // Đã bỏ hẳn màn dùng thử không cần đăng nhập (xem CLAUDE.md).
    expect(find.text('Tra cứu bệnh mà không cần đăng nhập'), findsNothing);
  });

  testWidgets('đăng nhập xong vào trang chủ, có thanh tab',
      (WidgetTester tester) async {
    await tester.pumpWidget(const AgriXaiFarmerApp());
    await tester.pump();

    await _login(tester);

    expect(find.byType(AppShell), findsOneWidget);
    // Tên hiển thị là từ cuối của họ tên đầy đủ (đúng vị trí tên gọi trong
    // tên người Việt) — tài khoản giả `Nông dân thử nghiệm` -> "nghiệm".
    expect(find.text('Chào bác nghiệm'), findsOneWidget);
    expect(find.text('Lô đất của bạn'), findsOneWidget);
    // Năm nhãn của thanh tab — không còn nút camera nổi ở giữa (xem
    // CLAUDE.md mục Diễn đàn nông dân).
    expect(find.text('Diễn đàn'), findsOneWidget);
    expect(find.text('Trang chủ'), findsOneWidget);
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
    // Đã bỏ hẳn màn dùng thử không cần đăng nhập — phải đăng nhập trước rồi
    // mới vào được tab Danh mục (xem CLAUDE.md).
    await _login(tester);
    await tester.tap(find.text('Danh mục'));
    await tester.pumpAndSettle();

    expect(find.text('Mốc sương muộn'), findsOneWidget);

    await tester.enterText(find.byType(TextField).first, 'nhện');
    await tester.pumpAndSettle();

    expect(find.text('Nhện đỏ hai chấm'), findsOneWidget);
    expect(find.text('Mốc sương muộn'), findsNothing);
  });
}
