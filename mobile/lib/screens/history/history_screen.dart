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
import '../../widgets/inputs.dart';
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
  static const int _pageSize = 10;

  /// `null` nghĩa là "Tất cả".
  Severity? _severity;

  /// `null` nghĩa là "Tất cả lô đất".
  int? _plotId;

  bool _loading = true;
  String? _error;
  List<DiagnosisEntry> _rows = <DiagnosisEntry>[];
  List<Plot> _plots = <Plot>[];
  int _total = 0;
  int _page = 1;

  /// Bản ghi đang gọi `GET /diagnoses/{id}` để mở màn kết quả — chặn double-tap.
  int? _openingId;

  static const List<(Severity?, String)> _chips = <(Severity?, String)>[
    (null, 'Tất cả'),
    (Severity.severe, 'Nặng'),
    (Severity.moderate, 'Trung bình'),
    (Severity.mild, 'Nhẹ'),
    (Severity.none, 'Khoẻ mạnh'),
  ];

  int get _totalPages => _total == 0 ? 1 : ((_total + _pageSize - 1) ~/ _pageSize);

  @override
  void initState() {
    super.initState();
    _load(page: 1);
  }

  Future<void> _load({int? page}) async {
    final int targetPage = page ?? _page;
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final List<Plot> plots = _plots.isEmpty ? await _fetchPlots() : _plots;
      final ({List<DiagnosisEntry> items, int total}) result =
          await session.diagnosisService.list(
        page: targetPage,
        pageSize: _pageSize,
        severity: _severity,
        plotId: _plotId,
      );
      if (!mounted) return;
      setState(() {
        _plots = plots;
        _rows = result.items;
        _total = result.total;
        _page = targetPage;
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

  Future<List<Plot>> _fetchPlots() async {
    final List<dynamic> body =
        await session.apiClient.get('/plots') as List<dynamic>;
    return body.map((dynamic p) => Plot.fromJson(p as Map<String, dynamic>)).toList();
  }

  void _selectSeverity(Severity? severity) {
    setState(() => _severity = severity);
    _load(page: 1);
  }

  void _selectPlot(int? plotId) {
    setState(() => _plotId = plotId);
    _load(page: 1);
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
    final String suffix = _severity == null
        ? ''
        : ' ở mức ${DemoData.sev(_severity!).name.toLowerCase()}';
    return '$_total lần chẩn đoán$suffix';
  }

  String get _plotLabel => _plotId == null
      ? 'Tất cả lô đất'
      : _plots
          .firstWhere((Plot p) => p.id == _plotId, orElse: () => _plots.first)
          .name;

  @override
  Widget build(BuildContext context) {
    return RefreshIndicator(
      onRefresh: () => _load(page: 1),
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
            GlassDropdownField<int?>(
              label: _plotLabel,
              value: _plotId,
              sheetTitle: 'Lọc theo lô đất',
              options: <int?>[null, ..._plots.map((Plot p) => p.id)],
              optionLabel: (int? id) => id == null
                  ? 'Tất cả lô đất'
                  : _plots.firstWhere((Plot p) => p.id == id).name,
              onChanged: _selectPlot,
            ),
            const SizedBox(height: 10),
            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.only(bottom: 16),
              child: Row(
                children: <Widget>[
                  for (final (Severity?, String) chip in _chips) ...<Widget>[
                    SelectableChip(
                      label: chip.$2,
                      selected: _severity == chip.$1,
                      onPressed: () => _selectSeverity(chip.$1),
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
            else ...<Widget>[
              for (int i = 0; i < _rows.length; i++) ...<Widget>[
                DiagnosisCard(
                  entry: _rows[i],
                  onTap: () => _open(_rows[i]),
                ),
                if (i != _rows.length - 1) const SizedBox(height: 10),
              ],
              const SizedBox(height: 16),
              _PaginationBar(
                page: _page,
                totalPages: _totalPages,
                total: _total,
                onPrev: _page > 1 ? () => _load(page: _page - 1) : null,
                onNext: _page < _totalPages ? () => _load(page: _page + 1) : null,
              ),
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
            _severity == null && _plotId == null
                ? 'Chưa có lần chẩn đoán nào — chụp ảnh lá ở tab Chẩn đoán để bắt đầu.'
                : 'Chưa có lần chẩn đoán nào khớp bộ lọc này.',
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
            onPressed: () => _load(page: 1),
            minHeight: 44,
            fontSize: 14,
          ),
        ],
      ),
    );
  }
}

/// Cùng hình dạng với `_PaginationBar` của `forum_screen.dart` — không tách
/// chung ra `widgets/` vì mỗi màn tự quản lý widget hiển thị danh sách riêng
/// của mình (xem `_ThumbnailStrip` ở `capture_screen.dart` cho quy ước
/// tương tự trong dự án).
class _PaginationBar extends StatelessWidget {
  const _PaginationBar({
    required this.page,
    required this.totalPages,
    required this.total,
    required this.onPrev,
    required this.onNext,
  });

  final int page;
  final int totalPages;
  final int total;
  final VoidCallback? onPrev;
  final VoidCallback? onNext;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: <Widget>[
        _PageButton(label: '← Trước', onTap: onPrev),
        const SizedBox(width: 12),
        Text(
          'Trang $page / $totalPages  ($total kết quả)',
          style: agriStyle(size: 12.5, color: AgriColors.inkA(.65), weight: FontWeight.w600),
        ),
        const SizedBox(width: 12),
        _PageButton(label: 'Tiếp →', onTap: onNext),
      ],
    );
  }
}

class _PageButton extends StatelessWidget {
  const _PageButton({required this.label, required this.onTap});

  final String label;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final bool enabled = onTap != null;
    return Material(
      color: const Color(0x00000000),
      borderRadius: BorderRadius.circular(999),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(999),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
          child: Text(
            label,
            style: agriStyle(
              size: 12.5,
              weight: FontWeight.w700,
              color: enabled ? AgriColors.primary : AgriColors.inkA(.3),
            ),
          ),
        ),
      ),
    );
  }
}
