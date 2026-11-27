import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// Chỗ lưu access token + refresh token — tách khỏi `FlutterSecureStorage`
/// cụ thể để widget test tiêm được bản giả (plugin thật gọi platform
/// channel, không chạy được trong `flutter test`).
abstract class TokenStore {
  Future<String?> read();
  Future<void> write(String token);
  Future<void> delete();

  Future<String?> readRefresh();
  Future<void> writeRefresh(String token);
  Future<void> deleteRefresh();

  /// Hồ sơ người dùng (chuỗi JSON) của phiên đang lưu — để mở được app khi
  /// mất mạng, xem `AuthService.tryRestore`.
  Future<String?> readUser();
  Future<void> writeUser(String userJson);
  Future<void> deleteUser();
}

class SecureTokenStore implements TokenStore {
  SecureTokenStore([FlutterSecureStorage? storage])
      : _storage = storage ?? const FlutterSecureStorage();

  static const String _key = 'agrixai_token';
  static const String _refreshKey = 'agrixai_refresh_token';
  static const String _userKey = 'agrixai_user';

  final FlutterSecureStorage _storage;

  @override
  Future<String?> read() => _storage.read(key: _key);

  @override
  Future<void> write(String token) => _storage.write(key: _key, value: token);

  @override
  Future<void> delete() => _storage.delete(key: _key);

  @override
  Future<String?> readRefresh() => _storage.read(key: _refreshKey);

  @override
  Future<void> writeRefresh(String token) =>
      _storage.write(key: _refreshKey, value: token);

  @override
  Future<void> deleteRefresh() => _storage.delete(key: _refreshKey);

  @override
  Future<String?> readUser() => _storage.read(key: _userKey);

  @override
  Future<void> writeUser(String userJson) =>
      _storage.write(key: _userKey, value: userJson);

  @override
  Future<void> deleteUser() => _storage.delete(key: _userKey);
}
