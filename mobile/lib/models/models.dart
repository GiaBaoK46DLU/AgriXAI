import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:flutter/painting.dart';

import '../core/app_config.dart';

/// Mức độ nặng của một lần chẩn đoán — bốn bậc, khớp `severity_levels`
/// trong `shared/data/tomato_diseases.json`.
enum Severity { none, mild, moderate, severe }

/// Màu và tên hiển thị của từng bậc, lấy nguyên từ thiết kế v4.
@immutable
class SeverityStyle {
  const SeverityStyle({
    required this.name,
    required this.bg,
    required this.fg,
    required this.dot,
    required this.leafA,
    required this.leafB,
    required this.iconBg,
  });

  final String name;
  final Color bg;
  final Color fg;
  final Color dot;

  /// Hai tông của icon lá trong thẻ lô đất và hàng lịch sử.
  final Color leafA;
  final Color leafB;

  /// Nền ô icon — riêng mức "Nặng" dùng cam nhạt thay vì màu chip.
  final Color iconBg;
}

/// Nhóm tác nhân gây bệnh — quyết định tag màu trong danh mục.
enum PathogenType { fungus, bacteria, virus, pest, healthy }

@immutable
class PathogenTypeStyle {
  const PathogenTypeStyle({
    required this.label,
    required this.bg,
    required this.fg,
    required this.dot,
  });

  final String label;
  final Color bg;
  final Color fg;
  final Color dot;
}

/// Một loại thuốc gợi ý. `productUrl` mở trang sản phẩm/hoạt chất qua
/// `url_launcher`. `note` dùng cho ca như virus xoăn vàng lá — thuốc trị bọ
/// phấn (môi giới truyền bệnh) chứ không trị trực tiếp virus.
@immutable
class ProductLink {
  const ProductLink({
    required this.name,
    required this.group,
    this.productUrl,
    this.note,
  });

  factory ProductLink.fromJson(Map<String, dynamic> json) => ProductLink(
        name: json['name'] as String,
        group: (json['group'] as String?) ?? '',
        productUrl: json['purchase_url'] as String?,
        note: json['note'] as String?,
      );

  final String name;
  final String group;
  final String? productUrl;
  final String? note;
}

@immutable
class Disease {
  const Disease({
    required this.key,
    required this.name,
    required this.en,
    required this.type,
    required this.pathogen,
    required this.cue,
    required this.symptoms,
    required this.conditions,
    required this.treatments,
    required this.prevention,
    this.products = const <ProductLink>[],
    this.noProductText,
    this.videoUrl,
  });

  /// Parse `DiseaseInfo` trả về từ `GET /diseases` hoặc `GET /diseases/{key}`.
  ///
  /// `type` (nhóm tác nhân) không có trong JSON của backend — đây là phân
  /// loại chỉ để tô màu nhãn ở app, suy ra từ khoá bệnh. Danh sách 10 khoá cố
  /// định (gắn với thứ tự output mô hình) nên suy trực tiếp an toàn hơn là
  /// đoán qua chữ trong trường `pathogen`.
  factory Disease.fromJson(Map<String, dynamic> json) {
    final String key = json['key'] as String;
    final bool isHealthy = json['is_healthy'] as bool? ?? false;
    final List<ProductLink> products = (json['products'] as List<dynamic>? ??
            const <dynamic>[])
        .map((dynamic p) => ProductLink.fromJson(p as Map<String, dynamic>))
        .toList();

    return Disease(
      key: key,
      name: json['name_vi'] as String,
      en: json['name_en'] as String,
      type: _pathogenTypeForKey(key, isHealthy),
      pathogen: (json['pathogen'] as String?) ?? 'Không có tác nhân gây bệnh',
      cue: (json['visual_cue'] as String?) ?? '',
      symptoms: (json['symptoms'] as String?) ?? '',
      conditions: (json['favorable_conditions'] as String?) ?? 'Không áp dụng.',
      treatments: (json['treatments'] as List<dynamic>? ?? const <dynamic>[])
          .cast<String>(),
      prevention: (json['prevention'] as List<dynamic>? ?? const <dynamic>[])
          .cast<String>(),
      products: products,
      noProductText: products.isEmpty
          ? (isHealthy
              ? 'Lá đang khoẻ — không cần dùng thuốc. Giữ nguyên chế độ chăm sóc và kiểm tra vườn định kỳ.'
              : 'Chưa có thuốc trị trực tiếp — làm theo các bước "Cần làm ngay" ở trên.')
          : null,
      videoUrl: json['video_url'] as String?,
    );
  }

