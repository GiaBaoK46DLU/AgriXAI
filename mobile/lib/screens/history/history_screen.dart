import 'package:flutter/material.dart';

import '../../core/app_colors.dart';
import '../../core/app_metrics.dart';
import '../../core/app_scope.dart';
import '../../core/app_typography.dart';
import '../../data/demo_data.dart';
import '../../models/models.dart';
import '../../services/api_client.dart';
import '../../services/session.dart' as session;
import '../../widgets/buttons.dart';
import '../../widgets/chips.dart';
import '../../widgets/rows.dart';
import '../result/result_screen.dart';

/// **07 Lịch sử** — UC-M10. Nối `GET /diagnoses` thật — đăng nhập luôn bắt
/// buộc trước khi vào được app nên không cần màn "đăng nhập để lưu lịch sử"
/// riêng, mọi lần chẩn đoán của người dùng đã đăng nhập đều tự lưu ở backend.
class HistoryScreen extends StatefulWidget {
  const HistoryScreen({super.key});

  @override
  State<HistoryScreen> createState() => _HistoryScreenState();
}

class _HistoryScreenState extends State<HistoryScreen> {
  /// `null` nghĩa là "Tất cả".
  Severity? _filter;

  bool _loading = true;
  String? _error;
  List<DiagnosisEntry> _rows = <DiagnosisEntry>[];
  int _total = 0;

  /// Bản ghi đang gọi `GET /diagnoses/{id}` để mở màn kết quả — chặn double-tap.
  int? _openingId;

  static const List<(Severity?, String)> _chips = <(Severity?, String)>[
    (null, 'Tất cả'),
    (Severity.severe, 'Nặng'),
    (Severity.moderate, 'Trung bình'),
    (Severity.mild, 'Nhẹ'),
    (Severity.none, 'Khoẻ mạnh'),
  ];

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
      final ({List<DiagnosisEntry> items, int total}) page =
          await session.diagnosisService.list(pageSize: 50, severity: _filter);
      if (!mounted) return;
      setState(() {
        _rows = page.items;
        _total = page.total;
        _loading = false;
      });
    } on ApiException catch (e) {
      if (mounted) setState(() { _error = e.message; _loading = false; });
    } catch (_) {
      if (mounted) {
        setState(() {
          _error = 'Không tải được lịch sử — kiểm tra kết nối mạng rồi thử lại.';
          _loading = false;
        });
      }
    }
  }

  void _selectFilter(Severity? severity) {
    setState(() => _filter = severity);
    _load();
  }

  Future<void> _open(DiagnosisEntry entry) async {
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

  String get _countLabel {
    final String suffix = _filter == null
        ? ''
        : ' ở mức ${DemoData.sev(_filter!).name.toLowerCase()}';
    return '$_total lần chẩn đoán$suffix';
  }

  @override
  Widget build(BuildContext context) {
    return RefreshIndicator(
      onRefresh: _load,
      child: SingleChildScrollView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: EdgeInsets.fromLTRB(
          16,
          AgriMetrics.screenTop(context),
          16,
          22,
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: <Widget>[
            Text(
              'Lịch sử chẩn đoán',
              style: agriStyle(size: 23, weight: FontWeight.w700, em: -0.02),
            ),
            const SizedBox(height: 3),
            Text(
              _loading ? 'Đang tải…' : _countLabel,
              style: agriStyle(size: 13, color: AgriColors.inkA(.7)),
            ),
            const SizedBox(height: 16),
            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.only(bottom: 16),
              child: Row(
                children: <Widget>[
                  for (final (Severity?, String) chip in _chips) ...<Widget>[
                    SelectableChip(
                      label: chip.$2,
                      selected: _filter == chip.$1,
                      onPressed: () => _selectFilter(chip.$1),
                      minHeight: 44,
                      fontSize: 13,
                      horizontalPadding: 17,
                    ),
                    if (chip != _chips.last) const SizedBox(width: 8),
                  ],
                ],
              ),
            ),
            const SizedBox(height: 8),
            if (_loading)
              const Padding(
                padding: EdgeInsets.symmetric(vertical: 60),
                child: Center(child: CircularProgressIndicator()),
              )
            else if (_error != null)
              _errorState(_error!)
            else if (_rows.isEmpty)
              _emptyState()
            else
              for (int i = 0; i < _rows.length; i++) ...<Widget>[
                DiagnosisCard(
                  entry: _rows[i],
                  onTap: () => _open(_rows[i]),
                ),
                if (i != _rows.length - 1) const SizedBox(height: 10),
              ],
          ],
        ),
      ),
    );
  }

  Widget _emptyState() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 46),
      child: Column(
        children: <Widget>[
          Text(
            'Không có kết quả',
            style: agriStyle(size: 18, weight: FontWeight.w700),
          ),
          const SizedBox(height: 6),
          Text(
            _filter == null
                ? 'Chưa có lần chẩn đoán nào — chụp ảnh lá ở tab Chẩn đoán để bắt đầu.'
                : 'Chưa có lần chẩn đoán nào ở mức độ này.',
            textAlign: TextAlign.center,
            style: agriStyle(size: 14, color: AgriColors.inkA(.68)),
          ),
        ],
      ),
    );
  }

  Widget _errorState(String message) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 46),
      child: Column(
        children: <Widget>[
          Text(
            message,
            textAlign: TextAlign.center,
            style: agriStyle(size: 14, color: AgriColors.inkA(.72)),
          ),
          const SizedBox(height: 14),
          GlassPillButton(
            label: 'Thử lại',
            onPressed: _load,
            minHeight: 44,
            fontSize: 14,
          ),
        ],
      ),
    );
  }
}
