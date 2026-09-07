import 'dart:convert';

import 'package:http/http.dart' as http;

import '../core/app_config.dart';

/// Lỗi khi backend trả về mã không phải 2xx — mang theo thông báo lấy từ
/// trường `detail` của FastAPI để hiện thẳng lên UI, không cần đoán.
class ApiException implements Exception {
  ApiException(this.statusCode, this.message);

  final int statusCode;
  final String message;

  @override
  String toString() => 'ApiException($statusCode, $message)';
}

/// Lớp gọi HTTP dùng chung cho toàn app.
///
/// `httpClient` truyền vào được để widget test tiêm một client giả — không
/// bên nào trong app gọi `http.get`/`http.post` trực tiếp ngoài lớp này.
class ApiClient {
  ApiClient({http.Client? httpClient}) : _http = httpClient ?? http.Client();

  final http.Client _http;
  String? _token;

  void setToken(String? token) => _token = token;

  Map<String, String> get _headers => <String, String>{
        'Content-Type': 'application/json',
        if (_token != null) 'Authorization': 'Bearer $_token',
      };

  Uri _uri(String path) => Uri.parse('${AppConfig.baseUrl}$path');

  dynamic _decode(http.Response response) {
    final int code = response.statusCode;
    if (code < 200 || code >= 300) {
      String message = 'Lỗi máy chủ ($code)';
      try {
        final dynamic body = jsonDecode(response.body);
        if (body is Map && body['detail'] != null) {
          message = body['detail'].toString();
        }
      } catch (_) {
        // Không parse được thì dùng thông báo mặc định ở trên.
      }
      throw ApiException(code, message);
    }
    if (response.body.isEmpty) return null;
    return jsonDecode(utf8.decode(response.bodyBytes));
  }

  Future<dynamic> get(String path) async {
    final http.Response response =
        await _http.get(_uri(path), headers: _headers);
    return _decode(response);
  }

  Future<dynamic> postJson(String path, Map<String, dynamic> body) async {
    final http.Response response = await _http.post(
      _uri(path),
      headers: _headers,
      body: jsonEncode(body),
    );
    return _decode(response);
  }

  Future<dynamic> patchJson(String path, Map<String, dynamic> body) async {
    final http.Response response = await _http.patch(
      _uri(path),
      headers: _headers,
      body: jsonEncode(body),
    );
    return _decode(response);
  }

  /// Gửi ảnh dạng `multipart/form-data` — dùng cho `POST /diagnoses`.
  Future<dynamic> postMultipart(
    String path, {
    required String fileField,
    required List<int> fileBytes,
    required String filename,
    Map<String, String> fields = const <String, String>{},
  }) async {
    final http.MultipartRequest request =
        http.MultipartRequest('POST', _uri(path));
    if (_token != null) {
      request.headers['Authorization'] = 'Bearer $_token';
    }
    request.fields.addAll(fields);
    request.files.add(http.MultipartFile.fromBytes(
      fileField,
      fileBytes,
      filename: filename,
    ));

    final http.StreamedResponse streamed = await _http
        .send(request)
        .timeout(const Duration(seconds: 8));
    final http.Response response = await http.Response.fromStream(streamed);
    return _decode(response);
  }
}
