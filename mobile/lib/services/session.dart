import 'api_client.dart';
import 'auth_service.dart';
import 'diagnosis_service.dart';
import 'disease_service.dart';
import 'forum_service.dart';
import 'weather_service.dart';

/// Một `ApiClient` dùng chung cho cả app, để token đăng nhập một lần dùng
/// được ở mọi màn hình. Không dùng khung DI riêng — dự án nhỏ, một singleton
/// đơn giản là đủ.
///
/// Cố tình không phải `final`: widget test thay cả bốn biến này bằng bản
/// dùng `http.Client`/`TokenStore` giả trước khi `pumpWidget`, để không đụng
/// mạng thật hay platform channel của `flutter_secure_storage`.
ApiClient apiClient = ApiClient();
AuthService authService = AuthService(apiClient: apiClient);
DiseaseService diseaseService = DiseaseService(apiClient: apiClient);
DiagnosisService diagnosisService = DiagnosisService(apiClient: apiClient);
ForumService forumService = ForumService(apiClient: apiClient);
WeatherService weatherService = WeatherService(apiClient: apiClient);

CurrentUser? currentUser;
