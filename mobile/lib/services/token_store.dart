import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// Chỗ lưu JWT — tách khỏi `FlutterSecureStorage` cụ thể để widget test tiêm
/// được bản giả (plugin thật gọi platform channel, không chạy được trong
/// `flutter test`).
abstract class TokenStore {
  Future<String?> read();
  Future<void> write(String token);
  Future<void> delete();
}

class SecureTokenStore implements TokenStore {
  SecureTokenStore([FlutterSecureStorage? storage])
      : _storage = storage ?? const FlutterSecureStorage();

  static const String _key = 'agrixai_token';

  final FlutterSecureStorage _storage;

  @override
  Future<String?> read() => _storage.read(key: _key);

  @override
  Future<void> write(String token) => _storage.write(key: _key, value: token);

  @override
  Future<void> delete() => _storage.delete(key: _key);
}
