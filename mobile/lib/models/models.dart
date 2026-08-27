import 'package:flutter/foundation.dart';
import 'package:flutter/painting.dart';

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

/// Một loại thuốc gợi ý. `productUrl` để sẵn chỗ gắn link nhà phân phối —
/// chưa nối, đúng như ghi chú trong bản thiết kế.
@immutable
class ProductLink {
  const ProductLink({
    required this.name,
    required this.group,
    this.productUrl,
  });

  final String name;
  final String group;
  final String? productUrl;
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
    this.productNote,
    this.noProductText,
    this.videoId,
  });

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

  /// Ghi chú riêng khi thuốc không trị bệnh mà trị môi giới truyền bệnh.
  final String? productNote;

  /// Câu giải thích khi cố ý không có thuốc nào.
  final String? noProductText;

  /// Id video YouTube hướng dẫn xử lý — chưa có video nào.
  final String? videoId;
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

/// Ba trường hợp demo của màn "Kết quả chẩn đoán" trong bản thiết kế.
@immutable
class DiagnosisCase {
  const DiagnosisCase({
    required this.diseaseKey,
    required this.confidence,
    required this.affected,
    required this.severity,
    required this.plot,
    required this.time,
    required this.explanation,
    required this.top3,
    this.urgent,
  });

  final String diseaseKey;
  final String confidence;
  final String affected;
  final Severity severity;
  final String plot;
  final String time;
  final String explanation;

  /// Ba khả năng cao nhất: (tên bệnh, phần trăm).
  final List<(String, String)> top3;

  /// Dòng cảnh báo đỏ-cam ở màn 06; `null` thì không hiện thẻ nào.
  final String? urgent;
}