  static PathogenType _pathogenTypeForKey(String key, bool isHealthy) {
    if (isHealthy) return PathogenType.healthy;
    if (key == 'spider_mites') return PathogenType.pest;
    if (key == 'yellow_leaf_curl_virus' || key == 'mosaic_virus') {
      return PathogenType.virus;
    }
    if (key == 'bacterial_spot') return PathogenType.bacteria;
    return PathogenType.fungus;
  }

  final String key;
  final String name;
  final String en;
  final PathogenType type;
  final String pathogen;

  /// Câu "nhận biết nhanh".
  final String cue;
  final String symptoms;
  final String conditions;
  final List<String> treatments;
  final List<String> prevention;
  final List<ProductLink> products;

  /// Câu giải thích khi cố ý không có thuốc nào.
  final String? noProductText;

  /// Link video YouTube hướng dẫn xử lý, `null` nếu chưa có.
  final String? videoUrl;
}

@immutable
class Plot {
  const Plot({
    required this.id,
    required this.puc,
    required this.name,
    required this.region,
    required this.area,
    required this.status,
    required this.count,
    required this.last,
    required this.lastDisease,
    required this.lastSeverity,
  });

  final int id;
  final String puc;
  final String name;
  final String region;
  final String area;
  final String status;
  final int count;
  final String last;
  final String lastDisease;
  final Severity lastSeverity;
}

@immutable
class DiagnosisEntry {
  const DiagnosisEntry({
    required this.id,
    required this.disease,
    required this.severity,
    required this.confidence,
    required this.plotId,
    required this.plot,
    required this.time,
    this.caseKey,
  });

  /// Dựng từ một phần tử `items` của `GET /diagnoses` (`DiagnosisOut`).
  ///
  /// `plotId` dùng `-1` làm giá trị "không có" khi bản ghi chưa gán lô đất —
  /// cùng quy ước sentinel đã dùng ở `capture_screen.dart` — để không phải
  /// đổi field này sang `int?` và kéo theo sửa mọi nơi đang dùng nó.
  factory DiagnosisEntry.fromJson(Map<String, dynamic> json) {
    final Severity severity = Severity.values.firstWhere(
      (Severity s) => s.name == json['severity'],
      orElse: () => Severity.mild,
    );
    final String? plotName = json['plot_name'] as String?;
    final String? plotPuc = json['plot_puc'] as String?;
    final String plotLabel = plotName == null
        ? 'Chưa gán lô đất'
        : (plotPuc == null ? plotName : '$plotName · $plotPuc');

    return DiagnosisEntry(
      id: json['id'] as int,
      disease: json['disease_name'] as String,
      severity: severity,
      confidence: '${((json['confidence'] as num) * 100).round()}%',
      plotId: (json['plot_id'] as int?) ?? -1,
      plot: plotLabel,
      time: formatIsoTimestamp(json['created_at'] as String),
    );
  }

  final int id;
  final String disease;
  final Severity severity;
  final String confidence;
  final int plotId;
  final String plot;
  final String time;

  /// Trường hợp demo tương ứng ở màn 05, nếu bệnh này có sẵn một bản.
  final String? caseKey;

  String get meta => '$plot · $time';
}

