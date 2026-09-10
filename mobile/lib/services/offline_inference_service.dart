import 'dart:convert';
import 'dart:io';
import 'dart:math' as math;
import 'dart:typed_data';

import 'package:flutter/services.dart' show rootBundle;
import 'package:flutter_onnxruntime/flutter_onnxruntime.dart';
import 'package:image/image.dart' as img;
import 'package:path_provider/path_provider.dart';

import '../models/models.dart';

/// Suy luận ngay trên máy khi không gọi được backend — dùng mô hình đã xuất
/// sang ONNX (`model/src/export_onnx.py`) kèm CAM tính sẵn cho mọi lớp.
///
/// Vì sao không dùng lại Grad-CAM y hệt server: Grad-CAM cần backprop, ONNX
/// Runtime trên điện thoại chỉ chạy forward. Kiến trúc hiện tại (GAP + một lớp
/// Linear) cho phép dùng CAM cổ điển (Zhou et al., 2016) — về mặt toán học gần
/// tương đương Grad-CAM với đúng kiến trúc này — tính được bằng một lượt
/// forward duy nhất. Xem lời giải thích đầy đủ ở đầu `export_onnx.py`.
///
/// Các ngưỡng `_heatmapThreshold`/`_minRegionRatio` và câu giải thích bên dưới
/// cố tình chép lại logic của `backend/app/services/xai/explain.py` +
/// `overlay.py` để kết quả offline giống hệt online về mặt nội dung hiển thị.
/// Đây là bản sao thủ công, không dùng chung code với backend (khác ngôn ngữ)
/// — sửa một bên phải nhớ soát lại bên kia.
class OfflineInferenceService {
  OfflineInferenceService._();

  static final OfflineInferenceService instance = OfflineInferenceService._();

  static const double _heatmapThreshold = 0.5;
  static const double _minRegionRatio = 0.005;
  static const int _regionGrid = 56;
  static const List<int> _outlineColor = <int>[255, 64, 32];

  OrtSession? _session;
  Map<String, dynamic>? _meta;
  Map<String, dynamic>? _catalog;

  Future<void> _ensureLoaded() async {
    if (_session != null) return;
    final OnnxRuntime ort = OnnxRuntime();
    _session = await ort.createSessionFromAsset('assets/model/tomato_leaf_v1.onnx');
    _meta = jsonDecode(await rootBundle.loadString('assets/model/tomato_leaf_v1_meta.json'))
        as Map<String, dynamic>;
    _catalog = jsonDecode(await rootBundle.loadString('assets/model/tomato_diseases.json'))
        as Map<String, dynamic>;
  }

  Map<String, dynamic> _diseaseJson(String key) {
    final List<Map<String, dynamic>> diseases =
        (_catalog!['diseases'] as List<dynamic>).cast<Map<String, dynamic>>();
    return diseases.firstWhere((Map<String, dynamic> d) => d['key'] == key);
  }

  List<Map<String, dynamic>> get _severityLevels =>
      (_catalog!['severity_levels'] as List<dynamic>).cast<Map<String, dynamic>>();

