import 'package:flutter/material.dart';
import 'package:flutter_tts/flutter_tts.dart';

import '../../core/app_colors.dart';
import '../../core/app_glass.dart';
import '../../core/app_metrics.dart';
import '../../core/app_scope.dart';
import '../../core/app_typography.dart';
import '../../data/demo_data.dart';
import '../../models/models.dart';
import '../../widgets/agri_icons.dart';
import '../../widgets/agri_screen.dart';
import '../../widgets/buttons.dart';
import '../../widgets/chips.dart';
import '../../widgets/glass_card.dart';
import '../../widgets/image_slot.dart';
import '../../widgets/misc.dart';
import '../capture/capture_screen.dart';
import 'treatment_screen.dart';

/// **05 Kết quả chẩn đoán** — UC-M8. Màn quan trọng nhất của đồ án: đây là
/// chỗ phần XAI hiện ra cho người dùng.
///
/// API khi nối thật: `POST /diagnoses` rồi `GET /diagnoses/{id}`. Nút gạt
/// "Vùng nghi ngờ / Ảnh gốc" chỉ đổi giữa `overlay_url` và `image_url`.
class ResultScreen extends StatefulWidget {
  const ResultScreen({required this.diagnosisCase, super.key});

  final DiagnosisCase diagnosisCase;

  @override
  State<ResultScreen> createState() => _ResultScreenState();
}

class _ResultScreenState extends State<ResultScreen> {
  bool _xai = true;
  bool _speaking = false;
  FlutterTts? _tts;

  DiagnosisCase get _case => widget.diagnosisCase;

  Disease get _disease => DemoData.diseaseByKey(_case.diseaseKey);

  @override
  void dispose() {
    _tts?.stop();
    super.dispose();
  }

