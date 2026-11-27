import 'dart:convert';
import 'dart:io';
import 'dart:isolate';
import 'dart:math' as math;
import 'dart:typed_data';

import 'package:flutter/foundation.dart' show debugPrint, kReleaseMode;
import 'package:flutter/services.dart' show rootBundle;
import 'package:flutter_onnxruntime/flutter_onnxruntime.dart';
import 'package:image/image.dart' as img;
import 'package:path_provider/path_provider.dart';

import '../models/models.dart';
import 'image_resize.dart';
import 'offline_aggregation.dart';

/// Một ảnh đưa vào chế độ ngoại tuyến: `file` là ảnh gốc dùng để hiển thị,
/// `bytes` là bản đã nén dùng để suy luận (cũng là bản gửi lên máy chủ).
typedef OfflineImageInput = ({File file, List<int> bytes});

/// Suy luận ngay trên máy khi không gọi được backend — dùng mô hình đã xuất
/// sang ONNX (`model/src/export_onnx.py`) kèm CAM tính sẵn cho mọi lớp.
///
/// Vì sao không dùng lại Grad-CAM y hệt server: Grad-CAM cần backprop, ONNX
/// Runtime trên điện thoại chỉ chạy forward. Kiến trúc hiện tại (GAP + một lớp
/// Linear) cho phép dùng CAM cổ điển (Zhou et al., 2016) — về mặt toán học gần
/// tương đương Grad-CAM với đúng kiến trúc này — tính được bằng một lượt
/// forward duy nhất. Xem lời giải thích đầy đủ ở đầu `export_onnx.py`.
///
/// Luồng giống máy chủ: nhận 3–5 ảnh, mỗi ảnh đi qua bộ lọc ảnh đầu vào (#92,
/// `organ_gate_v1.onnx`) trước, ảnh được cho qua mới chạy mô hình bệnh; kết quả
/// chung là trung bình xác suất của các ảnh được cho qua
/// (`offline_aggregation.dart`).
///
/// Các ngưỡng `_heatmapThreshold`/`_minRegionRatio` và câu giải thích bên dưới
/// cố tình chép lại logic của `backend/app/services/xai/explain.py` +
/// `overlay.py` để kết quả offline giống hệt online về mặt nội dung hiển thị.
/// Đây là bản sao thủ công, không dùng chung code với backend (khác ngôn ngữ)
/// — sửa một bên phải nhớ soát lại bên kia.
class OfflineInferenceService {
  OfflineInferenceService._();

  static final OfflineInferenceService instance = OfflineInferenceService._();

  static const int minImages = 3;
  static const int maxImages = 5;

  /// Câu trả lời khi bộ lọc từ chối ảnh. PHẢI khớp nguyên văn
  /// `NOT_TOMATO_LEAF_MESSAGE` trong `backend/app/services/catalog.py`.
  static const String notLeafMessage = 'Ảnh chưa rõ lá cây, bạn chụp lại giúp mình nhé';

  /// Khoá lớp "bị từ chối" lưu trong checkpoint bộ lọc. Đây là định danh gắn
  /// với checkpoint đã huấn luyện, không phải chữ hiển thị.
  static const String _rejectedClass = 'not_tomato_leaf';

  static const double _heatmapThreshold = 0.5;
  // Ngưỡng RIÊNG cho việc vẽ vùng khoanh — khớp `OVERLAY_DRAW_THRESHOLD` trong
  // `backend/app/core/config.py`. `_heatmapThreshold` ở trên vẫn dùng cho tỉ lệ
  // diện tích/mức độ nặng (khớp `max_area_ratio` trong tomato_diseases.json),
  // đổi nó sẽ đổi luôn phân loại Nhẹ/Trung bình/Nặng. Ngưỡng vẽ cao hơn để elip
  // bám sát đỉnh nóng nhất của CAM thay vì cả vùng >=0.5 rộng hơn.
  static const double _overlayDrawThreshold = 0.62;
  static const double _minRegionRatio = 0.005;
  static const int _regionGrid = 56;
  static const List<int> _outlineColor = <int>[255, 64, 32];

  OrtSession? _session;
  OrtSession? _gateSession;
  Map<String, dynamic>? _meta;
  Map<String, dynamic>? _gateMeta;
  Map<String, dynamic>? _catalog;
  Future<void>? _loading;