  /// Chẩn đoán một ảnh hoàn toàn trên máy, không cần mạng.
  ///
  /// `imageBytes` là ảnh đã nén (`AnalyzingScreen._compress`, tối đa
  /// 1280×1280) — decode/vẽ overlay/encode PNG đều chạy đồng bộ trên UI
  /// isolate (gói `image` không có bản native), nên nếu decode thẳng ảnh gốc
  /// từ camera (có thể hơn chục megapixel) sẽ đứng hình màn hình vài giây.
  /// `imageFile` (ảnh gốc, không nén) chỉ dùng để hiện ở nút gạt "Ảnh gốc" —
  /// `Image.file` decode bằng codec native nên không tốn chi phí này.
  Future<DiagnosisCase> diagnose({
    required File imageFile,
    required List<int> imageBytes,
    String plotLabel = 'Chưa gán lô đất',
  }) async {
    await _ensureLoaded();
    final DateTime started = DateTime.now();

    img.Image? decoded = img.decodeImage(Uint8List.fromList(imageBytes));
    if (decoded == null) {
      throw const OfflineDiagnosisException('Không đọc được ảnh này để chẩn đoán ngoại tuyến.');
    }
    decoded = img.bakeOrientation(decoded);

    final int imageSize = _meta!['image_size'] as int;
    final List<double> mean =
        (_meta!['mean'] as List<dynamic>).map((dynamic n) => (n as num).toDouble()).toList();
    final List<double> std =
        (_meta!['std'] as List<dynamic>).map((dynamic n) => (n as num).toDouble()).toList();
    final List<String> classKeys = (_meta!['class_keys'] as List<dynamic>).cast<String>();

    final Float32List input = _preprocess(decoded, imageSize, mean, std);

    final Map<String, OrtValue> outputs = await _session!.run(<String, OrtValue>{
      'image': await OrtValue.fromList(input, <int>[1, 3, imageSize, imageSize]),
    });
    final List<dynamic> probsNested = await outputs['probs']!.asList();
    final List<dynamic> camsNested = await outputs['cams']!.asList();
    for (final OrtValue v in outputs.values) {
      await v.dispose();
    }

    final List<double> probs =
        (probsNested[0] as List<dynamic>).map((dynamic e) => (e as num).toDouble()).toList();
    int idx = 0;
    for (int k = 1; k < probs.length; k++) {
      if (probs[k] > probs[idx]) idx = k;
    }
    final double confidence = probs[idx];
    final String diseaseKey = classKeys[idx];

    final List<List<double>> camNorm = _reluNormalize(
      (camsNested[0][idx] as List<dynamic>)
          .map<List<double>>((dynamic row) =>
              (row as List<dynamic>).map((dynamic e) => (e as num).toDouble()).toList())
          .toList(),
    );
    final List<List<double>> camGrid = _bilinearResize(camNorm, _regionGrid, _regionGrid);
    final List<List<bool>> mask = List<List<bool>>.generate(
      _regionGrid,
      (int y) => List<bool>.generate(_regionGrid, (int x) => camGrid[y][x] >= _heatmapThreshold),
    );
    final double ratio = _maskRatio(mask);

    final Map<String, dynamic> disease = _diseaseJson(diseaseKey);
    final bool isHealthy = disease['is_healthy'] as bool? ?? false;
    final String region = _describeRegion(mask, ratio);
    final (String severityKey, String severityName) = _severityFor(ratio, isHealthy);
    final String explanation = _buildExplanation(
      disease: disease,
      confidence: confidence,
      ratio: ratio,
      region: region,
      isHealthy: isHealthy,
    );

    File? overlayFile;
    if (ratio >= _minRegionRatio) {
      final _GridBox? box = _largestComponentBox(mask);
      if (box != null) {
        overlayFile = await _drawOverlay(decoded, box, _regionGrid);
      }
    }

    final List<(String, String)> top3 = _top3(probs, classKeys);
    final bool severe = severityKey == 'severe';
    final List<dynamic> treatments = disease['treatments'] as List<dynamic>? ?? const <dynamic>[];
    final String? urgent = severe && treatments.isNotEmpty ? treatments.first as String : null;

    final Severity severityEnum = Severity.values.firstWhere(
      (Severity s) => s.name == severityKey,
      orElse: () => Severity.mild,
    );
    final int latencyMs = DateTime.now().difference(started).inMilliseconds;

    return DiagnosisCase(
      diseaseKey: diseaseKey,
      disease: Disease.fromJson(disease),
      confidence: '${(confidence * 100).round()}%',
      affected: '${(ratio * 100).round()}%',
      severity: severityEnum,
      plot: plotLabel,
      time: 'Hôm nay ${_hhmm(DateTime.now())}',
      explanation: explanation,
      top3: top3,
      imageFile: imageFile,
      overlayFile: overlayFile,
      urgent: urgent,
      modelBadge: '${_meta!['model_version']} · $latencyMs ms · ngoại tuyến',
      disclaimer: (_catalog!['disclaimer'] as String?) ?? '',
    );
  }

  // ── Tiền xử lý ảnh — khớp build_infer_transform (model/src/data/dataset.py) ──

  Float32List _preprocess(img.Image image, int size, List<double> mean, List<double> std) {
    final img.Image resized = img.copyResize(
      image,
      width: size,
      height: size,
      interpolation: img.Interpolation.linear,
    );
    final Float32List out = Float32List(3 * size * size);
    final int plane = size * size;
    for (int y = 0; y < size; y++) {
      for (int x = 0; x < size; x++) {
        final img.Pixel p = resized.getPixel(x, y);
        final int base = y * size + x;
        out[base] = (p.r / 255.0 - mean[0]) / std[0];
        out[plane + base] = (p.g / 255.0 - mean[1]) / std[1];
        out[2 * plane + base] = (p.b / 255.0 - mean[2]) / std[2];
      }
    }
    return out;
  }

  // ── CAM: ReLU + chuẩn hoá min-max, giống hệt công thức trong gradcam.py ──

