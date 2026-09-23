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
        _tokenStore = tokenStore ?? SecureTokenStore() {
    // ApiClient tự làm mới access token khi gặp 401 hết phiên (xem
    // `api_client.dart`) — mỗi lần làm mới thành công phải ghi đè lại
    // `TokenStore` để lần mở app kế tiếp không dùng phải refresh token cũ
    // (đã bị thu hồi do cơ chế xoay vòng).
    _api.onTokensRefreshed = (String accessToken, String refreshToken) {
      _tokenStore.write(accessToken);
      _tokenStore.writeRefresh(refreshToken);
    };
  }

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
    final String refreshToken = body['refresh_token'] as String;
    _api.setToken(token);
    _api.setRefreshToken(refreshToken);
    await _tokenStore.write(token);
    await _tokenStore.writeRefresh(refreshToken);
    return CurrentUser.fromJson(body['user'] as Map<String, dynamic>);
  }

  /// Gọi lúc app khởi động — nếu có token đã lưu thì nạp lại và xác nhận
  /// còn hiệu lực. Trả về `null` nếu chưa đăng nhập hoặc cả access lẫn
  /// refresh token đều đã hết hạn.
  ///
  /// Nạp cả refresh token vào [ApiClient] trước khi gọi [me] — access token
  /// đã lưu có thể đã hết hạn (chỉ sống 30 phút) trong lúc app đóng, lúc đó
  /// [ApiClient] tự làm mới token ở nền (xem `api_client.dart`) nên người
  /// dùng vẫn vào thẳng app, không phải đăng nhập lại mỗi khi mở app sau một
  /// lúc lâu.
  Future<CurrentUser?> tryRestore() async {
    final String? token = await _tokenStore.read();
    final String? refreshToken = await _tokenStore.readRefresh();
    if (token == null || refreshToken == null) return null;
    _api.setToken(token);
    _api.setRefreshToken(refreshToken);
    try {
      return await me();
    } on ApiException {
      await logout();
      return null;
    } on SessionExpiredException {
      // ApiClient đã tự dọn token trong bộ nhớ khi refresh thất bại — chỉ
      // còn phải dọn nốt TokenStore, không gọi lại `/auth/logout` (refresh
      // token lúc này chắc chắn đã không còn hợp lệ để thu hồi).
      await _tokenStore.delete();
      await _tokenStore.deleteRefresh();
      return null;
    } on NetworkException {
      // Mất mạng lúc khởi động không có nghĩa phiên đã hết hạn — giữ
      // nguyên token trong TokenStore (không logout), chỉ coi như chưa
      // xác nhận được để _StartupGate không treo vô thời hạn. Mở lại app
      // khi có mạng thì tryRestore() chạy lại và tự đăng nhập như cũ.
      return null;
    }
  }

  Future<CurrentUser> me() async {
    final dynamic body = await _api.get('/auth/me');
    return CurrentUser.fromJson(body as Map<String, dynamic>);
  }

  /// Sửa họ tên / số điện thoại — `PATCH /auth/me`. Không nhận mật khẩu qua
  /// đường này, xem [changePassword].
  Future<CurrentUser> updateMe({String? fullName, String? phone}) async {
    final dynamic body = await _api.patchJson('/auth/me', <String, dynamic>{
      if (fullName != null) 'full_name': fullName,
      if (phone != null) 'phone': phone,
    });
    return CurrentUser.fromJson(body as Map<String, dynamic>);
  }

  /// Đổi mật khẩu tự phục vụ — bắt buộc đúng mật khẩu hiện tại
  /// (`POST /auth/change-password`), khác `updateMe` vốn không nhận mật khẩu.
  Future<void> changePassword({
    required String currentPassword,
    required String newPassword,
  }) async {
    await _api.postJson('/auth/change-password', <String, dynamic>{
      'current_password': currentPassword,
      'new_password': newPassword,
    });
  }

  /// Thu hồi refresh token phía server (`POST /auth/logout`) trước khi xoá
  /// khỏi máy — chỉ xoá cục bộ thì token thô vẫn dùng làm mới access token
  /// được nếu ai đó có được nó. Không chặn đăng xuất nếu gọi backend thất
  /// bại (mất mạng...) — với người dùng, đăng xuất trên máy phải luôn thành
  /// công; token hết hạn tự nhiên sau `REFRESH_TOKEN_EXPIRE_DAYS` dù không
  /// thu hồi được ngay.
  Future<void> logout() async {
    final String? refreshToken = await _tokenStore.readRefresh();
    if (refreshToken != null) {
      try {
        await _api.postJson('/auth/logout', <String, dynamic>{
          'refresh_token': refreshToken,
        });
      } catch (_) {
        // Xem ghi chú ở trên — bỏ qua, vẫn xoá cục bộ.
      }
    }
    _api.setToken(null);
    _api.setRefreshToken(null);
    await _tokenStore.delete();
    await _tokenStore.deleteRefresh();
  }
}