  Future<void> _ensureLoaded() => _loading ??= _loadOrReset();

  Future<void> _loadOrReset() async {
    try {
      await _load();
    } catch (_) {
      _loading = null; // cho phép thử nạp lại ở lần chẩn đoán sau
      rethrow;
    }
  }

  Future<void> _load() async {
    final OnnxRuntime ort = OnnxRuntime();
    _meta = await _loadJson('assets/model/tomato_leaf_v1_meta.json');
    _gateMeta = await _loadJson('assets/model/organ_gate_v1_meta.json');
    _catalog = await _loadJson('assets/model/tomato_diseases.json');
    _session ??= await ort.createSessionFromAsset('assets/model/tomato_leaf_v1.onnx');
    _gateSession ??= await ort.createSessionFromAsset('assets/model/organ_gate_v1.onnx');
  }

  Future<Map<String, dynamic>> _loadJson(String asset) async =>
      jsonDecode(await rootBundle.loadString(asset)) as Map<String, dynamic>;

  Map<String, dynamic> _diseaseJson(String key) {
    final List<Map<String, dynamic>> diseases =
        (_catalog!['diseases'] as List<dynamic>).cast<Map<String, dynamic>>();
    return diseases.firstWhere((Map<String, dynamic> d) => d['key'] == key);
  }

  List<Map<String, dynamic>> get _severityLevels =>
      (_catalog!['severity_levels'] as List<dynamic>).cast<Map<String, dynamic>>();

  /// Chẩn đoán 3–5 ảnh hoàn toàn trên máy, không cần mạng.
  ///
  /// `bytes` của mỗi ảnh là bản đã nén (`AnalyzingScreen._compress`). `file` là
  /// ảnh gốc, chỉ dùng để hiện ở nút gạt "Ảnh gốc" — `Image.file` giải mã bằng
  /// codec native nên không tốn thêm chi phí đáng kể.
  ///
  /// Giải mã, thu phóng và vẽ vùng khoanh dùng Dart thuần nên được đẩy sang
  /// isolate nền để màn hình không đứng khi xử lý tới 5 ảnh.
  ///
  /// Ném [OfflineDiagnosisException] kèm [notLeafMessage] khi bộ lọc từ chối
  /// toàn bộ ảnh.
  Future<DiagnosisCase> diagnose({
    required List<OfflineImageInput> images,
    String plotLabel = 'Chưa gán lô đất',
  }) async {
    if (images.length < minImages || images.length > maxImages) {
      throw const OfflineDiagnosisException(
        'Cần từ $minImages đến $maxImages ảnh để chẩn đoán.',
      );
    }
    await _ensureLoaded();
    final Stopwatch total = Stopwatch()..start();
    final List<String> classKeys = _strings(_meta!['class_keys']);

    // Chạy tuần tự để không giữ cùng lúc nhiều ảnh đã giải mã trong bộ nhớ.
    final List<_ImageOutcome> outcomes = <_ImageOutcome>[];
    for (int i = 0; i < images.length; i++) {
      outcomes.add(await _runSingleImage(images[i], i));
    }

    // Ảnh bị bộ lọc từ chối không được tính vào kết quả chung.
    final List<_LeafOutcome> leaves = outcomes.whereType<_LeafOutcome>().toList();
    if (leaves.isEmpty) {
      throw const OfflineDiagnosisException(notLeafMessage);
    }

    final List<List<double>> leafProbs = <List<double>>[
      for (final _LeafOutcome leaf in leaves) leaf.probs,
    ];
    final List<double> probs = averageProbabilities(leafProbs);
    final int idx = argmax(probs);
    final double confidence = probs[idx];
    final String diseaseKey = classKeys[idx];

    // Mức độ, vị trí và câu giải thích lấy từ CAM của ĐÚNG bệnh thắng cuộc trên
    // ảnh đại diện (mô hình ONNX trả sẵn CAM cho mọi lớp).
    final _LeafOutcome representative = leaves[representativeIndex(leafProbs, idx)];
    final List<List<double>> camGrid = _camGrid(representative.cams[idx]);
    final List<List<bool>> mask = _threshold(camGrid, _heatmapThreshold);
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

    final List<DiagnosisImageResult> imageResults = <DiagnosisImageResult>[
      for (final _ImageOutcome outcome in outcomes) _imageResult(outcome, classKeys),
    ];

    final List<(String, String)> top3 = _top3(probs, classKeys);
    final bool severe = severityKey == 'severe';
    final List<dynamic> treatments = disease['treatments'] as List<dynamic>? ?? const <dynamic>[];
    final String? urgent = severe && treatments.isNotEmpty ? treatments.first as String : null;

    final Severity severityEnum = Severity.values.firstWhere(
      (Severity s) => s.name == severityKey,
      orElse: () => Severity.mild,
    );
    final int latencyMs = total.elapsedMilliseconds;
    _log('tổng ${images.length} ảnh (${leaves.length} ảnh được cho qua): $latencyMs ms');

    return DiagnosisCase(
      diseaseKey: diseaseKey,
      disease: Disease.fromJson(disease),
      confidence: _percent(confidence),
      affected: _percent(ratio),
      severity: severityEnum,
      plot: plotLabel,
      time: 'Hôm nay ${_hhmm(DateTime.now())}',
      explanation: explanation,
      top3: top3,
      imageFile: representative.file,
      overlayFile: representative.topIndex == idx ? representative.overlayFile : null,
      images: imageResults,
      urgent: urgent,
      modelBadge: '${_meta!['model_version']} · $latencyMs ms · ngoại tuyến',
      disclaimer: (_catalog!['disclaimer'] as String?) ?? '',
    );
  }