  List<List<double>> _reluNormalize(List<List<double>> raw) {
    double lo = double.infinity, hi = -double.infinity;
    for (final List<double> row in raw) {
      for (final double v in row) {
        final double r = math.max(0.0, v);
        if (r < lo) lo = r;
        if (r > hi) hi = r;
      }
    }
    final double range = hi - lo;
    return raw
        .map((List<double> row) => row
            .map((double v) => range > 0 ? (math.max(0.0, v) - lo) / range : 0.0)
            .toList())
        .toList();
  }

  List<List<double>> _bilinearResize(List<List<double>> src, int outH, int outW) {
    final int inH = src.length;
    final int inW = src[0].length;
    final double sy = inH / outH;
    final double sx = inW / outW;
    return List<List<double>>.generate(outH, (int oy) {
      final double fy = ((oy + 0.5) * sy - 0.5).clamp(0.0, inH - 1.0);
      final int y0 = fy.floor();
      final int y1 = math.min(y0 + 1, inH - 1);
      final double wy = fy - y0;
      return List<double>.generate(outW, (int ox) {
        final double fx = ((ox + 0.5) * sx - 0.5).clamp(0.0, inW - 1.0);
        final int x0 = fx.floor();
        final int x1 = math.min(x0 + 1, inW - 1);
        final double wx = fx - x0;
        final double top = src[y0][x0] * (1 - wx) + src[y0][x1] * wx;
        final double bottom = src[y1][x0] * (1 - wx) + src[y1][x1] * wx;
        return top * (1 - wy) + bottom * wy;
      });
    });
  }

  double _maskRatio(List<List<bool>> mask) {
    int count = 0;
    for (final List<bool> row in mask) {
      for (final bool v in row) {
        if (v) count++;
      }
    }
    return count / (mask.length * mask[0].length);
  }

  // ── Mô tả vị trí / mức độ / câu giải thích — chép từ xai/explain.py ──

  String _describeRegion(List<List<bool>> mask, double ratio) {
    final int h = mask.length;
    final int w = mask[0].length;
    int sumY = 0, sumX = 0, count = 0;
    for (int y = 0; y < h; y++) {
      for (int x = 0; x < w; x++) {
        if (mask[y][x]) {
          sumY += y;
          sumX += x;
          count++;
        }
      }
    }
    if (count == 0) return 'toàn bộ phiến lá';
    if (ratio > 0.45) return 'phần lớn diện tích lá';

    final double cy = sumY / count / h;
    final double cx = sumX / count / w;
    final String vertical = cy < 0.34 ? 'phía trên' : (cy > 0.66 ? 'phía dưới' : 'phần giữa');
    final String horizontal = cx < 0.34 ? 'bên trái' : (cx > 0.66 ? 'bên phải' : '');
    return '${'$vertical $horizontal'.trim()} của lá';
  }

  (String, String) _severityFor(double ratio, bool isHealthy) {
    final List<Map<String, dynamic>> levels = List<Map<String, dynamic>>.of(_severityLevels)
      ..sort((a, b) =>
          (a['max_area_ratio'] as num).compareTo(b['max_area_ratio'] as num));

    if (isHealthy) {
      final Map<String, dynamic> none = levels.firstWhere(
        (Map<String, dynamic> l) => l['key'] == 'none',
        orElse: () => levels.first,
      );
      return (none['key'] as String, none['name_vi'] as String);
    }
    for (final Map<String, dynamic> level in levels) {
      if (level['key'] == 'none') continue;
      if (ratio <= (level['max_area_ratio'] as num).toDouble()) {
        return (level['key'] as String, level['name_vi'] as String);
      }
    }
    final Map<String, dynamic> last = levels.last;
    return (last['key'] as String, last['name_vi'] as String);
  }

  String _buildExplanation({
    required Map<String, dynamic> disease,
    required double confidence,
    required double ratio,
    required String region,
    required bool isHealthy,
  }) {
    final String nameVi = disease['name_vi'] as String? ?? disease['key'] as String;
    final String pct = '${(confidence * 100).round()}%';

    if (isHealthy) {
      return 'Hệ thống không tìm thấy dấu hiệu bệnh nào rõ rệt trên lá '
          '(độ tin cậy $pct). Lá có màu đều, không có đốm hay biến dạng.';
    }
    if (ratio < _minRegionRatio) {
      return 'Hệ thống nghiêng về $nameVi với độ tin cậy $pct, '
          'nhưng không khoanh được vùng nào đủ rõ trên ảnh. '
          'Nên chụp lại gần hơn, đủ sáng và lấy nét vào phần lá nghi ngờ.';
    }
    final String cue = (disease['visual_cue'] as String?) ?? 'dấu hiệu bất thường';
    final String ratioPct = '${(ratio * 100).round()}%';
    return 'Hệ thống tập trung vào $region — nơi xuất hiện $cue. '
        'Đây là dấu hiệu đặc trưng của $nameVi '
        '(độ tin cậy $pct, vùng nghi ngờ chiếm khoảng $ratioPct diện tích ảnh).';
  }

