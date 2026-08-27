import 'package:flutter/material.dart';

import '../../core/app_colors.dart';
import '../../core/app_glass.dart';
import '../../core/app_metrics.dart';
import '../../core/app_scope.dart';
import '../../core/app_typography.dart';
import '../../data/demo_data.dart';
import '../../models/models.dart';
import '../../widgets/agri_icons.dart';
import '../../widgets/buttons.dart';
import '../../widgets/glass_bottom_bar.dart';
import '../../widgets/glass_card.dart';
import '../../widgets/image_slot.dart';
import '../../widgets/misc.dart';
import '../../widgets/rows.dart';
import '../capture/capture_screen.dart';
import '../plot/plot_detail_screen.dart';
import '../plot/plot_form_screen.dart';
import '../result/result_screen.dart';

/// **02 Trang chủ · lô đất** — UC-M3.
///
/// API khi nối thật: `GET /plots` và `GET /diagnoses?limit=3`. Ô thời tiết
/// chưa có endpoint — xem mục 8 của README bàn giao.
class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    // Cắt sẵn rồi mới đọc theo chỉ số. Đọc thẳng `history[2]` thì tài khoản
    // chưa chẩn đoán đủ ba lần là ném `RangeError` — chắc chắn xảy ra khi
    // thay dữ liệu mẫu bằng `GET /diagnoses`.
    final List<DiagnosisEntry> recent = DemoData.history.take(3).toList();

    return SingleChildScrollView(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          const _Hero(),
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 18, 16, 22),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: <Widget>[
                const _UrgentCard(),
                const SizedBox(height: 14),
                _DiagnoseButton(
                  onPressed: () =>
                      AppNav.push(context, (_) => const CaptureScreen()),
                ),
                const SizedBox(height: 24),
                SectionHeader(
                  title: 'Lô đất của bạn',
                  action: GlassPillButton(
                    label: '+ Thêm lô',
                    onPressed: () =>
                        AppNav.push(context, (_) => const PlotFormScreen()),
                    minHeight: 40,
                    fontSize: 13.5,
                    color: AgriColors.primary,
                    style: GlassStyle.field,
                  ),
                ),
                const SizedBox(height: 12),
                for (final Plot plot in DemoData.plots) ...<Widget>[
                  PlotCard(
                    plot: plot,
                    onTap: () => AppNav.push(
                      context,
                      (_) => PlotDetailScreen(plotId: plot.id),
                    ),
                  ),
                  if (plot != DemoData.plots.last) const SizedBox(height: 11),
                ],
                const SizedBox(height: 26),
                SectionHeader(
                  title: 'Chẩn đoán gần đây',
                  action: GhostButton(
                    label: 'Tất cả',
                    onPressed: () =>
                        AppScope.read(context).select(AgriTab.history),
                  ),
                ),
                const SizedBox(height: 12),
                for (int i = 0; i < recent.length; i++) ...<Widget>[
                  DiagnosisMiniRow(
                    entry: recent[i],
                    onTap: () => AppNav.push(
                      context,
                      (_) => ResultScreen(
                        diagnosisCase: DemoData.caseByKey(recent[i].caseKey),
                      ),
                    ),
                  ),
                  if (i != recent.length - 1) const SizedBox(height: 9),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }
}

/// Khối ảnh trên cùng: ảnh vườn + lớp phủ sáng + lời chào + ô thời tiết.
class _Hero extends StatelessWidget {
  const _Hero();

