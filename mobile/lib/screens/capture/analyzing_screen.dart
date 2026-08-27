import 'dart:async';

import 'package:flutter/material.dart';

import '../../core/app_colors.dart';
import '../../core/app_glass.dart';
import '../../core/app_metrics.dart';
import '../../core/app_scope.dart';
import '../../core/app_transitions.dart';
import '../../core/app_typography.dart';
import '../../data/demo_data.dart';
import '../../widgets/agri_icons.dart';
import '../../widgets/agri_screen.dart';
import '../../widgets/glass_card.dart';
import '../../widgets/misc.dart';
import '../result/result_screen.dart';

/// **04 Đang phân tích** — UC-M7.
///
/// Mốc thời gian lấy đúng prototype: 600ms · 1400ms · 2100ms rồi 2600ms sang
/// màn 05. App thật cho từng bước chạy theo trạng thái request thực.
class AnalyzingScreen extends StatefulWidget {
  const AnalyzingScreen({super.key});

  @override
  State<AnalyzingScreen> createState() => _AnalyzingScreenState();
}

class _AnalyzingScreenState extends State<AnalyzingScreen> {
  static const List<String> _labels = <String>[
    'Tải ảnh lên máy chủ',
    'Nhận diện bệnh (ResNet-50)',
    'Khoanh vùng nghi ngờ (Grad-CAM)',
  ];

  final List<Timer> _timers = <Timer>[];
  int _step = 0;

  @override
  void initState() {
    super.initState();
    _timers.addAll(<Timer>[
      Timer(const Duration(milliseconds: 600), () => _setStep(1)),
      Timer(const Duration(milliseconds: 1400), () => _setStep(2)),
      Timer(const Duration(milliseconds: 2100), () => _setStep(3)),
      Timer(const Duration(milliseconds: 2600), _openResult),
    ]);
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

  void _openResult() {
    if (!mounted) return;
    AppNav.replace(
      context,
      (_) => ResultScreen(diagnosisCase: DemoData.caseByKey('severe')),
    );
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
            children: <Widget>[
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
                      child: AgriIcons.leaf(
                        64,
                        a: AgriColors.olive,
                        b: AgriColors.primary,
                      ),
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
            ],
          ),
        ),
      ),
    );
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
