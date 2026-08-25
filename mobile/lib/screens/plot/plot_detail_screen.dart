import 'package:flutter/material.dart';

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
import '../../widgets/glass_card.dart';
import '../../widgets/image_slot.dart';
import '../../widgets/rows.dart';
import '../capture/capture_screen.dart';
import '../result/result_screen.dart';
import 'plot_form_screen.dart';

/// **08 Chi tiết lô đất** — UC-M3, UC-M5.
///
/// API khi nối thật: `GET /plots/{id}`, `GET /diagnoses?plot_id=`,
/// `DELETE /plots/{id}`.
class PlotDetailScreen extends StatelessWidget {
  const PlotDetailScreen({required this.plotId, super.key});

  final int plotId;

  @override
  Widget build(BuildContext context) {
    final Plot plot = DemoData.plotById(plotId);
    final List<DiagnosisEntry> rows = DemoData.history
        .where((DiagnosisEntry h) => h.plotId == plot.id)
        .toList();

    final List<(String, String)> facts = <(String, String)>[
      ('Mã vùng trồng', plot.puc),
      ('Khu vực', plot.region),
      ('Diện tích', plot.area),
      ('Cây trồng', 'Cà chua'),
      ('Trạng thái', plot.status),
      ('Số lần chẩn đoán', '${plot.count}'),
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
                  Text(
                    'Lịch sử trên lô này',
                    style: agriStyle(
                      size: 18.5,
                      weight: FontWeight.w700,
                      em: -0.01,
                    ),
                  ),
                  const SizedBox(height: 12),
                  for (int i = 0; i < rows.length; i++) ...<Widget>[
                    DiagnosisMiniRow(
                      entry: rows[i],
                      style: GlassStyle.softFlat,
                      padding: const EdgeInsets.all(14),
                      onTap: () => AppNav.push(
                        context,
                        (_) => ResultScreen(
                          diagnosisCase: DemoData.caseByKey(rows[i].caseKey),
                        ),
                      ),
                    ),
                    if (i != rows.length - 1) const SizedBox(height: 10),
                  ],
                  const SizedBox(height: 22),
                  PrimarySolidButton(
                    label: 'Chẩn đoán cho lô này',
                    onPressed: () => AppNav.push(
                      context,
                      (_) => CaptureScreen(initialPlotId: plot.id),
                    ),
                  ),
                  const SizedBox(height: 10),
                  GlassPillButton(
                    label: 'Xoá lô đất',
                    onPressed: () {},
                    minHeight: 48,
                    fontSize: 14.5,
                    fontWeight: FontWeight.w700,
                    color: AgriColors.accentInkDeep,
                    gradient: agriDangerGradient,
                    border: Border.all(color: AgriColors.accentA(.55)),
                    style: GlassStyle.control,
                  ),
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
            const Positioned.fill(
              child: ImageSlot(placeholder: 'Ảnh lô đất'),
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
                    onPressed: () => AppNav.push(
                      context,
                      (_) => PlotFormScreen(plot: plot),
                    ),
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
