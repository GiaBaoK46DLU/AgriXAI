import '../models/models.dart';
import 'api_client.dart';

/// Gửi ảnh để chẩn đoán. Cần đã đăng nhập.
///
/// Chưa có hàm đọc lịch sử (`GET /diagnoses`) ở đây: endpoint đó trả về
/// `DiagnosisOut` rút gọn, không kèm `disease`/`top_predictions` như
/// `DiagnosisCase.fromApi` cần — màn Lịch sử để làm sau (theo đúng phạm vi đã
/// thống nhất) nên chưa xây dở dang phần đọc chi tiết từng bản ghi ở đây.
class DiagnosisService {
  DiagnosisService({ApiClient? apiClient}) : _api = apiClient ?? ApiClient();

  final ApiClient _api;

  Future<DiagnosisCase> diagnose({
    required List<int> imageBytes,
    required String filename,
    int? plotId,
    String? note,
  }) async {
    final dynamic body = await _api.postMultipart(
      '/diagnoses',
      fileField: 'file',
      fileBytes: imageBytes,
      filename: filename,
      fields: <String, String>{
        if (plotId != null) 'plot_id': plotId.toString(),
        if (note != null && note.isNotEmpty) 'note': note,
      },
    );
    return DiagnosisCase.fromApi(body as Map<String, dynamic>);
  }
}