  Future<void> _toggleSpeak() async {
    if (_speaking) {
      await _tts?.stop();
      if (mounted) setState(() => _speaking = false);
      return;
    }

    final String text = '${_disease.name}. ${_case.explanation}'
        '${_case.urgent == null ? '' : ' ${_case.urgent}'}';

    try {
      final FlutterTts tts = _tts ??= FlutterTts();
      await tts.setLanguage('vi-VN');
      tts.setCompletionHandler(() {
        if (mounted) setState(() => _speaking = false);
      });
      tts.setCancelHandler(() {
        if (mounted) setState(() => _speaking = false);
      });
      tts.setErrorHandler((dynamic _) {
        if (mounted) setState(() => _speaking = false);
      });
      setState(() => _speaking = true);
      await tts.speak(text);
    } catch (_) {
      // Máy chưa cài giọng tiếng Việt thì chỉ trả nút về trạng thái ban đầu.
      if (mounted) setState(() => _speaking = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return AgriScreen(
      child: SingleChildScrollView(
        padding: EdgeInsets.fromLTRB(
          16,
          AgriMetrics.screenTop(context),
          16,
          22,
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: <Widget>[
            ScreenHeader(
              title: 'Kết quả chẩn đoán',
              onBack: () => Navigator.of(context).pop(),
              expandTitle: true,
              trailing: GlassIconButton(
                icon: AgriIcons.share(20, AgriColors.primary),
                onPressed: () {},
                tooltip: 'Chia sẻ kết quả',
              ),
            ),
            const SizedBox(height: 16),
            _imageFrame(),
            const SizedBox(height: 16),
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: <Widget>[
                      Text(
                        _disease.pathogen.toUpperCase(),
                        style: AgriTextStyles.kicker(AgriColors.oliveInk),
                      ),
                      const SizedBox(height: 5),
                      Text(
                        _disease.name,
                        style: agriStyle(
                          size: 26,
                          weight: FontWeight.w800,
                          em: -0.02,
                          height: 1.12,
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 11),
                SeverityChip(
                  severity: _case.severity,
                  fontSize: 13,
                  padding: const EdgeInsets.symmetric(
                    horizontal: 15,
                    vertical: 8,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            _metricsCard(),
            const SizedBox(height: 14),
            _explainCard(),
            const SizedBox(height: 14),
            _top3Card(),
            const SizedBox(height: 16),
            Wrap(
              spacing: 7,
              runSpacing: 7,
              children: <Widget>[
                MetaChip(label: _case.plot),
                MetaChip(label: _case.time),
                const MetaChip(label: DemoData.modelBadge),
              ],
            ),
            const SizedBox(height: 14),
            Text(
              DemoData.disclaimer,
              style: agriStyle(
                size: 12,
                height: 1.55,
                color: AgriColors.inkA(.62),
              ),
            ),
            const SizedBox(height: 18),
            PrimaryPillButton(
              label: 'Xem gợi ý xử lý',
              icon: AgriIcons.arrowRight(22, AgriColors.primary),
              onPressed: () => AppNav.push(
                context,
                (_) => TreatmentScreen(diagnosisCase: _case),
              ),
            ),
            const SizedBox(height: 10),
            Row(
              children: <Widget>[
                Expanded(
                  child: GlassPillButton(
                    label: 'Thêm ghi chú',
                    onPressed: () {},
                    minHeight: 48,
                    fontSize: 14.5,
                    style: GlassStyle.field,
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: GlassPillButton(
                    label: 'Chụp lại',
                    onPressed: () =>
                        AppNav.push(context, (_) => const CaptureScreen()),
                    minHeight: 48,
                    fontSize: 14.5,
                    style: GlassStyle.field,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  /// Khung ảnh 272px + lớp Grad-CAM + nút gạt XAI.
  Widget _imageFrame() {
    return Container(
      height: 272,
      decoration: BoxDecoration(
        color: AgriColors.viewfinderVoid,
        borderRadius: BorderRadius.circular(32),
        border: Border.all(color: AgriColors.whiteA(.62)),
        boxShadow: AgriShadows.hero(),
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(32),
        child: Stack(
          children: <Widget>[
            const Positioned.fill(
              child: ImageSlot(
                placeholder: 'Kéo ảnh lá bệnh vào đây',
                onDark: true,
              ),
            ),
            if (_xai) const Positioned.fill(child: GradCamOverlay()),
            Positioned(
              top: 14,
              right: 14,
              child: GlassCard(
                style: GlassStyle.overImage,
                blurSigma: 26,
                radius: 999,
                padding: const EdgeInsets.all(4),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: <Widget>[
                    _xaiToggle('Vùng nghi ngờ', _xai, () {
                      setState(() => _xai = true);
                    }),
                    const SizedBox(width: 4),
                    _xaiToggle('Ảnh gốc', !_xai, () {
                      setState(() => _xai = false);
                    }),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _xaiToggle(String label, bool active, VoidCallback onTap) {
    return Material(
      color: const Color(0x00000000),
      borderRadius: BorderRadius.circular(999),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(999),
        child: Ink(
          decoration: BoxDecoration(
            gradient: active ? agriPrimaryGradient : null,
            borderRadius: BorderRadius.circular(999),
          ),
          child: Container(
            constraints: const BoxConstraints(minHeight: 34),
            padding: const EdgeInsets.symmetric(horizontal: 14),
            alignment: Alignment.center,
            child: Text(
              label,
              style: agriStyle(
                size: 12,
                weight: FontWeight.w600,
                color: active ? const Color(0xFFFFFFFF) : AgriColors.ink,
              ),
            ),
          ),
        ),
      ),
    );
  }

  /// Hai thanh: độ tin cậy và tỉ lệ vùng nghi ngờ.
  Widget _metricsCard() {
    return GlassCard(
      style: GlassStyle.card,
      radius: 28,
      padding: const EdgeInsets.all(18),
      shadows: AgriShadows.raised(.12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          _metricRow(
            'Độ tin cậy',
            _case.confidence,
            gradient: agriProgressGradient,
          ),
          const SizedBox(height: 14),
          _metricRow(
            'Vùng nghi ngờ trên ảnh',
            _case.affected,
            color: AgriColors.accent,
          ),
        ],
      ),
    );
  }

  Widget _metricRow(
    String label,
    String value, {
    Gradient? gradient,
    Color? color,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: <Widget>[
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: <Widget>[
            Text(
              label,
              style: agriStyle(
                size: 13.5,
                weight: FontWeight.w600,
                color: AgriColors.inkA(.74),
              ),
            ),
            Text(
              value,
              style: agriStyle(size: 13.5, weight: FontWeight.w600),
            ),
          ],
        ),
        const SizedBox(height: 7),
        AgriProgressBar(
          value: DemoData.percentToFraction(value),
          gradient: gradient,
          color: color,
        ),
      ],
    );
  }

  /// Thẻ giải thích XAI — phần cốt lõi của đề tài.
  Widget _explainCard() {
    return GlassCard(
      radius: 28,
      blurSigma: 28,
      gradient: agriExplainGradient,
      border: Border.all(color: AgriColors.whiteA(.6)),
      padding: const EdgeInsets.all(18),
      shadows: <BoxShadow>[
        BoxShadow(
          color: AgriColors.shadowA(.14),
          offset: const Offset(0, 12),
          blurRadius: 28,
        ),
      ],
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          Row(
            children: <Widget>[
              AgriIcons.info(18),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  'VÌ SAO HỆ THỐNG KẾT LUẬN VẬY?',
                  style: AgriTextStyles.kicker(AgriColors.primary),
                ),
              ),
              const SizedBox(width: 8),
              _speakButton(),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            _case.explanation,
            style: agriStyle(size: 15, height: 1.58),
          ),
        ],
      ),
    );
  }

  Widget _speakButton() {
    return Material(
      color: const Color(0x00000000),
      borderRadius: BorderRadius.circular(999),
      child: InkWell(
        onTap: _toggleSpeak,
        borderRadius: BorderRadius.circular(999),
        child: Ink(
          decoration: BoxDecoration(
            color: _speaking ? null : AgriColors.whiteA(.55),
            gradient: _speaking ? agriPrimaryGradient : null,
            borderRadius: BorderRadius.circular(999),
            border: Border.all(color: AgriColors.primaryA(.34)),
          ),
          child: Container(
            constraints: const BoxConstraints(minHeight: 34),
            padding: const EdgeInsets.symmetric(horizontal: 13),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: <Widget>[
                if (_speaking)
                  AgriIcons.stopSquare(15, const Color(0xFFFFFFFF))
                else
                  AgriIcons.speaker(15, AgriColors.primary),
                const SizedBox(width: 6),
                Text(
                  _speaking ? 'Dừng đọc' : 'Nghe đọc',
                  style: agriStyle(
                    size: 12,
                    weight: FontWeight.w700,
                    color: _speaking
                        ? const Color(0xFFFFFFFF)
                        : AgriColors.primary,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _top3Card() {
    return GlassCard(
      radius: 26,
      blurSigma: 26,
      gradient: const GlassStyle(
        topOpacity: .8,
        bottomOpacity: .4,
        borderOpacity: .6,
      ).gradient,
      border: Border.all(color: AgriColors.whiteA(.6)),
      padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 16),
      shadows: <BoxShadow>[
        BoxShadow(
          color: AgriColors.shadowA(.12),
          offset: const Offset(0, 10),
          blurRadius: 24,
        ),
      ],
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          Text(
            'Ba khả năng cao nhất',
            style: agriStyle(
              size: 13,
              weight: FontWeight.w600,
              color: AgriColors.inkA(.74),
            ),
          ),
          const SizedBox(height: 11),
          for (int i = 0; i < _case.top3.length; i++) ...<Widget>[
            _top3Row(i),
            if (i != _case.top3.length - 1) const SizedBox(height: 10),
          ],
        ],
      ),
    );
  }

  Widget _top3Row(int index) {
    final (String name, String percent) = _case.top3[index];
    final bool first = index == 0;
    return Row(
      children: <Widget>[
        Expanded(
          child: Text(
            name,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: agriStyle(
              size: 14,
              weight: first ? FontWeight.w700 : FontWeight.w500,
              color: AgriColors.top3Ink,
            ),
          ),
        ),
        const SizedBox(width: 11),
        SizedBox(
          width: 86,
          child: AgriProgressBar(
            value: DemoData.percentToFraction(percent),
            height: 7,
            gradient: first ? agriProgressGradient : null,
            color: first ? null : AgriColors.inkSoftA(.18),
          ),
        ),
        const SizedBox(width: 11),
        SizedBox(
          width: 40,
          child: Text(
            percent,
            textAlign: TextAlign.right,
            style: agriStyle(size: 13, weight: FontWeight.w700),
          ),
        ),
      ],
    );
  }
}
