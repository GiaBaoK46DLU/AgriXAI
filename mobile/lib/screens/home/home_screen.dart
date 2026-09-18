import 'dart:async';

import 'package:flutter/material.dart';

import '../../core/app_colors.dart';
import '../../core/app_glass.dart';
import '../../core/app_metrics.dart';
import '../../core/app_scope.dart';
import '../../core/app_typography.dart';
import '../../models/models.dart';
import '../../services/api_client.dart';
import '../../services/session.dart' as session;
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

const List<String> _weekdayVi = <String>[
  'Thứ Hai',
  'Thứ Ba',
  'Thứ Tư',
  'Thứ Năm',
  'Thứ Sáu',
  'Thứ Bảy',
  'Chủ Nhật',
];

/// **02 Trang chủ · lô đất** — UC-M3.
///
/// Nối `GET /plots`, `GET /diagnoses?page_size=3` và `GET /weather` thật.
class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  bool _loading = true;
  String? _error;
  List<Plot> _plots = <Plot>[];
  List<DiagnosisEntry> _recent = <DiagnosisEntry>[];
  WeatherSnapshot? _weather;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final List<dynamic> plotsBody =
          await session.apiClient.get('/plots') as List<dynamic>;
      final ({List<DiagnosisEntry> items, int total}) recentPage =
          await session.diagnosisService.list(pageSize: 3);
      if (!mounted) return;
      setState(() {
        _plots = plotsBody
            .map((dynamic p) => Plot.fromJson(p as Map<String, dynamic>))
            .toList();
        _recent = recentPage.items;
        _loading = false;
      });
    } on ApiException catch (e) {
      if (mounted) setState(() { _error = e.message; _loading = false; });
    } catch (_) {
      if (mounted) {
        setState(() {
          _error = 'Không tải được trang chủ — kiểm tra kết nối mạng rồi thử lại.';
          _loading = false;
        });
      }
    }
    // Ô thời tiết tải riêng: hỏng thì chỉ ô đó rơi về trạng thái "--", không
    // kéo sập cả trang chủ (xem rủi ro kết nối mạng lúc demo trong CLAUDE.md).
    unawaited(_loadWeather());
  }

  Future<void> _loadWeather() async {
    try {
      final WeatherSnapshot w = await session.weatherService.fetch();
      if (mounted) setState(() => _weather = w);
    } catch (_) {
      // Bỏ qua — `_WeatherCard` tự hiện trạng thái "chưa có dữ liệu".
    }
  }

  /// Chỉ tính "cần xử lý" khi lần chẩn đoán Nặng gần nhất còn trong 24 giờ —
  /// theo yêu cầu của Học: qua khỏi 24 giờ thì banner tự biến mất, không hiện
  /// mãi mãi dù lô đất chưa từng chẩn đoán lại.
  Plot? get _urgentPlot {
    final DateTime now = DateTime.now();
    for (final Plot plot in _plots) {
      final DateTime? at = plot.lastDiagnosisAt;
      if (plot.lastSeverity == Severity.severe &&
          at != null &&
          now.difference(at) < const Duration(hours: 24)) {
        return plot;
      }
    }
    return null;
  }

  Future<void> _openPlot(Plot plot) async {
    await AppNav.push(context, (_) => PlotDetailScreen(plotId: plot.id));
    if (mounted) _load();
  }

  Future<void> _addPlot() async {
    await AppNav.push(context, (_) => const PlotFormScreen());
    if (mounted) _load();
  }

  Future<void> _openDiagnosis(DiagnosisEntry entry) async {
    try {
      final DiagnosisCase detail = await session.diagnosisService.get(entry.id);
      if (!mounted) return;
      await AppNav.push(context, (_) => ResultScreen(diagnosisCase: detail));
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Không mở được chi tiết bản ghi này')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final Plot? urgent = _urgentPlot;

    return RefreshIndicator(
      onRefresh: _load,
      child: SingleChildScrollView(
        physics: const AlwaysScrollableScrollPhysics(),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: <Widget>[
            _Hero(weather: _weather),
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 18, 16, 22),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: <Widget>[
                  if (urgent != null) ...<Widget>[
                    UrgentBanner(
                      plotName: urgent.name,
                      diseaseName: urgent.lastDisease,
                      onViewResult: () => _openPlot(urgent),
                    ),
                    const SizedBox(height: 14),
                  ],
                  _DiagnoseButton(
                    onPressed: () =>
                        AppNav.push(context, (_) => const CaptureScreen()),
                  ),
                  const SizedBox(height: 24),
                  SectionHeader(
                    title: 'Lô đất của bạn',
                    action: GlassPillButton(
                      label: '+ Thêm lô',
                      onPressed: _addPlot,
                      minHeight: 40,
                      fontSize: 13.5,
                      color: AgriColors.primary,
                      style: GlassStyle.field,
                    ),
                  ),
                  const SizedBox(height: 12),
                  if (_loading)
                    const Padding(
                      padding: EdgeInsets.symmetric(vertical: 30),
                      child: Center(child: CircularProgressIndicator()),
                    )
                  else if (_error != null)
                    _errorState()
                  else if (_plots.isEmpty)
                    Padding(
                      padding: const EdgeInsets.symmetric(vertical: 16),
                      child: Text(
                        'Chưa có lô đất nào — nhấn "+ Thêm lô" để bắt đầu theo dõi.',
                        style: agriStyle(size: 13.5, color: AgriColors.inkA(.68)),
                      ),
                    )
                  else
                    for (final Plot plot in _plots) ...<Widget>[
                      PlotCard(plot: plot, onTap: () => _openPlot(plot)),
                      if (plot != _plots.last) const SizedBox(height: 11),
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
                  if (!_loading && _error == null)
                    if (_recent.isEmpty)
                      Padding(
                        padding: const EdgeInsets.symmetric(vertical: 12),
                        child: Text(
                          'Chưa có lần chẩn đoán nào gắn với lô đất.',
                          style: agriStyle(size: 13, color: AgriColors.inkA(.65)),
                        ),
                      )
                    else
                      for (int i = 0; i < _recent.length; i++) ...<Widget>[
                        DiagnosisMiniRow(
                          entry: _recent[i],
                          onTap: () => _openDiagnosis(_recent[i]),
                        ),
                        if (i != _recent.length - 1) const SizedBox(height: 9),
                      ],
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _errorState() {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 20),
      child: Column(
        children: <Widget>[
          Text(
            _error!,
            textAlign: TextAlign.center,
            style: agriStyle(size: 13.5, color: AgriColors.inkA(.7)),
          ),
          const SizedBox(height: 10),
          GlassPillButton(
            label: 'Thử lại',
            onPressed: _load,
            minHeight: 40,
            fontSize: 13.5,
          ),
        ],
      ),
    );
  }
}

/// Khối ảnh trên cùng: ảnh vườn + lớp phủ sáng + lời chào + ô thời tiết.
class _Hero extends StatelessWidget {
  const _Hero({required this.weather});

  final WeatherSnapshot? weather;

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
                child: _GreetingRow(location: weather?.location),
              ),
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 16),
                child: _WeatherCard(weather: weather),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _GreetingRow extends StatelessWidget {
  const _GreetingRow({this.location});

  final String? location;

  @override
  Widget build(BuildContext context) {
    final String name = session.currentUser?.fullName.split(' ').last ?? 'bạn';
    final DateTime now = DateTime.now();
    final String dateLabel =
        '${_weekdayVi[now.weekday - 1]}, ${now.day.toString().padLeft(2, '0')}/'
        '${now.month.toString().padLeft(2, '0')}';

    return Row(
      children: <Widget>[
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Text(
                'Chào bác $name',
                style: agriStyle(size: 19, weight: FontWeight.w700, em: -0.01),
              ),
              const SizedBox(height: 2),
              Text(
                '$dateLabel · ${location ?? 'Đà Lạt'}',
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
              name.isEmpty ? '?' : name.substring(0, 1).toUpperCase(),
              style: agriStyle(size: 16, weight: FontWeight.w700),
            ),
          ),
        ),
      ],
    );
  }
}