  /// Một ảnh: tiền xử lý → bộ lọc → (nếu được cho qua) mô hình bệnh + vùng khoanh.
  Future<_ImageOutcome> _runSingleImage(OfflineImageInput input, int position) async {
    final Stopwatch watch = Stopwatch()..start();
    final _InputSpec gateSpec = _InputSpec.fromMeta(_gateMeta!);
    final _InputSpec modelSpec = _InputSpec.fromMeta(_meta!);

    final _PreparedImage? prepared = await _prepareInBackground(
      Uint8List.fromList(input.bytes),
      gateSpec,
      modelSpec,
    );
    if (prepared == null) {
      throw const OfflineDiagnosisException('Không đọc được ảnh này để chẩn đoán ngoại tuyến.');
    }
    final int prepareMs = watch.elapsedMilliseconds;

    // Bộ lọc xem TOÀN ảnh, giống máy chủ (`DiseasePredictor.predict`).
    final Map<String, List<dynamic>> gateOutput =
        await _runSession(_gateSession!, prepared.gateInput, gateSpec.size);
    final List<double> gateProbs = _doubles(gateOutput['probs']![0]);
    final int gateIdx = argmax(gateProbs);
    final int gateMs = watch.elapsedMilliseconds - prepareMs;

    if (_strings(_gateMeta!['class_keys'])[gateIdx] == _rejectedClass) {
      _log('ảnh ${position + 1}: tiền xử lý $prepareMs ms, bộ lọc $gateMs ms → bị từ chối');
      return _RejectedOutcome(input.file, gateProbs[gateIdx]);
    }

    final Map<String, List<dynamic>> output =
        await _runSession(_session!, prepared.modelInput, modelSpec.size);
    final List<double> probs = _doubles(output['probs']![0]);
    final List<List<List<double>>> cams = <List<List<double>>>[
      for (final dynamic cam in output['cams']![0] as List<dynamic>)
        <List<double>>[for (final dynamic row in cam as List<dynamic>) _doubles(row)],
    ];
    final int modelMs = watch.elapsedMilliseconds - prepareMs - gateMs;

    // Vùng khoanh của từng ảnh ứng với bệnh mà chính ảnh đó chọn, giống máy chủ.
    final int topIndex = argmax(probs);
    final File? overlayFile = await _maybeOverlay(prepared.image, _camGrid(cams[topIndex]), position);
    final int overlayMs = watch.elapsedMilliseconds - prepareMs - gateMs - modelMs;
    _log('ảnh ${position + 1}: tiền xử lý $prepareMs ms, bộ lọc $gateMs ms, '
        'mô hình $modelMs ms, vẽ vùng khoanh $overlayMs ms');

    return _LeafOutcome(input.file, probs, cams, topIndex, overlayFile);
  }

