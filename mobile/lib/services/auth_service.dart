import 'api_client.dart';
import 'token_store.dart';

class CurrentUser {
  const CurrentUser({
    required this.id,
    required this.username,
    required this.fullName,
    required this.role,
  });

  factory CurrentUser.fromJson(Map<String, dynamic> json) => CurrentUser(
        id: json['id'] as int,
        username: json['username'] as String,
        fullName: json['full_name'] as String,
        role: json['role'] as String,
      );

  final int id;
  final String username;
  final String fullName;
  final String role;

  bool get isAdmin => role == 'admin';
}

/// Đăng nhập bằng tài khoản do admin cấp — không có màn tự đăng ký.
///
/// Token lưu bằng `flutter_secure_storage` để sống sót qua lần mở app kế
/// tiếp; nạp lại vào [ApiClient] mỗi lần app khởi động (xem [tryRestore]).
class AuthService {
  AuthService({ApiClient? apiClient, TokenStore? tokenStore})
      : _api = apiClient ?? ApiClient(),
        _tokenStore = tokenStore ?? SecureTokenStore();

  final ApiClient _api;
  final TokenStore _tokenStore;

  ApiClient get apiClient => _api;

  Future<CurrentUser> login(String username, String password) async {
    final dynamic body = await _api.postJson('/auth/login', <String, dynamic>{
      'username': username,
      'password': password,
    });
    final String token = body['access_token'] as String;
    _api.setToken(token);
    await _tokenStore.write(token);
    return me();
  }

  /// Gọi lúc app khởi động — nếu có token đã lưu thì nạp lại và xác nhận
  /// còn hiệu lực. Trả về `null` nếu chưa đăng nhập hoặc token đã hết hạn.
  Future<CurrentUser?> tryRestore() async {
    final String? token = await _tokenStore.read();
    if (token == null) return null;
    _api.setToken(token);
    try {
      return await me();
    } on ApiException {
      await logout();
      return null;
    }
  }

  Future<CurrentUser> me() async {
    final dynamic body = await _api.get('/auth/me');
    return CurrentUser.fromJson(body as Map<String, dynamic>);
  }

  Future<void> logout() async {
    _api.setToken(null);
    await _tokenStore.delete();
  }
}
