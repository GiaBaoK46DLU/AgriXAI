import 'dart:async';
import 'dart:io';
import 'dart:typed_data';

import 'package:flutter/foundation.dart' show kDebugMode;
import 'package:flutter/material.dart';
import 'package:flutter_image_compress/flutter_image_compress.dart';

import '../../core/app_colors.dart';
import '../../core/app_glass.dart';
import '../../core/app_metrics.dart';
import '../../core/app_scope.dart';
import '../../core/app_transitions.dart';
import '../../core/app_typography.dart';
import '../../models/models.dart';
import '../../services/api_client.dart';
import '../../services/offline_inference_service.dart';
import '../../services/session.dart' as session;
import '../../widgets/agri_icons.dart';
import '../../widgets/agri_screen.dart';
import '../../widgets/buttons.dart';
import '../../widgets/glass_card.dart';
import '../../widgets/misc.dart';
import '../result/result_screen.dart';

/// **04 Đang phân tích** — UC-M7.
///
/// Ba nhãn bước chạy theo mốc thời gian cố định (chỉ để mắt có gì nhìn khi
/// chờ) trong lúc `POST /diagnoses` chạy thật ở nền; màn chỉ chuyển tiếp khi
/// cả hai xong. Backend giới hạn 10 MB/ảnh nên nén trước khi gửi.
///
/// Nhận 3–5 ảnh (`widget.images`) — mỗi ảnh chạy qua mô hình riêng ở backend,
/// kết quả cuối cùng tổng hợp theo đa số phiếu (xem CLAUDE.md). Suy luận
/// ngoại tuyến (khi mất mạng) chỉ hỗ trợ một ảnh nên dùng ảnh đầu tiên.
class AnalyzingScreen extends StatefulWidget {
  const AnalyzingScreen({
    required this.images,
    this.plotId,
    this.plotName,
    this.save = true,
    this.note,
    super.key,
  });

  final List<File> images;
  final int? plotId;

  /// Tên lô đất để hiện trên kết quả nếu phải rơi về suy luận ngoại tuyến —
  /// lúc đó không gọi được `GET /plots` nên phải mang theo từ màn Chụp ảnh.
  final String? plotName;

  /// Ghi chú tự do, tối đa 500 ký tự — chỉ gửi lên backend, suy luận ngoại
  /// tuyến không dùng tới (không có gì lưu để gắn ghi chú vào).
  final String? note;

  /// `false` khi vào từ nút chụp ảnh chung (không qua một lô đất cụ thể) —
  /// backend không lưu kết quả này vào CSDL (xem CLAUDE.md mục quản lý lô
  /// đất). Không ảnh hưởng tới nhánh suy luận ngoại tuyến, vốn đã không đụng
  /// tới backend nên chưa bao giờ được lưu.
  final bool save;

  @override
  State<AnalyzingScreen> createState() => _AnalyzingScreenState();
}

class _AnalyzingScreenState extends State<AnalyzingScreen> {
  /// Câu báo lỗi khi bộ chặn lá/không-phải-lá (#92, nối vào backend ở #47)
  /// từ chối cả lô ảnh. PHẢI khớp nguyên văn với `NOT_TOMATO_LEAF_MESSAGE`
  /// trong `backend/app/services/catalog.py` — hai bên không import chung
  /// được (khác ngôn ngữ) nên chép tay, cùng kiểu với cách
  /// `mobile/assets/model/tomato_diseases.json` chép tay từ `shared/data/`
  /// (xem CLAUDE.md). Dùng để hiện một màn phản hồi nhẹ nhàng hơn (icon máy
  /// ảnh) thay vì màn lỗi chung (icon cảnh báo) — đây không phải một lỗi hệ
  /// thống, mà là hệ thống đang làm đúng việc của nó.
  static const String _notTomatoLeafMessage =
      'Ảnh chưa rõ lá cà chua, bạn chụp lại giúp mình nhé';

  static const List<String> _labels = <String>[
    'Nén và tải ảnh lên máy chủ',
    'Nhận diện bệnh',
    'Khoanh vùng nghi ngờ (Grad-CAM)',
  ];

  final List<Timer> _timers = <Timer>[];
  int _step = 0;
  String? _error;

  @override
  void initState() {
    super.initState();
    _timers.addAll(<Timer>[
      Timer(const Duration(milliseconds: 600), () => _setStep(1)),
      Timer(const Duration(milliseconds: 1400), () => _setStep(2)),
      Timer(const Duration(milliseconds: 2100), () => _setStep(3)),
    ]);
    _run();
  }