  DiagnosisImageResult _imageResult(_ImageOutcome outcome, List<String> classKeys) {
    return switch (outcome) {
      _RejectedOutcome() => DiagnosisImageResult(
          diseaseName: notLeafMessage,
          confidence: _percent(outcome.confidence),
          imageFile: outcome.file,
          rejected: true,
        ),
      _LeafOutcome() => DiagnosisImageResult(
          diseaseName: _diseaseJson(classKeys[outcome.topIndex])['name_vi'] as String? ??
              classKeys[outcome.topIndex],
          confidence: _percent(outcome.probs[outcome.topIndex]),
          imageFile: outcome.file,
          overlayFile: outcome.overlayFile,
        ),
    };
  }

  /// Chạy một phiên ONNX và giải phóng mọi tensor native sau khi đọc xong.
  Future<Map<String, List<dynamic>>> _runSession(
    OrtSession session,
    Float32List input,
    int size,
  ) async {
    final OrtValue tensor = await OrtValue.fromList(input, <int>[1, 3, size, size]);
    try {
      final Map<String, OrtValue> outputs =
          await session.run(<String, OrtValue>{'image': tensor});
      try {
        return <String, List<dynamic>>{
          for (final MapEntry<String, OrtValue> entry in outputs.entries)
            entry.key: await entry.value.asList(),
        };
      } finally {
        for (final OrtValue value in outputs.values) {
          await value.dispose();
        }
      }
    } finally {
      await tensor.dispose();
    }
  }

