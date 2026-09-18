import 'dart:async';
import 'dart:convert';
import 'dart:io';

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

/// Mất mạng (không có `SocketException` bắt được, timeout hết hạn...) —
/// tách khỏi [ApiException] (backend có trả lời, chỉ là báo lỗi) để UI hiện
/// đúng thông báo cho từng trường hợp thay vì gộp chung "lỗi máy chủ".
class NetworkException implements Exception {
  NetworkException([
    this.message = 'Không có kết nối mạng. Kiểm tra Wi-Fi rồi thử lại.',
  ]);

  final String message;

  @override
  String toString() => message;
}

/// Access token hết hạn VÀ refresh token cũng không làm mới được (hết hạn,
/// đã thu hồi, hoặc tài khoản bị khoá). [ApiClient] đã tự gọi
/// [ApiClient.onSessionExpired] (dọn phiên + điều hướng về màn Đăng nhập)
/// trước khi ném lỗi này — nơi gọi API chỉ cần dừng loading, không cần tự
/// điều hướng lại.
class SessionExpiredException implements Exception {
  const SessionExpiredException();
}

/// Lớp gọi HTTP dùng chung cho toàn app.
///
/// `httpClient` truyền vào được để widget test tiêm một client giả — không
/// bên nào trong app gọi `http.get`/`http.post` trực tiếp ngoài lớp này.
///
/// Tự làm mới access token khi gặp 401 kèm header `WWW-Authenticate` (chỉ
/// `get_current_user` ở backend gắn header này — lỗi 401 "nghiệp vụ" như sai
/// mật khẩu hiện tại ở đổi mật khẩu KHÔNG có header đó, nên không bị hiểu
/// nhầm thành hết phiên). Xem `backend/app/api/deps.py`.
class ApiClient {
  ApiClient({http.Client? httpClient}) : _http = httpClient ?? http.Client();

  static const Duration _requestTimeout = Duration(seconds: 12);
  static const Duration _uploadTimeout = Duration(seconds: 20);

  final http.Client _http;
  String? _token;
  String? _refreshToken;

  /// Gọi mỗi khi `ApiClient` tự làm mới token thành công — nơi gán
  /// (`AuthService`) dùng để lưu lại token mới vào `TokenStore`.
  void Function(String accessToken, String refreshToken)? onTokensRefreshed;

  /// Gọi khi không còn cách nào lấy access token hợp lệ nữa — nơi gán
  /// (`main.dart`) chịu trách nhiệm xoá phiên và đưa người dùng về màn
  /// Đăng nhập.
  void Function()? onSessionExpired;

  void setToken(String? token) => _token = token;

  void setRefreshToken(String? token) => _refreshToken = token;

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

  /// Chạy [send], bắt mất mạng/timeout thành [NetworkException], và khi gặp
  /// 401 hết phiên thì tự làm mới token rồi gọi lại [send] đúng một lần.
  Future<http.Response> _guarded(Future<http.Response> Function() send) async {
    http.Response response = await _runCatchingNetwork(send);
    if (!_looksLikeExpiredSession(response)) return response;
    if (_refreshToken == null) return response;

    final bool refreshed = await _tryRefresh();
    if (refreshed) {
      response = await _runCatchingNetwork(send);
      if (!_looksLikeExpiredSession(response)) return response;
    }

    _token = null;
    _refreshToken = null;
    onSessionExpired?.call();
    throw const SessionExpiredException();
  }

  bool _looksLikeExpiredSession(http.Response response) {
    if (response.statusCode != 401) return false;
    // Header chỉ được `get_current_user` gắn — 401 "nghiệp vụ" (sai mật khẩu
    // hiện tại, sai tài khoản lúc đăng nhập...) không có header này.
    return response.headers.containsKey('www-authenticate');
  }

  Future<http.Response> _runCatchingNetwork(
    Future<http.Response> Function() send,
  ) async {
    try {
      return await send();
    } on SocketException {
      throw NetworkException();
    } on TimeoutException {
      throw NetworkException();
    }
  }

  Future<bool> _tryRefresh() async {
    final String? refreshToken = _refreshToken;
    if (refreshToken == null) return false;
    try {
      final http.Response response = await _http
          .post(
            _uri('/auth/refresh'),
            headers: const <String, String>{'Content-Type': 'application/json'},
            body: jsonEncode(<String, String>{'refresh_token': refreshToken}),
          )
          .timeout(_requestTimeout);
      if (response.statusCode != 200) return false;
      final Map<String, dynamic> body =
          jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
      final String newAccess = body['access_token'] as String;
      final String newRefresh = body['refresh_token'] as String;
      _token = newAccess;
      _refreshToken = newRefresh;
      onTokensRefreshed?.call(newAccess, newRefresh);
      return true;
    } catch (_) {
      return false;
    }
  }

  Future<dynamic> get(String path) async {
    final http.Response response = await _guarded(
      () => _http.get(_uri(path), headers: _headers).timeout(_requestTimeout),
    );
    return _decode(response);
  }

  Future<dynamic> postJson(String path, Map<String, dynamic> body) async {
    final http.Response response = await _guarded(
      () => _http
          .post(_uri(path), headers: _headers, body: jsonEncode(body))
          .timeout(_requestTimeout),
    );
    return _decode(response);
  }

  Future<dynamic> patchJson(String path, Map<String, dynamic> body) async {
    final http.Response response = await _guarded(
      () => _http
          .patch(_uri(path), headers: _headers, body: jsonEncode(body))
          .timeout(_requestTimeout),
    );
    return _decode(response);
  }

  Future<dynamic> delete(String path) async {
    final http.Response response = await _guarded(
      () => _http.delete(_uri(path), headers: _headers).timeout(_requestTimeout),
    );
    return _decode(response);
  }

  /// Gửi nhiều ảnh dạng `multipart/form-data`, cùng dưới một tên trường —
  /// dùng cho `POST /diagnoses` (3–5 ảnh dưới trường `files`).
  Future<dynamic> postMultipartFiles(
    String path, {
    required String fileField,
    required List<({List<int> bytes, String filename})> files,
    Map<String, String> fields = const <String, String>{},
  }) async {
    Future<http.Response> send() async {
      final http.MultipartRequest request =
          http.MultipartRequest('POST', _uri(path));
      if (_token != null) {
        request.headers['Authorization'] = 'Bearer $_token';
      }
      request.fields.addAll(fields);
      for (final ({List<int> bytes, String filename}) file in files) {
        request.files.add(http.MultipartFile.fromBytes(
          fileField,
          file.bytes,
          filename: file.filename,
        ));
      }

      final http.StreamedResponse streamed =
          await _http.send(request).timeout(_uploadTimeout);
      return http.Response.fromStream(streamed);
    }

    final http.Response response = await _guarded(send);
    return _decode(response);
  }
}
