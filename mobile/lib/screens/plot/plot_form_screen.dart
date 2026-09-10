import 'package:flutter/material.dart';

import '../../core/app_colors.dart';
import '../../core/app_glass.dart';
import '../../core/app_metrics.dart';
import '../../core/app_scope.dart';
import '../../core/app_typography.dart';
import '../../models/models.dart';
import '../../services/api_client.dart';
import '../../services/session.dart' as session;
import '../../widgets/agri_screen.dart';
import '../../widgets/buttons.dart';
import '../../widgets/chips.dart';
import '../../widgets/glass_bottom_bar.dart';
import '../../widgets/glass_card.dart';
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

  bool _saving = false;
  String? _error;

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
      if (widget.plot == null) {
        final String puc = _puc.text.trim();
        await session.apiClient.postJson('/plots', <String, dynamic>{
          ...payload,
          if (puc.isNotEmpty) 'puc': puc,
        });
      } else {
        await session.apiClient.patchJson('/plots/${widget.plot!.id}', payload);
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