  @override
  void dispose() {
    for (final Timer timer in _timers) {
      timer.cancel();
    }
    super.dispose();
  }

  void _setStep(int value) {
    if (!mounted) return;
    setState(() => _step = value);
  }

  static const int _maxCompressedBytes = 2 * 1024 * 1024; // 2 MB

  /// Nén tới khi dưới 2 MB hoặc hết nước — mỗi lượt nén lại từ file GỐC
  /// (không nén chồng lên ảnh đã nén) với quality/kích thước thấp hơn, để
  /// không mất chất lượng oan do nén JPEG nhiều lớp chồng nhau. `quality: 82,
  /// minWidth/minHeight: 1280` một lượt duy nhất (cách cũ) không đủ với ảnh
  /// gốc rất nặng — camera hiện đại dễ ra ảnh 8–12 MB.
  Future<({List<int> bytes, String filename})> _compress(File file) async {
    final int originalSize = await file.length();
    int quality = 82;
    int dimension = 1280;
    List<int> bytes = <int>[];

    for (int attempt = 0; attempt < 5; attempt++) {
      final Uint8List? result = await FlutterImageCompress.compressWithFile(
        file.path,
        quality: quality,
        minWidth: dimension,
        minHeight: dimension,
      );
      bytes = result ?? await file.readAsBytes();
      if (bytes.length <= _maxCompressedBytes || quality <= 35) break;
      quality = (quality - 15).clamp(35, 100);
      dimension = (dimension * 0.85).round();
    }

    if (kDebugMode) {
      debugPrint(
        'Nén ảnh ${file.uri.pathSegments.last}: '
        '${(originalSize / 1024).round()} KB → ${(bytes.length / 1024).round()} KB '
        '(quality=$quality, cạnh tối thiểu=${dimension}px)',
      );
    }

    return (bytes: bytes, filename: file.uri.pathSegments.last);
  }