  Future<File?> _maybeOverlay(img.Image image, List<List<double>> camGrid, int position) async {
    if (_maskRatio(_threshold(camGrid, _heatmapThreshold)) < _minRegionRatio) return null;
    final _GridBox? box = _largestComponentBox(_threshold(camGrid, _overlayDrawThreshold));
    if (box == null) return null;

    final Uint8List jpeg = await _renderOverlayInBackground(image, box, _regionGrid);
    final Directory dir = await getTemporaryDirectory();
    final File file = File(
      '${dir.path}${Platform.pathSeparator}'
      'agrixai_offline_${DateTime.now().microsecondsSinceEpoch}_$position.jpg',
    );
    await file.writeAsBytes(jpeg);
    return file;
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

  /// CAM thô 7×7 của một lớp → lưới 56×56 đã ReLU, chuẩn hoá 0..1.
  List<List<double>> _camGrid(List<List<double>> raw) =>
      _bilinearResize(_reluNormalize(raw), _regionGrid, _regionGrid);

  List<List<bool>> _threshold(List<List<double>> grid, double threshold) => <List<bool>>[
        for (final List<double> row in grid) <bool>[for (final double v in row) v >= threshold],
      ];

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

  // ── Tìm vùng lớn nhất trên mặt nạ (BFS 4 hướng) để vẽ elip lên ảnh gốc ──

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

  String _hhmm(DateTime t) =>
      '${t.hour.toString().padLeft(2, '0')}:${t.minute.toString().padLeft(2, '0')}';

  String _percent(double fraction) => '${(fraction * 100).round()}%';

  List<String> _strings(dynamic list) => (list as List<dynamic>).cast<String>();

  List<double> _doubles(dynamic list) =>
      <double>[for (final dynamic v in list as List<dynamic>) (v as num).toDouble()];

  /// Thời gian từng bước chỉ in ở bản debug/profile, phục vụ đo hiệu năng.
  void _log(String message) {
    if (!kReleaseMode) debugPrint('[ngoại tuyến] $message');
  }
}

// ── Phần chạy trong isolate nền: phải là hàm cấp cao nhất để không kéo theo
// đối tượng dịch vụ (giữ phiên ONNX native, không gửi qua isolate được). ──

Future<_PreparedImage?> _prepareInBackground(
  Uint8List bytes,
  _InputSpec gate,
  _InputSpec model,
) =>
    Isolate.run(() => _prepare(bytes, gate, model));

/// Giải mã ảnh và dựng tensor đầu vào cho bộ lọc lẫn mô hình bệnh. Trả `null`
/// khi không giải mã được.
_PreparedImage? _prepare(Uint8List bytes, _InputSpec gate, _InputSpec model) {
  final img.Image? decoded = img.decodeImage(bytes);
  if (decoded == null) return null;
  img.Image image = img.bakeOrientation(decoded);
  if (image.numChannels != 3 || image.format != img.Format.uint8 || image.hasPalette) {
    image = image.convert(format: img.Format.uint8, numChannels: 3);
  }
  final Uint8List rgb = image.getBytes(order: img.ChannelOrder.rgb);

  final Float32List gateInput = _toTensor(rgb, image.width, image.height, gate);
  final Float32List modelInput = gate.sameAs(model)
      ? gateInput
      : _toTensor(rgb, image.width, image.height, model);
  return _PreparedImage(image, gateInput, modelInput);
}

/// Khớp `build_infer_transform` (model/src/data/dataset.py): resize thẳng về
/// vuông bằng bilinear của Pillow, chia 255, chuẩn hoá ImageNet, thứ tự NCHW.
Float32List _toTensor(Uint8List rgb, int width, int height, _InputSpec spec) {
  final int size = spec.size;
  final Uint8List resized = resizeRgbBilinear(rgb, width, height, size, size);
  final int plane = size * size;
  final Float32List out = Float32List(3 * plane);
  for (int i = 0; i < plane; i++) {
    for (int c = 0; c < 3; c++) {
      out[c * plane + i] = (resized[i * 3 + c] / 255.0 - spec.mean[c]) / spec.std[c];
    }
  }
  return out;
}

Future<Uint8List> _renderOverlayInBackground(img.Image image, _GridBox box, int gridSize) =>
    Isolate.run(() => _renderOverlay(image, box, gridSize));

/// Vẽ elip theo khung bao vùng nghi ngờ. `image` là bản sao đã được chép sang
/// isolate nên vẽ trực tiếp lên đó không ảnh hưởng ảnh bên ngoài.
Uint8List _renderOverlay(img.Image image, _GridBox box, int gridSize) {
  final double sx = image.width / gridSize;
  final double sy = image.height / gridSize;
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
  final num thickness = math.max(2, (math.min(image.width, image.height) / 220).round());
  img.drawPolygon(
    image,
    vertices: vertices,
    color: img.ColorRgb8(
      OfflineInferenceService._outlineColor[0],
      OfflineInferenceService._outlineColor[1],
      OfflineInferenceService._outlineColor[2],
    ),
    antialias: true,
    thickness: thickness,
  );
  return img.encodeJpg(image, quality: 88);
}

/// Kích thước và hệ số chuẩn hoá đầu vào, đọc từ file meta của mỗi mô hình.
class _InputSpec {
  const _InputSpec(this.size, this.mean, this.std);

  factory _InputSpec.fromMeta(Map<String, dynamic> meta) => _InputSpec(
        meta['image_size'] as int,
        <double>[for (final dynamic v in meta['mean'] as List<dynamic>) (v as num).toDouble()],
        <double>[for (final dynamic v in meta['std'] as List<dynamic>) (v as num).toDouble()],
      );

  final int size;
  final List<double> mean;
  final List<double> std;

  bool sameAs(_InputSpec other) =>
      size == other.size &&
      List<bool>.generate(3, (int c) => mean[c] == other.mean[c] && std[c] == other.std[c])
          .every((bool ok) => ok);
}

class _PreparedImage {
  const _PreparedImage(this.image, this.gateInput, this.modelInput);
  final img.Image image;
  final Float32List gateInput;
  final Float32List modelInput;
}

sealed class _ImageOutcome {
  const _ImageOutcome(this.file);
  final File file;
}

/// Ảnh bị bộ lọc đầu vào từ chối; mô hình bệnh không chạy trên ảnh này.
class _RejectedOutcome extends _ImageOutcome {
  const _RejectedOutcome(super.file, this.confidence);
  final double confidence;
}

class _LeafOutcome extends _ImageOutcome {
  const _LeafOutcome(super.file, this.probs, this.cams, this.topIndex, this.overlayFile);
  final List<double> probs;

  /// CAM thô của mọi lớp: `cams[lớp][hàng][cột]`.
  final List<List<List<double>>> cams;
  final int topIndex;
  final File? overlayFile;
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
