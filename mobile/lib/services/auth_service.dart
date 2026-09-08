import 'api_client.dart';
import 'token_store.dart';

class CurrentUser {
  const CurrentUser({
    required this.id,
    required this.username,
    required this.fullName,
    required this.role,
    this.email,
    this.phone,
  });

  factory CurrentUser.fromJson(Map<String, dynamic> json) => CurrentUser(
        id: json['id'] as int,
        username: json['username'] as String,
        fullName: json['full_name'] as String,
        role: json['role'] as String,
        email: json['email'] as String?,
        phone: json['phone'] as String?,
      );

  final int id;
  final String username;
  final String fullName;
  final String role;
  final String? email;
  final String? phone;

  bool get isAdmin => role == 'admin';
}

/// Đăng nhập/đăng ký. Tài khoản `admin` vẫn phải do admin khác cấp qua
/// `POST /users` — tự đăng ký (`POST /auth/register`) chỉ tạo vai trò `farmer`.
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
    return _applyToken(body as Map<String, dynamic>);
  }

  /// Tự đăng ký — đăng nhập luôn sau khi tạo tài khoản thành công, không bắt
  /// người dùng phải quay lại màn Đăng nhập gõ lại mật khẩu vừa nhập.
  Future<CurrentUser> register({
    required String username,
    required String password,
    required String fullName,
    required String email,
    String? phone,
  }) async {
    final dynamic body = await _api.postJson('/auth/register', <String, dynamic>{
      'username': username,
      'password': password,
      'full_name': fullName,
      'email': email,
      if (phone != null && phone.isNotEmpty) 'phone': phone,
    });
    return _applyToken(body as Map<String, dynamic>);
  }

  Future<CurrentUser> _applyToken(Map<String, dynamic> body) async {
    final String token = body['access_token'] as String;
    _api.setToken(token);
    await _tokenStore.write(token);
    return CurrentUser.fromJson(body['user'] as Map<String, dynamic>);
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

  /// Sửa họ tên / số điện thoại. `role`/`email`/`is_active` bị backend bỏ qua
  /// khi tự sửa hồ sơ (chỉ `PATCH /users/{id}` của admin mới đổi được) nên
  /// không nhận tham số ở đây.
  Future<CurrentUser> updateMe({String? fullName, String? phone}) async {
    final dynamic body = await _api.patchJson('/auth/me', <String, dynamic>{
      if (fullName != null) 'full_name': fullName,
      if (phone != null) 'phone': phone,
    });
    return CurrentUser.fromJson(body as Map<String, dynamic>);
  }

  Future<void> changePassword(String newPassword) async {
    await _api.patchJson('/auth/me', <String, dynamic>{'password': newPassword});
  }

  Future<void> logout() async {
    _api.setToken(null);
    await _tokenStore.delete();
  }
}
