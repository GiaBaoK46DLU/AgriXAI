import '../models/models.dart';
import 'api_client.dart';

/// Gửi 3–5 ảnh để chẩn đoán. Cần đã đăng nhập.
class DiagnosisService {
  DiagnosisService({ApiClient? apiClient}) : _api = apiClient ?? ApiClient();

  final ApiClient _api;

  /// `save = false` khi chẩn đoán nhanh từ nút chụp ảnh chung, không qua một
  /// lô đất cụ thể — backend không lưu vào CSDL nên không xuất hiện ở Lịch sử
  /// (xem CLAUDE.md mục quản lý lô đất).
  Future<DiagnosisCase> diagnose({
    required List<({List<int> bytes, String filename})> images,
    int? plotId,
    String? note,
    bool save = true,
  }) async {
    final dynamic body = await _api.postMultipartFiles(
      '/diagnoses',
      fileField: 'files',
      files: images,
      fields: <String, String>{
        if (plotId != null) 'plot_id': plotId.toString(),
        if (note != null && note.isNotEmpty) 'note': note,
        'save': save.toString(),
      },
    );
    return DiagnosisCase.fromApi(body as Map<String, dynamic>);
  }

  /// Danh sách lịch sử — `GET /diagnoses`. Trả về `items` rút gọn
  /// (`DiagnosisOut`, không kèm `disease`/`top_predictions`); xem chi tiết
  /// từng bản ghi thì gọi [get].
  Future<({List<DiagnosisEntry> items, int total})> list({
    int page = 1,
    int pageSize = 20,
    Severity? severity,
    int? plotId,
  }) async {
    final Map<String, String> query = <String, String>{
      'page': page.toString(),
      'page_size': pageSize.toString(),
      if (severity != null) 'severity': severity.name,
      if (plotId != null) 'plot_id': plotId.toString(),
    };
    final String qs = query.entries.map((e) => '${e.key}=${e.value}').join('&');
    final dynamic body = await _api.get('/diagnoses?$qs');
    final Map<String, dynamic> map = body as Map<String, dynamic>;
    final List<DiagnosisEntry> items = (map['items'] as List<dynamic>)
        .map((dynamic j) => DiagnosisEntry.fromJson(j as Map<String, dynamic>))
        .toList();
    return (items: items, total: map['total'] as int);
  }

  /// Chi tiết đầy đủ một bản ghi — dùng khi nhấn vào một dòng ở màn Lịch sử.
  Future<DiagnosisCase> get(int id) async {
    final dynamic body = await _api.get('/diagnoses/$id');
    return DiagnosisCase.fromApi(body as Map<String, dynamic>);
  }
}
