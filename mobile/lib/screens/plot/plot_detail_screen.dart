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
import '../../widgets/agri_screen.dart';
import '../../widgets/buttons.dart';
import '../../widgets/glass_bottom_bar.dart';
import '../../widgets/glass_card.dart';
import '../../widgets/image_slot.dart';
import '../../widgets/misc.dart';
import '../../widgets/rows.dart';
import '../capture/capture_screen.dart';
import '../result/result_screen.dart';
import 'plot_form_screen.dart';

/// **08 Chi tiết lô đất** — UC-M3, UC-M5.
///
/// Nối `GET /plots/{id}`, `GET /diagnoses?plot_id=`, `DELETE /plots/{id}`.
/// Bệnh mức Nặng gần nhất trên lô này hiện banner "Cần xử lý trong 24 giờ" —
/// xem CLAUDE.md.
class PlotDetailScreen extends StatefulWidget {
  const PlotDetailScreen({required this.plotId, super.key});

  final int plotId;

  @override
  State<PlotDetailScreen> createState() => _PlotDetailScreenState();
}

class _PlotDetailScreenState extends State<PlotDetailScreen> {
  bool _loading = true;
  String? _error;
  bool _deleting = false;
  Plot? _plot;
  List<DiagnosisEntry> _rows = <DiagnosisEntry>[];
  int _total = 0;
  int? _openingId;

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
      final dynamic plotJson = await session.apiClient.get('/plots/${widget.plotId}');
      final ({List<DiagnosisEntry> items, int total}) page =
          await session.diagnosisService.list(plotId: widget.plotId, pageSize: 50);
      if (!mounted) return;
      setState(() {
        _plot = Plot.fromJson(plotJson as Map<String, dynamic>);
        _rows = page.items;
        _total = page.total;
        _loading = false;
      });
    } on ApiException catch (e) {
      if (mounted) setState(() { _error = e.message; _loading = false; });
    } catch (_) {
      if (mounted) {
        setState(() {
          _error = 'Không tải được lô đất — kiểm tra kết nối mạng rồi thử lại.';
          _loading = false;
        });
      }
    }
  }

  DiagnosisEntry? get _latest => _rows.isNotEmpty ? _rows.first : null;

  Future<void> _diagnoseForPlot() async {
    final Plot plot = _plot!;
    await AppNav.push(
      context,
      (_) => CaptureScreen(initialPlotId: plot.id, initialPlotName: plot.name),
    );
    if (mounted) _load();
  }

  Future<void> _openLatestResult() async {
    final DiagnosisEntry? entry = _latest;
    if (entry == null) return;
    await _openEntry(entry);
  }

  Future<void> _openEntry(DiagnosisEntry entry) async {
    if (_openingId != null) return;
    setState(() => _openingId = entry.id);
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
    } finally {
      if (mounted) setState(() => _openingId = null);
    }
  }

  Future<void> _confirmDelete() async {
    final bool? confirmed = await showDialog<bool>(
      context: context,
      builder: (BuildContext context) => AlertDialog(
        title: const Text('Xoá lô đất?'),
        content: Text(
          'Lịch sử chẩn đoán trên lô "${_plot?.name}" vẫn được giữ lại, chỉ '
          'không còn gắn với lô đất nào nữa.',
        ),
        actions: <Widget>[
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('Huỷ'),
          ),
          TextButton(
            onPressed: () => Navigator.of(context).pop(true),
            child: const Text('Xoá'),
          ),
        ],
      ),
    );
    if (confirmed != true || !mounted) return;

    setState(() => _deleting = true);
    try {
      await session.apiClient.delete('/plots/${widget.plotId}');
      if (!mounted) return;
      AppNav.toTab(context, AgriTab.plots);
    } on ApiException catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(e.message)));
      }
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Không xoá được lô đất, thử lại sau.')),
        );
      }
    } finally {
      if (mounted) setState(() => _deleting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return const AgriScreen(child: Center(child: CircularProgressIndicator()));
    }
    if (_error != null || _plot == null) {
      return AgriScreen(
        child: Padding(
          padding: EdgeInsets.fromLTRB(20, AgriMetrics.screenTop(context), 20, 20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: <Widget>[
              ScreenHeader(title: 'Lô đất', onBack: () => Navigator.of(context).pop()),
              const SizedBox(height: 40),
              Text(
                _error ?? 'Không tìm thấy lô đất này',
                textAlign: TextAlign.center,
                style: agriStyle(size: 14, color: AgriColors.inkA(.72)),
              ),
              const SizedBox(height: 14),
              PrimarySolidButton(label: 'Thử lại', onPressed: _load),
            ],
          ),
        ),
      );
    }

    final Plot plot = _plot!;
    final DiagnosisEntry? latest = _latest;
    final bool urgent = latest != null && latest.severity == Severity.severe;

    final List<(String, String)> facts = <(String, String)>[
      ('Mã vùng trồng', plot.puc),
      ('Khu vực', plot.region),
      ('Diện tích', plot.area),
      ('Cây trồng', 'Cà chua'),
      ('Trạng thái', plot.status),
      ('Số lần chẩn đoán', '$_total'),
    ];

    return AgriScreen(
      child: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: <Widget>[
            _hero(context, plot),
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 16, 16, 22),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: <Widget>[
                  if (urgent) ...<Widget>[
                    UrgentBanner(
                      plotName: plot.name,
                      diseaseName: latest.disease,
                      onViewResult: _openLatestResult,
                    ),
                    const SizedBox(height: 16),
                  ],
                  GlassCard(
                    style: GlassStyle.card,
                    radius: 26,
                    shadows: AgriShadows.raised(),
                    child: Column(
                      children: <Widget>[
                        for (final (String, String) fact in facts)
                          _factRow(fact.$1, fact.$2),
                      ],
                    ),
                  ),
                  const SizedBox(height: 16),
                  PrimarySolidButton(
                    label: 'Chẩn đoán cho lô này',
                    onPressed: _diagnoseForPlot,
                  ),
                  const SizedBox(height: 10),
                  GlassPillButton(
                    label: _deleting ? 'Đang xoá…' : 'Xoá lô đất',
                    onPressed: _deleting ? () {} : _confirmDelete,
                    minHeight: 48,
                    fontSize: 14.5,
                    fontWeight: FontWeight.w700,
                    color: AgriColors.accentInkDeep,
                    gradient: agriDangerGradient,
                    border: Border.all(color: AgriColors.accentA(.55)),
                    style: GlassStyle.control,
                  ),
                  const SizedBox(height: 22),
                  Text(
                    'Lịch sử trên lô này',
                    style: agriStyle(
                      size: 18.5,
                      weight: FontWeight.w700,
                      em: -0.01,
                    ),
                  ),
                  const SizedBox(height: 12),
                  if (_rows.isEmpty)
                    Padding(
                      padding: const EdgeInsets.symmetric(vertical: 12),
                      child: Text(
                        'Chưa có lần chẩn đoán nào trên lô này.',
                        style: agriStyle(size: 13, color: AgriColors.inkA(.65)),
                      ),
                    )
                  else
                    for (int i = 0; i < _rows.length; i++) ...<Widget>[
                      DiagnosisMiniRow(
                        entry: _rows[i],
                        style: GlassStyle.softFlat,
                        padding: const EdgeInsets.all(14),
                        onTap: () => _openEntry(_rows[i]),
                      ),
                      if (i != _rows.length - 1) const SizedBox(height: 10),
                    ],
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _hero(BuildContext context, Plot plot) {
    return ClipRRect(
      borderRadius: const BorderRadius.only(
        bottomLeft: Radius.circular(32),
        bottomRight: Radius.circular(32),
      ),
      child: SizedBox(
        height: 206,
        child: Stack(
          children: <Widget>[
            Positioned.fill(
              child: ImageSlot(placeholder: 'Ảnh lô đất', imageUrl: plot.imageUrl),
            ),
            // linear-gradient(180deg, .92 0%, .8 46%, .86 100%)
            Positioned.fill(
              child: IgnorePointer(
                child: DecoratedBox(
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      begin: Alignment.topCenter,
                      end: Alignment.bottomCenter,
                      colors: <Color>[
                        AgriColors.heroVeil(.92),
                        AgriColors.heroVeil(.8),
                        AgriColors.heroVeil(.86),
                      ],
                      stops: const <double>[0, .46, 1],
                    ),
                  ),
                ),
              ),
            ),
            Padding(
              padding: EdgeInsets.fromLTRB(
                16,
                AgriMetrics.screenTop(context),
                16,
                0,
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  GlassIconButton(
                    icon: AgriIcons.chevronLeft(21, AgriColors.ink),
                    onPressed: () => Navigator.of(context).pop(),
                    style: GlassStyle.overImage,
                    tooltip: 'Quay lại',
                  ),
                  const SizedBox(width: 11),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: <Widget>[
                        Text(
                          plot.name,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: agriStyle(
                            size: 20,
                            weight: FontWeight.w700,
                            em: -0.01,
                          ),
                        ),
                        Text(
                          plot.puc,
                          style: agriStyle(
                            size: 12.5,
                            weight: FontWeight.w600,
                            color: AgriColors.inkA(.88),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(width: 11),
                  GlassIconButton(
                    icon: AgriIcons.pencil(20, AgriColors.ink),
                    onPressed: () async {
                      await AppNav.push(context, (_) => PlotFormScreen(plot: plot));
                    },
                    style: GlassStyle.overImage,
                    tooltip: 'Sửa lô đất',
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _factRow(String label, String value) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 17, vertical: 14),
      decoration: BoxDecoration(
        border: Border(
          bottom: BorderSide(color: AgriColors.whiteA(.72)),
        ),
      ),
      child: Row(
        children: <Widget>[
          Expanded(
            child: Text(
              label,
              style: agriStyle(size: 13.5, color: AgriColors.inkA(.72)),
            ),
          ),
          const SizedBox(width: 10),
          Text(
            value,
            style: agriStyle(size: 14.5, weight: FontWeight.w700),
          ),
        ],
      ),
    );
  }
}
