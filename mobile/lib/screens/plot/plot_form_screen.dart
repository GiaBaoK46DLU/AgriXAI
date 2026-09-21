import 'dart:io';

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

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
import '../../widgets/chips.dart';
import '../../widgets/glass_bottom_bar.dart';
import '../../widgets/glass_card.dart';
import '../../widgets/image_slot.dart';
import '../../widgets/inputs.dart';
import '../../widgets/misc.dart';

/// **09 Thêm / sửa lô đất** — UC-M4, UC-M5.
///
/// `POST /plots` khi thêm mới, `PATCH /plots/{id}` khi sửa.
class PlotFormScreen extends StatefulWidget {
  const PlotFormScreen({super.key, this.plot});

  /// `null` là thêm mới.
  final Plot? plot;

  @override
  State<PlotFormScreen> createState() => _PlotFormScreenState();
}

class _PlotFormScreenState extends State<PlotFormScreen> {
  static const List<String> _statuses = <String>[
    'Đang canh tác',
    'Bỏ hoá',
    'Lưu trữ',
  ];

  late final TextEditingController _name =
      TextEditingController(text: widget.plot?.name);
  late final TextEditingController _puc =
      TextEditingController(text: widget.plot?.puc);
  late final TextEditingController _region =
      TextEditingController(text: widget.plot?.region);
  late final TextEditingController _area = TextEditingController(
    text: widget.plot?.areaM2 == null
        ? ''
        : widget.plot!.areaM2!.toStringAsFixed(0),
  );
  final TextEditingController _crop = TextEditingController(text: 'Cà chua');
  final TextEditingController _note = TextEditingController();

  late String _status = widget.plot?.status ?? 'Đang canh tác';

  /// Ảnh mới chọn nhưng chưa tải lên — `null` nghĩa là giữ nguyên ảnh cũ
  /// (nếu sửa) hoặc chưa gán ảnh nào (nếu thêm mới).
  File? _pickedImage;

  bool _saving = false;
  String? _error;

  Future<void> _pickImage(ImageSource source) async {
    final XFile? picked = await ImagePicker().pickImage(
      source: source,
      maxWidth: 1600,
      imageQuality: 90,
    );
    if (picked == null) return;
    setState(() => _pickedImage = File(picked.path));
  }

