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
import '../../widgets/chips.dart';
import '../../widgets/glass_card.dart';
import '../../widgets/image_slot.dart';
import '../../widgets/misc.dart';
import 'analyzing_screen.dart';

/// **03 Chụp ảnh** — UC-M7.
///
/// Khi nối thật: chụp bằng `image_picker`, nén bằng `flutter_image_compress`
/// trước khi gửi (backend giới hạn 10 MB mỗi ảnh).
class CaptureScreen extends StatefulWidget {
  const CaptureScreen({super.key, this.initialPlotId = 1});

  final int initialPlotId;

  @override
  State<CaptureScreen> createState() => _CaptureScreenState();
}

class _CaptureScreenState extends State<CaptureScreen> {
  late int _plotId = widget.initialPlotId;

  void _analyze() {
    AppNav.replace(context, (_) => const AnalyzingScreen());
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
              title: 'Chụp ảnh chẩn đoán',
              onBack: () => Navigator.of(context).pop(),
            ),
            const SizedBox(height: 16),
            const _Viewfinder(),
            const SizedBox(height: 16),
            const Wrap(
              spacing: 7,
              runSpacing: 7,
              children: <Widget>[
                HintChip(label: 'Chụp gần 20–30 cm'),
                HintChip(label: 'Đủ sáng, không ngược nắng'),
                HintChip(label: 'Lấy nét vào vết bệnh'),
              ],
            ),
            const SizedBox(height: 20),
            Text(
              'Gán vào lô đất',
              style: agriStyle(
                size: 13,
                weight: FontWeight.w600,
                color: AgriColors.inkA(.74),
              ),
            ),
            const SizedBox(height: 10),
            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.only(bottom: 16),
              child: Row(
                children: <Widget>[
                  for (final Plot plot in DemoData.plots) ...<Widget>[
                    SelectableChip(
                      label: plot.name,
                      selected: _plotId == plot.id,
                      onPressed: () => setState(() => _plotId = plot.id),
                    ),
                    if (plot != DemoData.plots.last) const SizedBox(width: 8),
                  ],
                ],
              ),
            ),
            const SizedBox(height: 8),
            PrimaryPillButton(
              label: 'Chụp ảnh',
              icon: AgriIcons.camera(
                24,
                body: AgriColors.primary,
                lens: AgriColors.cream,
              ),
              onPressed: _analyze,
            ),
            const SizedBox(height: 10),
            GlassPillButton(
              label: 'Tải ảnh từ thư viện',
              onPressed: _analyze,
              icon: AgriIcons.upload(20, AgriColors.primary),
              minHeight: 52,
              fontSize: 15.5,
            ),
            const SizedBox(height: 15),
            Text(
              'Ảnh được nén trước khi gửi để tiết kiệm dữ liệu — giới hạn 10 MB '
              'mỗi ảnh.',
              style: agriStyle(
                size: 12,
                height: 1.5,
                color: AgriColors.inkA(.62),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// Khung ngắm cao 312, nền `#081711`, bốn góc chữ L trắng.
class _Viewfinder extends StatelessWidget {
  const _Viewfinder();

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 312,
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
                placeholder: 'Kéo ảnh lá cà chua vào đây',
                onDark: true,
              ),
            ),
            const Positioned.fill(child: ViewfinderCorners()),
            Positioned(
              left: 0,
              right: 0,
              bottom: 16,
              child: Center(
                child: GlassCard(
                  style: GlassStyle.overImage,
                  radius: 999,
                  padding: const EdgeInsets.symmetric(
                    horizontal: 16,
                    vertical: 8,
                  ),
                  child: Text(
                    'Đưa một lá vào giữa khung',
                    style: agriStyle(size: 12.5, weight: FontWeight.w600),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