class _WeatherCard extends StatelessWidget {
  const _WeatherCard({required this.weather});

  final WeatherSnapshot? weather;

  @override
  Widget build(BuildContext context) {
    final WeatherSnapshot? w = weather;
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
                          w == null ? '--°C' : '${w.temp}°C',
                          style: agriStyle(
                            size: 32,
                            weight: FontWeight.w800,
                            em: -0.02,
                            height: 1,
                          ),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            w?.description ?? 'Đang tải thời tiết…',
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: agriStyle(
                              size: 13,
                              weight: FontWeight.w600,
                              color: AgriColors.inkSoftA(.78),
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 3),
                    Text(
                      w?.detail ?? 'Không tải được thông tin thời tiết.',
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
          if (w != null && w.forecast.isNotEmpty) ...<Widget>[
            const SizedBox(height: 14),
            Row(
              children: <Widget>[
                for (final WeatherDay day in w.forecast) ...<Widget>[
                  Expanded(child: _ForecastCell(day: day)),
                  if (day != w.forecast.last) const SizedBox(width: 7),
                ],
              ],
            ),
          ],
          if (w?.advisory != null) ...<Widget>[
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
                      w!.advisory!,
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
                  'Chụp ảnh nhanh — không gắn lô đất, không lưu lịch sử',
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