  List<(String, String)> _top3(List<double> probs, List<String> classKeys) {
    final List<int> order = List<int>.generate(probs.length, (int i) => i)
      ..sort((int a, int b) => probs[b].compareTo(probs[a]));
    return order.take(3).map((int i) {
      final String nameVi = _diseaseJson(classKeys[i])['name_vi'] as String? ?? classKeys[i];
      return (nameVi, '${(probs[i] * 100).round()}%');
    }).toList();
  }

  // ── Tìm vùng lớn nhất trên mặt nạ (BFS 4 hướng) rồi vẽ elip lên ảnh gốc ──

  _GridBox? _largestComponentBox(List<List<bool>> mask) {
    final int h = mask.length;
    final int w = mask[0].length;
    final List<List<bool>> visited =
        List<List<bool>>.generate(h, (_) => List<bool>.filled(w, false));
    _GridBox? best;
    int bestSize = 0;

    for (int sy = 0; sy < h; sy++) {
      for (int sx = 0; sx < w; sx++) {
        if (!mask[sy][sx] || visited[sy][sx]) continue;
        int minX = sx, maxX = sx, minY = sy, maxY = sy, size = 0;
        final List<(int, int)> queue = <(int, int)>[(sy, sx)];
        visited[sy][sx] = true;
        int head = 0;
        while (head < queue.length) {
          final (int y, int x) = queue[head++];
          size++;
          if (x < minX) minX = x;
          if (x > maxX) maxX = x;
          if (y < minY) minY = y;
          if (y > maxY) maxY = y;
          for (final (int, int) d in const <(int, int)>[(1, 0), (-1, 0), (0, 1), (0, -1)]) {
            final int ny = y + d.$1, nx = x + d.$2;
            if (ny >= 0 && ny < h && nx >= 0 && nx < w && mask[ny][nx] && !visited[ny][nx]) {
              visited[ny][nx] = true;
              queue.add((ny, nx));
            }
          }
        }
        if (size > bestSize) {
          bestSize = size;
          best = _GridBox(minX, minY, maxX, maxY);
        }
      }
    }
    return best;
  }

  Future<File> _drawOverlay(img.Image original, _GridBox box, int gridSize) async {
    final img.Image canvas = img.Image.from(original);
    final double sx = canvas.width / gridSize;
    final double sy = canvas.height / gridSize;
    final double cx = (box.minX + box.maxX + 1) / 2 * sx;
    final double cy = (box.minY + box.maxY + 1) / 2 * sy;
    final double rx = math.max(6.0, (box.maxX - box.minX + 1) / 2 * sx);
    final double ry = math.max(6.0, (box.maxY - box.minY + 1) / 2 * sy);

    const int points = 48;
    final List<img.Point> vertices = List<img.Point>.generate(points, (int i) {
      final double angle = 2 * math.pi * i / points;
      return img.Point(cx + rx * math.cos(angle), cy + ry * math.sin(angle));
    });

    // Cùng công thức bề dày đường viền với backend/app/services/xai/overlay.py
    final num thickness = math.max(2, (math.min(canvas.width, canvas.height) / 220).round());
    img.drawPolygon(
      canvas,
      vertices: vertices,
      color: img.ColorRgb8(_outlineColor[0], _outlineColor[1], _outlineColor[2]),
      antialias: true,
      thickness: thickness,
    );

    final Directory dir = await getTemporaryDirectory();
    final File file = File(
      '${dir.path}${Platform.pathSeparator}agrixai_offline_${DateTime.now().millisecondsSinceEpoch}.png',
    );
    await file.writeAsBytes(img.encodePng(canvas));
    return file;
  }

  String _hhmm(DateTime t) =>
      '${t.hour.toString().padLeft(2, '0')}:${t.minute.toString().padLeft(2, '0')}';
}

class _GridBox {
  const _GridBox(this.minX, this.minY, this.maxX, this.maxY);
  final int minX, minY, maxX, maxY;
}

class OfflineDiagnosisException implements Exception {
  const OfflineDiagnosisException(this.message);
  final String message;
  @override
  String toString() => message;
}
