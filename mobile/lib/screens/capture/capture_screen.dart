import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart' show PlatformException;
import 'package:image_picker/image_picker.dart';
import 'package:permission_handler/permission_handler.dart' show openAppSettings;

import '../../core/app_colors.dart';
import '../../core/app_glass.dart';
import '../../core/app_metrics.dart';
import '../../core/app_scope.dart';
import '../../core/app_typography.dart';
import '../../widgets/agri_icons.dart';
import '../../widgets/agri_screen.dart';
import '../../widgets/buttons.dart';
import '../../widgets/chips.dart';
import '../../widgets/glass_card.dart';
import '../../widgets/image_slot.dart';
import '../../widgets/inputs.dart';
import '../../widgets/misc.dart';
import 'analyzing_screen.dart';

const int _minImages = 3;
const int _maxImages = 5;
const int _maxNoteLength = 500;

/// **03 Chụp ảnh** — UC-M7.
///
/// Cần 3–5 ảnh cùng một lá/vết bệnh — kết quả cuối cùng tổng hợp theo đa số
/// phiếu giữa các ảnh (xem CLAUDE.md). Nén thật xảy ra ở [AnalyzingScreen]
/// ngay trước khi gửi (giữ ảnh gốc ở đây để còn xem lại/bỏ bớt được).
///
/// Lô đất (nếu có) luôn đến từ màn *Chi tiết lô đất* qua [initialPlotId] —
/// không còn cho chọn lô ngay ở đây. Vào từ nút chụp ảnh chung (không có lô
/// đất) thì kết quả chỉ hiện tạm thời, KHÔNG được backend lưu lại (xem
/// CLAUDE.md mục quản lý lô đất).
class CaptureScreen extends StatefulWidget {
  const CaptureScreen({super.key, this.initialPlotId, this.initialPlotName});

  final int? initialPlotId;
  final String? initialPlotName;

  @override
  State<CaptureScreen> createState() => _CaptureScreenState();
}

class _CaptureScreenState extends State<CaptureScreen> {
  final List<File> _images = <File>[];
  final TextEditingController _note = TextEditingController();
  int _viewerPage = 0;

  bool get _hasPlot => widget.initialPlotId != null;

  int get _remainingSlots => _maxImages - _images.length;

  @override
  void dispose() {
    _note.dispose();
    super.dispose();
  }

  Future<void> _pickFromCamera() async {
    if (_remainingSlots <= 0) return;
    try {
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
    } on PlatformException catch (e) {
      // `image_picker` gộp chung mọi nền tảng thành mã lỗi này khi người
      // dùng từ chối quyền Máy ảnh — không tự mở lại được hộp thoại xin
      // quyền lần hai (cả Android lẫn iOS đều chặn xin lại sau khi từ chối),
      // nên chỉ còn cách hướng dẫn người dùng tự vào Cài đặt.
      if (e.code == 'camera_access_denied' && mounted) {
        await _showCameraPermissionDeniedDialog();
      } else if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Không mở được máy ảnh, thử lại nhé')),
        );
      }
    }
  }

  Future<void> _showCameraPermissionDeniedDialog() {
    return showDialog<void>(
      context: context,
      builder: (BuildContext context) => AlertDialog(
        title: const Text('Cần quyền truy cập máy ảnh'),
        content: const Text(
          'AgriXAI cần quyền Máy ảnh để chụp ảnh lá bệnh. Mở Cài đặt > Ứng '
          'dụng > AgriXAI > Quyền rồi bật lại quyền Máy ảnh.',
        ),
        actions: <Widget>[
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Để sau'),
          ),
          TextButton(
            onPressed: () {
              Navigator.of(context).pop();
              openAppSettings();
            },
            child: const Text('Mở Cài đặt'),
          ),
        ],
      ),
    );
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
    final String note = _note.text.trim();
    AppNav.replace(
      context,
      (_) => AnalyzingScreen(
        images: List<File>.of(_images),
        plotId: widget.initialPlotId,
        plotName: widget.initialPlotName,
        save: _hasPlot,
        note: note.isEmpty ? null : note,
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
            Text('Ghi chú (không bắt buộc)', style: AgriTextStyles.fieldLabel),
            const SizedBox(height: 6),
            GlassTextArea(
              controller: _note,
              hintText: 'Ví dụ: cây trồng gần 3 tuần, mới tưới đẫm hôm qua…',
              minLines: 2,
              maxLength: _maxNoteLength,
              onChanged: (_) => setState(() {}),
            ),
            const SizedBox(height: 4),
            Align(
              alignment: Alignment.centerRight,
              child: Text(
                '${_note.text.length}/$_maxNoteLength',
                style: agriStyle(size: 11.5, color: AgriColors.inkA(.55)),
              ),
            ),
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
              decoration: BoxDecoration(
                color: _hasPlot
                    ? AgriColors.primaryLightA(.14)
                    : AgriColors.inkSoftA(.08),
                borderRadius: BorderRadius.circular(16),
              ),
              child: Text(
                _hasPlot
                    ? 'Kết quả sẽ được gắn vào lô "${widget.initialPlotName}" và lưu vào lịch sử.'
                    : 'Chẩn đoán nhanh — kết quả sẽ KHÔNG được lưu vào lịch sử vì chưa gắn với '
                        'lô đất nào. Vào từ màn chi tiết lô đất để lưu lại kết quả.',
                style: agriStyle(
                  size: 12.5,
                  weight: FontWeight.w600,
                  color: AgriColors.inkA(.78),
                ),
              ),
            ),
            const SizedBox(height: 16),
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
