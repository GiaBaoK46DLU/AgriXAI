import '../models/models.dart';
import 'api_client.dart';

/// Ô thời tiết ở trang chủ — `GET /weather`. Công khai, không cần đăng nhập
/// (xem `backend/app/api/v1/endpoints/weather.py`).
class WeatherService {
  WeatherService({ApiClient? apiClient}) : _api = apiClient ?? ApiClient();

  final ApiClient _api;

  Future<WeatherSnapshot> fetch() async {
    final dynamic body = await _api.get('/weather');
    return WeatherSnapshot.fromJson(body as Map<String, dynamic>);
  }
}
