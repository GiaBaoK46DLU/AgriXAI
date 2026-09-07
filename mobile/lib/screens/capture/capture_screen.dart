import 'dart:io';

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

import '../../core/app_colors.dart';
import '../../core/app_glass.dart';
import '../../core/app_metrics.dart';
import '../../core/app_scope.dart';
import '../../core/app_typography.dart';
import '../../services/session.dart' as session;
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
/// Chụp bằng `image_picker`; nén thật xảy ra ở [AnalyzingScreen] ngay trước
/// khi gửi (giữ ảnh gốc ở đây để còn xem lại/chụp lại được).
class CaptureScreen extends StatefulWidget {
  const CaptureScreen({super.key, this.initialPlotId});

  final int? initialPlotId;

  @override
  State<CaptureScreen> createState() => _CaptureScreenState();
}

class _CaptureScreenState extends State<CaptureScreen> {
  int? _plotId;
  File? _image;
  List<({int id, String name})> _plots = <({int id, String name})>[];
  bool _loadingPlots = true;

  @override
  void initState() {
    super.initState();
    _plotId = widget.initialPlotId;
    _loadPlots();
  }

  Future<void> _loadPlots() async {
    try {
      final dynamic body = await session.apiClient.get('/plots');
      final List<({int id, String name})> plots = (body as List<dynamic>)
          .map((dynamic p) => (
                id: p['id'] as int,
                name: p['name'] as String,
              ))
          .toList();
      if (!mounted) return;
      setState(() {
        _plots = plots;
        _plotId ??= plots.isNotEmpty ? plots.first.id : null;
        _loadingPlots = false;
      });
    } catch (_) {
      if (mounted) setState(() => _loadingPlots = false);
    }
  }

  Future<void> _pick(ImageSource source) async {
    final XFile? picked = await ImagePicker().pickImage(
      source: source,
      maxWidth: 1600,
      imageQuality: 90,
    );
    if (picked == null) return;
    setState(() => _image = File(picked.path));
  }

  void _analyze() {
    if (_image == null) return;
    final String? plotName = _plotId == null
        ? null
        : _plots
            .firstWhere(
              (({int id, String name}) p) => p.id == _plotId,
              orElse: () => (id: -1, name: ''),
            )
            .name;
    AppNav.replace(
      context,
      (_) => AnalyzingScreen(
        image: _image!,
        plotId: _plotId,
        plotName: plotName?.isEmpty ?? true ? null : plotName,
      ),
    );
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
            _Viewfinder(image: _image),
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
            if (_loadingPlots)
              const Padding(
                padding: EdgeInsets.only(bottom: 16),
                child: SizedBox(
                  height: 20,
                  width: 20,
                  child: CircularProgressIndicator(strokeWidth: 2),
                ),
              )
            else if (_plots.isEmpty)
              Padding(
                padding: const EdgeInsets.only(bottom: 16),
                child: Text(
                  'Chưa có lô đất nào — vẫn chẩn đoán được, chỉ là chưa gán vào lô nào.',
                  style: agriStyle(size: 12.5, color: AgriColors.inkA(.65)),
                ),
              )
            else
              SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                padding: const EdgeInsets.only(bottom: 16),
                child: Row(
                  children: <Widget>[
                    for (final ({int id, String name}) plot in _plots) ...<Widget>[
                      SelectableChip(
                        label: plot.name,
                        selected: _plotId == plot.id,
                        onPressed: () => setState(() => _plotId = plot.id),
                      ),
                      if (plot.id != _plots.last.id) const SizedBox(width: 8),
                    ],
                  ],
                ),
              ),
            const SizedBox(height: 8),
            if (_image != null) ...<Widget>[
              PrimaryPillButton(
                label: 'Phân tích ảnh này',
                icon: AgriIcons.arrowRight(22, AgriColors.primary),
                onPressed: _analyze,
              ),
              const SizedBox(height: 10),
            ],
            GlassPillButton(
              label: 'Chụp ảnh',
              onPressed: () => _pick(ImageSource.camera),
              icon: AgriIcons.camera(
                20,
                body: AgriColors.primary,
                lens: AgriColors.cream,
              ),
              minHeight: 52,
              fontSize: 15.5,
            ),
            const SizedBox(height: 10),
            GlassPillButton(
              label: 'Tải ảnh từ thư viện',
              onPressed: () => _pick(ImageSource.gallery),
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
  const _Viewfinder({this.image});

  final File? image;

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
            Positioned.fill(
              child: ImageSlot(
                placeholder: 'Chưa có ảnh — chụp hoặc chọn từ thư viện',
                onDark: true,
                file: image,
              ),
            ),
            if (image == null) ...<Widget>[
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
          ],
        ),
      ),
    );
  }
}