  Future<void> _run() async {
    try {
      final List<({List<int> bytes, String filename})> images =
          await Future.wait(widget.images.map(_compress));

      DiagnosisCase result;
      try {
        result = await session.diagnosisService.diagnose(
          images: images,
          plotId: widget.plotId,
          note: widget.note,
          save: widget.save,
        );
      } on NetworkException {
        // Không gọi được backend (mất mạng, sập tường lửa, server tắt...) —
        // tự chuyển sang mô hình chạy ngay trên máy (xem CLAUDE.md mục suy
        // luận ngoại tuyến). Chỉ bắt NetworkException, KHÔNG bắt rộng mọi lỗi
        // nữa (xem #47): ApiException nghĩa là backend ĐÃ trả lời — kể cả bị
        // bộ chặn #92 từ chối ("không phải lá cà chua") — nên phải rơi xuống
        // `on ApiException` bên dưới để người dùng thấy đúng thông báo, thay
        // vì âm thầm chạy lại offline (không có bộ chặn) và có thể vẫn ra một
        // tên bệnh cho một tấm ảnh rõ ràng không phải lá. Suy luận ngoại
        // tuyến chỉ hỗ trợ một ảnh — dùng ảnh đầu tiên.
        result = await OfflineInferenceService.instance.diagnose(
          imageFile: widget.images.first,
          imageBytes: images.first.bytes,
          plotLabel: widget.plotName ?? 'Chưa gán lô đất',
        );
      }

      // Giữ tối thiểu ~2.6s để ba bước phía trên kịp chạy hết, đúng nhịp
      // prototype — API thật thường nhanh hơn khoảng đó (~350ms trên CPU).
      await Future<void>.delayed(const Duration(milliseconds: 2600));
      _setStep(3);
      if (!mounted) return;
      AppNav.replace(context, (_) => ResultScreen(diagnosisCase: result));
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.message);
    } catch (_) {
      if (mounted) {
        setState(() => _error = 'Không phân tích được ảnh, kể cả ở chế độ ngoại tuyến. Thử lại nhé.');
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return AgriScreen(
      child: Center(
        child: SingleChildScrollView(
          padding: EdgeInsets.fromLTRB(
            28,
            AgriMetrics.screenTop(context),
            28,
            40,
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            mainAxisSize: MainAxisSize.min,
            children: _error != null ? _errorContent() : _progressContent(),
          ),
        ),
      ),
    );
  }

  /// `true` khi bộ chặn #92 từ chối ảnh — không phải một lỗi hệ thống nên
  /// hiện màn phản hồi riêng, nhẹ nhàng hơn (xem `_notTomatoLeafMessage`).
  bool get _isNotTomatoLeaf => _error == _notTomatoLeafMessage;

  List<Widget> _errorContent() {
    final bool notLeaf = _isNotTomatoLeaf;
    return <Widget>[
      Center(
        child: GlassCard(
          style: const GlassStyle(
            topOpacity: .82,
            bottomOpacity: .41,
            borderOpacity: .62,
            blurSigma: 28,
          ),
          radius: 999,
          width: 136,
          height: 136,
          child: Center(
            child: notLeaf
                ? AgriIcons.camera(48, body: AgriColors.olive, lens: AgriColors.primary)
                : AgriIcons.warning(48, triangle: AgriColors.accent, mark: AgriColors.inkOnAccent),
          ),
        ),
      ),
      const SizedBox(height: 28),
      Text(
        notLeaf ? 'Chưa nhận diện được lá cà chua' : 'Không phân tích được ảnh',
        textAlign: TextAlign.center,
        style: agriStyle(size: 22, weight: FontWeight.w700, em: -0.02),
      ),
      const SizedBox(height: 8),
      Text(
        _error!,
        textAlign: TextAlign.center,
        style: agriStyle(size: 14, color: AgriColors.inkA(.72)),
      ),
      const SizedBox(height: 24),
      PrimaryPillButton(
        label: 'Quay lại chụp ảnh khác',
        icon: AgriIcons.arrowRight(22, AgriColors.primary),
        onPressed: () => Navigator.of(context).pop(),
      ),
    ];
  }

  List<Widget> _progressContent() {
    return <Widget>[
      Center(
        child: AgriPulse(
          child: GlassCard(
            style: const GlassStyle(
              topOpacity: .82,
              bottomOpacity: .41,
              borderOpacity: .62,
              blurSigma: 28,
            ),
            radius: 999,
            width: 136,
            height: 136,
            child: Center(
              child: AgriIcons.leaf(64, a: AgriColors.olive, b: AgriColors.primary),
            ),
          ),
        ),
      ),
      const SizedBox(height: 28),
      Text(
        'Đang phân tích ảnh…',
        textAlign: TextAlign.center,
        style: agriStyle(size: 24, weight: FontWeight.w700, em: -0.02),
      ),
      const SizedBox(height: 8),
      Text(
        'Thường mất 2–4 giây tuỳ đường mạng.',
        textAlign: TextAlign.center,
        style: agriStyle(size: 14, color: AgriColors.inkA(.72)),
      ),
      const SizedBox(height: 28),
      for (int i = 0; i < _labels.length; i++) ...<Widget>[
        _StepRow(index: i, label: _labels[i], done: _step > i),
        if (i != _labels.length - 1) const SizedBox(height: 11),
      ],
      const SizedBox(height: 26),
      AgriProgressBar(
        value: (_step * 0.334).clamp(0.0, 1.0),
        height: 8,
        gradient: agriProgressGradient,
        animate: true,
      ),
    ];
  }
}

class _StepRow extends StatelessWidget {
  const _StepRow({
    required this.index,
    required this.label,
    required this.done,
  });

  final int index;
  final String label;
  final bool done;

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      radius: 22,
      blurSigma: 26,
      gradient: done
          ? agriExplainGradient
          : const GlassStyle(
              topOpacity: .8,
              bottomOpacity: .4,
              borderOpacity: .6,
            ).gradient,
      border: Border.all(color: AgriColors.whiteA(.6)),
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      child: Row(
        children: <Widget>[
          Container(
            width: 26,
            height: 26,
            decoration: BoxDecoration(
              color: done ? AgriColors.primary : AgriColors.inkSoftA(.2),
              shape: BoxShape.circle,
            ),
            alignment: Alignment.center,
            child: Text(
              done ? '✓' : '${index + 1}',
              style: agriStyle(
                size: 12,
                weight: FontWeight.w700,
                color: const Color(0xFFFFFFFF),
              ),
            ),
          ),
          const SizedBox(width: 13),
          Expanded(
            child: Text(
              label,
              style: agriStyle(
                size: 14.5,
                weight: FontWeight.w600,
                color: done ? AgriColors.ink : AgriColors.inkA(.68),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
