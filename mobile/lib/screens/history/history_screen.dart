import 'package:flutter/material.dart';

import '../../core/app_colors.dart';
import '../../core/app_metrics.dart';
import '../../core/app_scope.dart';
import '../../core/app_typography.dart';
import '../../data/demo_data.dart';
import '../../models/models.dart';
import '../../widgets/chips.dart';
import '../../widgets/rows.dart';
import '../result/result_screen.dart';

/// **07 Lịch sử** — UC-M10.
///
/// API khi nối thật: `GET /diagnoses?severity=&plot_id=&page=`.
class HistoryScreen extends StatefulWidget {
  const HistoryScreen({super.key});

  @override
  State<HistoryScreen> createState() => _HistoryScreenState();
}

class _HistoryScreenState extends State<HistoryScreen> {
  /// `null` nghĩa là "Tất cả".
  Severity? _filter;

  static const List<(Severity?, String)> _chips = <(Severity?, String)>[
    (null, 'Tất cả'),
    (Severity.severe, 'Nặng'),
    (Severity.moderate, 'Trung bình'),
    (Severity.mild, 'Nhẹ'),
    (Severity.none, 'Khoẻ mạnh'),
  ];

  List<DiagnosisEntry> get _rows => _filter == null
      ? DemoData.history
      : DemoData.history
          .where((DiagnosisEntry h) => h.severity == _filter)
          .toList();

  String get _countLabel {
    final String suffix = _filter == null
        ? ''
        : ' ở mức ${DemoData.sev(_filter!).name.toLowerCase()}';
    return '${_rows.length} lần chẩn đoán$suffix';
  }

  @override
  Widget build(BuildContext context) {
    final List<DiagnosisEntry> rows = _rows;

    return SingleChildScrollView(
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
            _countLabel,
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
                    onPressed: () => setState(() => _filter = chip.$1),
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
          if (rows.isEmpty)
            Padding(
              padding: const EdgeInsets.symmetric(
                horizontal: 20,
                vertical: 46,
              ),
              child: Column(
                children: <Widget>[
                  Text(
                    'Không có kết quả',
                    style: agriStyle(size: 18, weight: FontWeight.w700),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    'Chưa có lần chẩn đoán nào ở mức độ này.',
                    textAlign: TextAlign.center,
                    style: agriStyle(size: 14, color: AgriColors.inkA(.68)),
                  ),
                ],
              ),
            )
          else
            for (int i = 0; i < rows.length; i++) ...<Widget>[
              DiagnosisCard(
                entry: rows[i],
                onTap: () => AppNav.push(
                  context,
                  (_) => ResultScreen(
                    diagnosisCase: DemoData.caseByKey(rows[i].caseKey),
                  ),
                ),
              ),
              if (i != rows.length - 1) const SizedBox(height: 10),
            ],
        ],
      ),
    );
  }
}