  @override
  void dispose() {
    _name.dispose();
    _puc.dispose();
    _region.dispose();
    _area.dispose();
    _crop.dispose();
    _note.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    final String name = _name.text.trim();
    if (name.isEmpty) {
      setState(() => _error = 'Nhập tên lô đất');
      return;
    }

    setState(() {
      _saving = true;
      _error = null;
    });

    final Map<String, dynamic> payload = <String, dynamic>{
      'name': name,
      'region': _region.text.trim().isEmpty ? null : _region.text.trim(),
      'area_m2': double.tryParse(_area.text.trim()),
      'status': plotStatusRawFromLabel(_status),
      'note': _note.text.trim().isEmpty ? null : _note.text.trim(),
    };

    try {
      int plotId;
      if (widget.plot == null) {
        final String puc = _puc.text.trim();
        final dynamic created = await session.apiClient.postJson('/plots', <String, dynamic>{
          ...payload,
          if (puc.isNotEmpty) 'puc': puc,
        });
        plotId = (created as Map<String, dynamic>)['id'] as int;
      } else {
        plotId = widget.plot!.id;
        await session.apiClient.patchJson('/plots/$plotId', payload);
      }

      final File? image = _pickedImage;
      if (image != null) {
        await session.apiClient.postMultipartFiles(
          '/plots/$plotId/image',
          fileField: 'file',
          files: <({List<int> bytes, String filename})>[
            (bytes: await image.readAsBytes(), filename: 'plot.jpg'),
          ],
        );
      }

      if (!mounted) return;
      AppNav.toTab(context, AgriTab.plots);
    } on ApiException catch (e) {
      if (mounted) setState(() { _error = e.message; _saving = false; });
    } catch (_) {
      if (mounted) {
        setState(() {
          _error = 'Không lưu được lô đất — kiểm tra kết nối mạng rồi thử lại.';
          _saving = false;
        });
      }
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
              title: widget.plot == null ? 'Thêm lô đất' : 'Sửa lô đất',
              onBack: () => Navigator.of(context).pop(),
            ),
            const SizedBox(height: 18),
            const FieldLabel('Ảnh lô đất'),
            ClipRRect(
              borderRadius: BorderRadius.circular(20),
              child: AspectRatio(
                aspectRatio: 16 / 9,
                child: ImageSlot(
                  placeholder: 'Chưa có ảnh lô đất',
                  file: _pickedImage,
                  imageUrl: _pickedImage == null ? widget.plot?.imageUrl : null,
                ),
              ),
            ),
            const SizedBox(height: 10),
            Row(
              children: <Widget>[
                Expanded(
                  child: GlassPillButton(
                    label: 'Chụp ảnh',
                    onPressed: () => _pickImage(ImageSource.camera),
                    icon: AgriIcons.camera(
                      18,
                      body: AgriColors.primary,
                      lens: AgriColors.cream,
                    ),
                    minHeight: 46,
                    fontSize: 13.5,
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: GlassPillButton(
                    label: 'Chọn từ thư viện',
                    onPressed: () => _pickImage(ImageSource.gallery),
                    icon: AgriIcons.upload(18, AgriColors.primary),
                    minHeight: 46,
                    fontSize: 13.5,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 18),
            GlassCard(
              style: GlassStyle.card,
              radius: 28,
              padding: const EdgeInsets.all(18),
              shadows: AgriShadows.raised(),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: <Widget>[
                  const FieldLabel('Tên lô đất'),
                  GlassField(
                    controller: _name,
                    hintText: 'Ví dụ: Vườn nhà trên',
                  ),
                  const SizedBox(height: 15),
                  const FieldLabel('Mã vùng trồng (PUC)'),
                  GlassField(
                    controller: _puc,
                    hintText: 'Để trống — hệ thống tự sinh',
                  ),
                  Padding(
                    padding: const EdgeInsets.only(top: 7, left: 6),
                    child: Text(
                      'Định dạng PUC-YYMM-XXXX.',
                      style: agriStyle(size: 12, color: AgriColors.inkA(.6)),
                    ),
                  ),
                  const SizedBox(height: 15),
                  const FieldLabel('Khu vực'),
                  GlassField(
                    controller: _region,
                    hintText: 'Xã / phường, tỉnh',
                  ),
                  const SizedBox(height: 15),
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: <Widget>[
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.stretch,
                          children: <Widget>[
                            const FieldLabel('Diện tích (m²)'),
                            GlassField(
                              controller: _area,
                              hintText: '1200',
                              keyboardType: TextInputType.number,
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(width: 11),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.stretch,
                          children: <Widget>[
                            const FieldLabel('Cây trồng'),
                            GlassField(controller: _crop),
                          ],
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 15),
                  const FieldLabel('Trạng thái', bottomGap: 8),
                  Row(
                    children: <Widget>[
                      for (final String status in _statuses) ...<Widget>[
                        SelectableChip(
                          label: status,
                          selected: _status == status,
                          onPressed: () => setState(() => _status = status),
                          expand: true,
                          horizontalPadding: 6,
                        ),
                        if (status != _statuses.last) const SizedBox(width: 7),
                      ],
                    ],
                  ),
                  const SizedBox(height: 15),
                  const FieldLabel('Ghi chú'),
                  GlassTextArea(
                    controller: _note,
                    hintText: 'Giống, ngày xuống giống, đặc điểm cần lưu ý…',
                  ),
                ],
              ),
            ),
            if (_error != null) ...<Widget>[
              const SizedBox(height: 14),
              Text(
                _error!,
                style: agriStyle(size: 12.5, weight: FontWeight.w600, color: AgriColors.accentInk),
              ),
            ],
            const SizedBox(height: 20),
            PrimarySolidButton(
              label: _saving ? 'Đang lưu…' : 'Lưu lô đất',
              onPressed: _saving ? () {} : _save,
            ),
            const SizedBox(height: 10),
            GlassPillButton(
              label: 'Huỷ',
              onPressed: () => Navigator.of(context).pop(),
              minHeight: 48,
              fontSize: 15,
              style: GlassStyle.field,
            ),
          ],
        ),
      ),
    );
  }
}