/// Kết quả riêng của MỘT trong 3–5 ảnh đã tải lên — dùng vẽ carousel khoanh
/// vùng ở màn kết quả. Xem `DiagnosisDetail.images` (`DiagnosisImageOut`) ở
/// backend.
@immutable
class DiagnosisImageResult {
  const DiagnosisImageResult({
    required this.diseaseName,
    required this.confidence,
    this.imageUrl,
    this.overlayUrl,
    this.imageFile,
    this.overlayFile,
  });

  factory DiagnosisImageResult.fromApi(Map<String, dynamic> json) {
    return DiagnosisImageResult(
      diseaseName: json['disease_name'] as String,
      confidence: '${((json['confidence'] as num) * 100).round()}%',
      imageUrl: DiagnosisCase._absoluteUrl(json['image_url'] as String?),
      overlayUrl: DiagnosisCase._absoluteUrl(json['overlay_url'] as String?),
    );
  }

  final String diseaseName;
  final String confidence;
  final String? imageUrl;
  final String? overlayUrl;

  /// Ảnh cục bộ khi chẩn đoán ngoại tuyến — ưu tiên hơn `imageUrl`/`overlayUrl`.
  final File? imageFile;
  final File? overlayFile;

  bool get hasOverlay => overlayUrl != null || overlayFile != null;
}

@immutable
class WeatherDay {
  const WeatherDay({
    required this.day,
    required this.temp,
    required this.isNow,
  });

  final String day;
  final String temp;
  final bool isNow;
}

/// Kết quả một lần chẩn đoán — dùng cho cả ba trường hợp demo lẫn kết quả
/// thật trả về từ `POST /diagnoses` (xem [DiagnosisCase.fromApi]).
@immutable
class DiagnosisCase {
  const DiagnosisCase({
    required this.diseaseKey,
    required this.disease,
    required this.confidence,
    required this.affected,
    required this.severity,
    required this.plot,
    required this.time,
    required this.explanation,
    required this.top3,
    this.imageUrl,
    this.overlayUrl,
    this.imageFile,
    this.overlayFile,
    this.images = const <DiagnosisImageResult>[],
    this.urgent,
    this.modelBadge = 'DummyPredictor',
    this.disclaimer = '',
  });

  /// Dựng từ `DiagnosisDetail` JSON mà `POST /diagnoses` trả về.
  ///
  /// Giữ đúng kiểu chuỗi đã định dạng sẵn (`"87%"`, `"Hôm nay 07:12"`) như
  /// các trường hợp demo, để `ResultScreen`/`TreatmentScreen` không phải
  /// phân biệt "dữ liệu thật" với "dữ liệu mẫu".
  factory DiagnosisCase.fromApi(Map<String, dynamic> json) {
    final Disease disease =
        Disease.fromJson(json['disease'] as Map<String, dynamic>);
    final double confidence = (json['confidence'] as num).toDouble();
    final double affected = (json['affected_ratio'] as num).toDouble();
    final List<(String, String)> top3 =
        (json['top_predictions'] as List<dynamic>? ?? const <dynamic>[])
            .map((dynamic p) {
      final Map<String, dynamic> item = p as Map<String, dynamic>;
      final double prob = (item['probability'] as num).toDouble();
      return (item['name_vi'] as String, _percent(prob));
    }).toList();

    final Severity severity = Severity.values.firstWhere(
      (Severity s) => s.name == json['severity'],
      orElse: () => Severity.mild,
    );

    // Chỉ mức "Nặng" mới đáng một banner cảnh báo riêng — bước xử lý đầu
    // tiên trong danh mục thường đã viết đúng giọng khẩn cấp cần thiết
    // (ví dụ mốc sương muộn: "xử lý ngay trong vòng 24 giờ").
    final String? urgent = severity == Severity.severe && disease.treatments.isNotEmpty
        ? disease.treatments.first
        : null;

    final List<DiagnosisImageResult> images =
        (json['images'] as List<dynamic>? ?? const <dynamic>[])
            .map((dynamic i) =>
                DiagnosisImageResult.fromApi(i as Map<String, dynamic>))
            .toList();

    return DiagnosisCase(
      diseaseKey: json['disease_key'] as String,
      disease: disease,
      confidence: _percent(confidence),
      affected: _percent(affected),
      severity: severity,
      plot: _plotLabel(json),
      time: formatIsoTimestamp(json['created_at'] as String),
      explanation: (json['explanation'] as String?) ?? '',
      top3: top3,
      imageUrl: _absoluteUrl(json['image_url'] as String?),
      overlayUrl: _absoluteUrl(json['overlay_url'] as String?),
      images: images,
      urgent: urgent,
      modelBadge: '${json['model_version']} · ${(json['latency_ms'] as num).round()} ms',
      disclaimer: (json['disclaimer'] as String?) ?? '',
    );
  }