  @override
  Widget build(BuildContext context) {
    return ClipRRect(
      borderRadius: const BorderRadius.only(
        bottomLeft: Radius.circular(34),
        bottomRight: Radius.circular(34),
      ),
      child: Stack(
        children: <Widget>[
          const Positioned.fill(
            child: ImageSlot(placeholder: 'Ảnh vườn cà chua'),
          ),
          // linear-gradient(180deg, .9 0%, .72 26%, .44 52%, .84 100%)
          Positioned.fill(
            child: IgnorePointer(
              child: DecoratedBox(
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.topCenter,
                    end: Alignment.bottomCenter,
                    colors: <Color>[
                      AgriColors.heroVeil(.9),
                      AgriColors.heroVeil(.72),
                      AgriColors.heroVeil(.44),
                      AgriColors.heroVeil(.84),
                    ],
                    stops: const <double>[0, .26, .52, 1],
                  ),
                ),
              ),
            ),
          ),
          Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: <Widget>[
              Padding(
                padding: EdgeInsets.fromLTRB(
                  20,
                  AgriMetrics.screenTop(context),
                  20,
                  4,
                ),
                child: const _GreetingRow(),
              ),
              const Padding(
                padding: EdgeInsets.symmetric(horizontal: 14, vertical: 16),
                child: _WeatherCard(),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _GreetingRow extends StatelessWidget {
  const _GreetingRow();

  @override
  Widget build(BuildContext context) {
    return Row(
      children: <Widget>[
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Text(
                'Chào anh Học',
                style: agriStyle(size: 19, weight: FontWeight.w700, em: -0.01),
              ),
              const SizedBox(height: 2),
              Text(
                'Thứ Năm, 21/08 · Cam Ly, Đà Lạt',
                style: agriStyle(
                  size: 12.5,
                  weight: FontWeight.w600,
                  color: AgriColors.inkA(.88),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(width: 12),
        GlassCard(
          style: const GlassStyle(
            topOpacity: .82,
            bottomOpacity: .48,
            borderOpacity: .75,
            borderWidth: 1.5,
            blurSigma: 20,
          ),
          radius: 999,
          width: 46,
          height: 46,
          onTap: () => AppScope.read(context).select(AgriTab.profile),
          child: Center(
            child: Text(
              'H',
              style: agriStyle(size: 16, weight: FontWeight.w700),
            ),
          ),
        ),
      ],
    );
  }
}

class _WeatherCard extends StatelessWidget {
  const _WeatherCard();

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      style: GlassStyle.floating,
      radius: 28,
      padding: const EdgeInsets.all(16),
      shadows: AgriShadows.hero(.13),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              AgriIcons.sun(46),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Row(
                      crossAxisAlignment: CrossAxisAlignment.baseline,
                      textBaseline: TextBaseline.alphabetic,
                      children: <Widget>[
                        Text(
                          '24°C',
                          style: agriStyle(
                            size: 32,
                            weight: FontWeight.w800,
                            em: -0.02,
                            height: 1,
                          ),
                        ),
                        const SizedBox(width: 8),
                        Text(
                          'Mát, nhiều mây',
                          style: agriStyle(
                            size: 13,
                            weight: FontWeight.w600,
                            color: AgriColors.inkSoftA(.78),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 3),
                    Text(
                      'Độ ẩm 60% · gió nhẹ · mưa phùn về đêm',
                      style: agriStyle(
                        size: 12.5,
                        weight: FontWeight.w500,
                        color: AgriColors.inkSoftA(.7),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),
          Row(
            children: <Widget>[
              for (final WeatherDay day in DemoData.weather) ...<Widget>[
                Expanded(child: _ForecastCell(day: day)),
                if (day != DemoData.weather.last) const SizedBox(width: 7),
              ],
            ],
          ),
          const SizedBox(height: 13),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 13, vertical: 11),
            decoration: BoxDecoration(
              color: AgriColors.weatherStripBg(),
              borderRadius: BorderRadius.circular(20),
            ),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Padding(
                  padding: const EdgeInsets.only(top: 1),
                  child: AgriIcons.warning(
                    19,
                    triangle: AgriColors.inkDeep,
                    mark: AgriColors.accent,
                  ),
                ),
                const SizedBox(width: 9),
                Expanded(
                  child: Text(
                    'Ẩm cao kéo dài — điều kiện thuận lợi cho mốc sương muộn. '
                    'Nên kiểm tra vườn hôm nay.',
                    style: agriStyle(
                      size: 12.5,
                      weight: FontWeight.w600,
                      height: 1.45,
                      color: AgriColors.inkDeep,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _ForecastCell extends StatelessWidget {
  const _ForecastCell({required this.day});

  final WeatherDay day;

  @override
  Widget build(BuildContext context) {
    final bool now = day.isNow;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 9),
      decoration: BoxDecoration(
        color: now ? AgriColors.accent : AgriColors.whiteA(.86),
        borderRadius: BorderRadius.circular(18),
        // Thiết kế ghi đè `border-color` cho mọi ô, kể cả ô không phải hôm nay.
        border: Border.all(color: AgriColors.forecastBorder),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: <Widget>[
          Text(
            day.day,
            style: agriStyle(
              size: 10.5,
              weight: FontWeight.w600,
              color: now
                  ? AgriColors.inkOnAccentA(.7)
                  : AgriColors.inkA(.8),
            ),
          ),
          const SizedBox(height: 5),
          Container(
            width: 9,
            height: 9,
            decoration: BoxDecoration(
              color: now ? AgriColors.inkOnAccent : AgriColors.inkA(.68),
              shape: BoxShape.circle,
            ),
          ),
          const SizedBox(height: 5),
          Text(
            day.temp,
            style: agriStyle(
              size: 12.5,
              weight: FontWeight.w700,
              color: now ? AgriColors.inkOnAccent : AgriColors.ink,
            ),
          ),
        ],
      ),
    );
  }
}

/// Thẻ cảnh báo "Cần xử lý trong 24 giờ".
class _UrgentCard extends StatelessWidget {
  const _UrgentCard();

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      radius: 28,
      blurSigma: 26,
      color: AgriColors.alertCardBg,
      border: Border.all(color: AgriColors.alertCardBorder()),
      padding: const EdgeInsets.all(16),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Padding(
            padding: const EdgeInsets.only(top: 2),
            child: AgriIcons.warning(
              22,
              triangle: AgriColors.accent,
              mark: AgriColors.inkOnAccent,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(
                  'Cần xử lý trong 24 giờ',
                  style: agriStyle(size: 15.5, weight: FontWeight.w700),
                ),
                const SizedBox(height: 3),
                Text.rich(
                  TextSpan(
                    children: <InlineSpan>[
                      const TextSpan(text: 'Lô '),
                      TextSpan(
                        text: 'Vườn nhà trên',
                        style: agriStyle(
                          size: 13.5,
                          weight: FontWeight.w700,
                          height: 1.45,
                          color: AgriColors.accentInk,
                        ),
                      ),
                      const TextSpan(
                        text: ' có dấu hiệu Mốc sương muộn ở mức Nặng.',
                      ),
                    ],
                  ),
                  style: agriStyle(
                    size: 13.5,
                    height: 1.45,
                    color: AgriColors.inkSoftA(.76),
                  ),
                ),
                const SizedBox(height: 11),
                const _ViewResultButton(),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _ViewResultButton extends StatelessWidget {
  const _ViewResultButton();

  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: Alignment.centerLeft,
      child: DecoratedBox(
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(999),
          boxShadow: AgriShadows.amberButton(),
        ),
        child: Material(
          color: const Color(0x00000000),
          borderRadius: BorderRadius.circular(999),
          child: InkWell(
            borderRadius: BorderRadius.circular(999),
            onTap: () => AppNav.push(
              context,
              (_) => ResultScreen(
                diagnosisCase: DemoData.caseByKey('severe'),
              ),
            ),
            child: Ink(
              decoration: BoxDecoration(
                color: AgriColors.alertButtonBg(),
                borderRadius: BorderRadius.circular(999),
                border: Border.all(color: AgriColors.whiteA(.6)),
              ),
              child: Container(
                constraints: const BoxConstraints(minHeight: 40),
                padding: const EdgeInsets.symmetric(horizontal: 17),
                alignment: Alignment.center,
                child: Text(
                  'Xem kết quả',
                  style: agriStyle(
                    size: 13.5,
                    weight: FontWeight.w700,
                    color: AgriColors.accentInkDarkest,
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

/// Nút lớn "Chẩn đoán bệnh".
class _DiagnoseButton extends StatelessWidget {
  const _DiagnoseButton({required this.onPressed});

  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      radius: 30,
      blurSigma: 26,
      gradient: agriBigActionGradient,
      border: Border.all(color: AgriColors.whiteA(.62)),
      shadows: AgriShadows.bigAction(),
      onTap: onPressed,
      padding: const EdgeInsets.all(16),
      child: Row(
        children: <Widget>[
          Container(
            width: 54,
            height: 54,
            decoration: BoxDecoration(
              color: AgriColors.whiteA(.24),
              borderRadius: BorderRadius.circular(20),
            ),
            alignment: Alignment.center,
            child: AgriIcons.camera(
              28,
              body: AgriColors.cream,
              lens: AgriColors.primary,
            ),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(
                  'Chẩn đoán bệnh',
                  style: agriStyle(
                    size: 20,
                    weight: FontWeight.w700,
                    em: -0.01,
                    color: const Color(0xFFFFFFFF),
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  'Chụp ảnh hoặc tải ảnh lá lên',
                  style: agriStyle(
                    size: 13.5,
                    color: AgriColors.whiteA(.82),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
