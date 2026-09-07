import '../models/models.dart';
import 'api_client.dart';

/// Danh mục bệnh — công khai, không cần đăng nhập.
class DiseaseService {
  DiseaseService({ApiClient? apiClient}) : _api = apiClient ?? ApiClient();

  final ApiClient _api;

  Future<List<Disease>> fetchAll() async {
    final dynamic body = await _api.get('/diseases');
    return (body as List<dynamic>)
        .map((dynamic d) => Disease.fromJson(d as Map<String, dynamic>))
        .toList();
  }

  Future<Disease> fetchOne(String key) async {
    final dynamic body = await _api.get('/diseases/$key');
    return Disease.fromJson(body as Map<String, dynamic>);
  }
}