  static String _percent(double fraction) =>
      '${(fraction * 100).round()}%';

  static String? _absoluteUrl(String? relative) =>
      relative == null ? null : '${AppConfig.storageBaseUrl}$relative';

  static String _plotLabel(Map<String, dynamic> json) {
    final String? name = json['plot_name'] as String?;
    final String? puc = json['plot_puc'] as String?;
    if (name == null) return 'Chưa gán lô đất';
    return puc == null ? name : '$name · $puc';
  }

  final String diseaseKey;
  final Disease disease;
  final String confidence;
  final String affected;
  final Severity severity;
  final String plot;
  final String time;
  final String explanation;

  /// Ba khả năng cao nhất: (tên bệnh, phần trăm).
  final List<(String, String)> top3;

  /// Đường dẫn ảnh gốc/ảnh đã khoanh vùng, ghép với `AppConfig.storageBaseUrl`
  /// khi hiển thị. `null` ở dữ liệu mẫu (chưa từng có ảnh thật).
  final String? imageUrl;
  final String? overlayUrl;

  /// Ảnh cục bộ khi chẩn đoán ngoại tuyến (`OfflineInferenceService`) — ưu
  /// tiên hơn `imageUrl`/`overlayUrl` nếu có, vì lúc đó chưa từng có URL nào
  /// từ backend. Xem `ResultScreen._imageFrame`.
  final File? imageFile;
  final File? overlayFile;

  /// Kết quả riêng từng ảnh trong 3–5 ảnh đã tải lên — rỗng ở dữ liệu mẫu cũ
  /// (chưa từng có nhiều ảnh), khi đó màn kết quả rơi về hiện một ảnh như cũ.
  final List<DiagnosisImageResult> images;

  /// Dòng cảnh báo đỏ-cam ở màn 06; `null` thì không hiện thẻ nào.
  final String? urgent;

  /// `"efficientnet_b0-... · 91 ms"` — phiên bản mô hình + độ trễ thật.
  final String modelBadge;

  /// Khuyến cáo tham khảo học thuật, lấy từ `DiagnosisDetail.disclaimer`.
  final String disclaimer;
}

/// `"Hôm nay 07:12"` / `"Hôm qua 16:40"` / `"18/08 08:05"` — dùng chung cho
/// `DiagnosisCase.fromApi` và `DiagnosisEntry.fromJson` để hai màn Kết quả và
/// Lịch sử luôn hiện thời gian theo đúng một định dạng.
String formatIsoTimestamp(String isoTimestamp) {
  final DateTime utc = DateTime.parse(isoTimestamp);
  final DateTime local = utc.toLocal();
  final DateTime now = DateTime.now();
  final String hm =
      '${local.hour.toString().padLeft(2, '0')}:${local.minute.toString().padLeft(2, '0')}';
  final bool sameDay = local.year == now.year &&
      local.month == now.month &&
      local.day == now.day;
  if (sameDay) return 'Hôm nay $hm';
  final DateTime yesterday = now.subtract(const Duration(days: 1));
  final bool wasYesterday = local.year == yesterday.year &&
      local.month == yesterday.month &&
      local.day == yesterday.day;
  if (wasYesterday) return 'Hôm qua $hm';
  return '${local.day.toString().padLeft(2, '0')}/${local.month.toString().padLeft(2, '0')} $hm';
}
