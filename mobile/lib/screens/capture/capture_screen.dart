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

const int _minImages = 3;
const int _maxImages = 5;

/// **03 Chụp ảnh** — UC-M7.
///
/// Cần 3–5 ảnh cùng một lá/vết bệnh — kết quả cuối cùng tổng hợp theo đa số
/// phiếu giữa các ảnh (xem CLAUDE.md). Nén thật xảy ra ở [AnalyzingScreen]
/// ngay trước khi gửi (giữ ảnh gốc ở đây để còn xem lại/bỏ bớt được).
class CaptureScreen extends StatefulWidget {
  const CaptureScreen({super.key, this.initialPlotId});

  final int? initialPlotId;

  @override
  State<CaptureScreen> createState() => _CaptureScreenState();
}

class _CaptureScreenState extends State<CaptureScreen> {
  int? _plotId;
  final List<File> _images = <File>[];
  int _viewerPage = 0;
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

  int get _remainingSlots => _maxImages - _images.length;

  Future<void> _pickFromCamera() async {
    if (_remainingSlots <= 0) return;
    final XFile? picked = await ImagePicker().pickImage(
      source: ImageSource.camera,
      maxWidth: 1600,
      imageQuality: 90,
    );
    if (picked == null) return;
    setState(() {
      _images.add(File(picked.path));
      _viewerPage = _images.length - 1;
    });
  }

  Future<void> _pickFromGallery() async {
    if (_remainingSlots <= 0) return;
    final List<XFile> picked = await ImagePicker().pickMultiImage(
      maxWidth: 1600,
      imageQuality: 90,
    );
    if (picked.isEmpty) return;
    setState(() {
      _images.addAll(
        picked.take(_remainingSlots).map((XFile x) => File(x.path)),
      );
      _viewerPage = _images.length - 1;
    });
  }

  void _removeAt(int index) {
    setState(() {
      _images.removeAt(index);
      if (_viewerPage >= _images.length) {
        _viewerPage = _images.isEmpty ? 0 : _images.length - 1;
      }
    });
  }

  void _analyze() {
    if (_images.length < _minImages) return;
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
        images: List<File>.of(_images),
        plotId: _plotId,
        plotName: plotName?.isEmpty ?? true ? null : plotName,
      ),
    );
  }

  String get _countHint {
    if (_images.isEmpty) return 'Chọn từ $_minImages đến $_maxImages ảnh cùng một lá/vết bệnh';
    if (_images.length < _minImages) {
      return 'Đã chọn ${_images.length}/$_maxImages ảnh — cần thêm ít nhất '
          '${_minImages - _images.length} ảnh nữa';
    }
    return 'Đã chọn ${_images.length}/$_maxImages ảnh';
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
            _Viewfinder(images: _images, page: _viewerPage),
            const SizedBox(height: 12),
            Text(
              _countHint,
              style: agriStyle(
                size: 12.5,
                weight: FontWeight.w600,
                color: _images.length >= _minImages
                    ? AgriColors.primary
                    : AgriColors.inkA(.68),
              ),
            ),
            if (_images.isNotEmpty) ...<Widget>[
              const SizedBox(height: 10),
              _ThumbnailStrip(
                images: _images,
                selected: _viewerPage,
                onSelect: (int i) => setState(() => _viewerPage = i),
                onRemove: _removeAt,
              ),
            ],
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
            if (_images.length >= _minImages) ...<Widget>[
              PrimaryPillButton(
                label: 'Phân tích ${_images.length} ảnh này',
                icon: AgriIcons.arrowRight(22, AgriColors.primary),
                onPressed: _analyze,
              ),
              const SizedBox(height: 10),
            ],
            GlassPillButton(
              label: _remainingSlots > 0 ? 'Chụp ảnh' : 'Đã đủ $_maxImages ảnh',
              onPressed: _pickFromCamera,
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
              label: _remainingSlots > 0 ? 'Tải ảnh từ thư viện' : 'Đã đủ $_maxImages ảnh',
              onPressed: _pickFromGallery,
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
///
/// Chưa chọn ảnh nào thì hiện placeholder như cũ; có ảnh thì lướt qua từng
/// ảnh bằng `PageView`, đồng bộ trang với [_ThumbnailStrip] bên dưới.
class _Viewfinder extends StatefulWidget {
  const _Viewfinder({required this.images, required this.page});

  final List<File> images;
  final int page;

  @override
  State<_Viewfinder> createState() => _ViewfinderState();
}

class _ViewfinderState extends State<_Viewfinder> {
  late final PageController _controller = PageController(initialPage: widget.page);

  @override
  void didUpdateWidget(_Viewfinder oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.page != widget.page && _controller.hasClients) {
      _controller.animateToPage(
        widget.page,
        duration: const Duration(milliseconds: 220),
        curve: Curves.easeOut,
      );
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

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
            if (widget.images.isEmpty)
              const Positioned.fill(
                child: ImageSlot(
                  placeholder: 'Chưa có ảnh — chụp hoặc chọn từ thư viện',
                  onDark: true,
                ),
              )
            else
              Positioned.fill(
                child: PageView.builder(
                  controller: _controller,
                  itemCount: widget.images.length,
                  itemBuilder: (BuildContext context, int i) => ImageSlot(
                    placeholder: '',
                    onDark: true,
                    file: widget.images[i],
                  ),
                ),
              ),
            if (widget.images.isEmpty) ...<Widget>[
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
            ] else
              Positioned(
                top: 14,
                right: 14,
                child: GlassCard(
                  style: GlassStyle.overImage,
                  radius: 999,
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                  child: Text(
                    '${widget.page + 1}/${widget.images.length}',
                    style: agriStyle(size: 12, weight: FontWeight.w700),
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

/// Dải thumbnail 64×64 bên dưới khung ngắm — chọn ảnh để xem lại, xoá bớt
/// bằng nút "x" ở góc, hoặc thêm ảnh nếu chưa đủ 5.
class _ThumbnailStrip extends StatelessWidget {
  const _ThumbnailStrip({
    required this.images,
    required this.selected,
    required this.onSelect,
    required this.onRemove,
  });

  final List<File> images;
  final int selected;
  final ValueChanged<int> onSelect;
  final ValueChanged<int> onRemove;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 64,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        itemCount: images.length,
        separatorBuilder: (_, __) => const SizedBox(width: 8),
        itemBuilder: (BuildContext context, int i) {
          final bool active = i == selected;
          return GestureDetector(
            onTap: () => onSelect(i),
            child: Stack(
              clipBehavior: Clip.none,
              children: <Widget>[
                Container(
                  width: 64,
                  height: 64,
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(
                      color: active ? AgriColors.primary : AgriColors.whiteA(.7),
                      width: active ? 2.5 : 1.5,
                    ),
                  ),
                  child: ClipRRect(
                    borderRadius: BorderRadius.circular(14),
                    child: Image.file(images[i], fit: BoxFit.cover),
                  ),
                ),
                Positioned(
                  top: -6,
                  right: -6,
                  child: GestureDetector(
                    onTap: () => onRemove(i),
                    child: Container(
                      width: 22,
                      height: 22,
                      decoration: const BoxDecoration(
                        color: Color(0xFFE0442C),
                        shape: BoxShape.circle,
                      ),
                      alignment: Alignment.center,
                      child: const Icon(Icons.close, size: 14, color: Color(0xFFFFFFFF)),
                    ),
                  ),
                ),
              ],
            ),
          );
        },
      ),
    );
  }
}
