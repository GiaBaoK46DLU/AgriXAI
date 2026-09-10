import 'dart:async';
import 'dart:io';
import 'dart:typed_data';

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
  const AnalyzingScreen({required this.images, this.plotId, this.plotName, super.key});

  final List<File> images;
  final int? plotId;

  /// Tên lô đất để hiện trên kết quả nếu phải rơi về suy luận ngoại tuyến —
  /// lúc đó không gọi được `GET /plots` nên phải mang theo từ màn Chụp ảnh.
  final String? plotName;

  @override
  State<AnalyzingScreen> createState() => _AnalyzingScreenState();
}

class _AnalyzingScreenState extends State<AnalyzingScreen> {
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

  Future<({List<int> bytes, String filename})> _compress(File file) async {
    final Uint8List? compressed = await FlutterImageCompress.compressWithFile(
      file.path,
      quality: 82,
      minWidth: 1280,
      minHeight: 1280,
    );
    final List<int> bytes = compressed ?? await file.readAsBytes();
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
        );
      } catch (_) {
        // Không gọi được backend (mất mạng, sập tường lửa, server tắt...) —
        // tự chuyển sang mô hình chạy ngay trên máy (xem CLAUDE.md mục suy
        // luận ngoại tuyến). Không phân biệt loại lỗi mạng cụ thể vì với
        // nông dân, "cứ ra được kết quả" quan trọng hơn thông báo lỗi chi tiết.
        // Suy luận ngoại tuyến chỉ hỗ trợ một ảnh — dùng ảnh đầu tiên.
        result = await OfflineInferenceService.instance.diagnose(
          imageFile: widget.images.first,
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

  List<Widget> _errorContent() {
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
            child: AgriIcons.warning(48, triangle: AgriColors.accent, mark: AgriColors.inkOnAccent),
          ),
        ),
      ),
      const SizedBox(height: 28),
      Text(
        'Không phân tích được ảnh',
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
