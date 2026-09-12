/// Địa chỉ backend — gom về một chỗ duy nhất (MB-02).
///
/// Điện thoại thật và máy chạy backend phải cùng mạng LAN. `localhost` trên
/// điện thoại là chính điện thoại, không phải máy tính — phải đổi thành IP
/// LAN của máy chạy backend (xem bằng `ipconfig`). Máy ảo Android dùng
/// `10.0.2.2` để trỏ vào `localhost` của máy thật.
class AppConfig {
  const AppConfig._();

  /// Đổi giá trị này khi demo trên điện thoại thật — 'localhost' chỉ đúng khi
  /// chạy app ngay trên máy chạy backend (web/desktop). Trên điện thoại thật
  /// (kể cả build ra APK cài trực tiếp) 'localhost' là chính điện thoại, luôn
  /// không kết nối được. IP LAN hiện tại của máy chạy backend (xem `ipconfig`,
  /// đổi lại nếu máy đổi mạng): 192.168.1.3.
  static const String backendHost = '192.168.1.3';
  static const int backendPort = 8000;

  static String get baseUrl => 'http://$backendHost:$backendPort/api/v1';

  /// Ảnh (`image_url`/`overlay_url`) trả về là đường dẫn tương đối
  /// (`/storage/...`) — ghép với gốc backend, không qua `/api/v1`.
  static String get storageBaseUrl => 'http://$backendHost:$backendPort';
}
