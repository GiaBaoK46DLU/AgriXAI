import 'package:flutter/material.dart';

import '../../core/app_colors.dart';
import '../../core/app_glass.dart';
import '../../core/app_metrics.dart';
import '../../core/app_scope.dart';
import '../../core/app_typography.dart';
import '../../data/demo_data.dart';
import '../../models/models.dart';
import '../../widgets/agri_icons.dart';
import '../../widgets/inputs.dart';
import '../../widgets/rows.dart';
import 'disease_detail_screen.dart';

/// **10 Danh mục bệnh** — UC-M13. Tra cứu được khi chưa đăng nhập.
///
/// API khi nối thật: `GET /diseases` — public, không cần token.
class CatalogScreen extends StatefulWidget {
  const CatalogScreen({super.key});

  @override
  State<CatalogScreen> createState() => _CatalogScreenState();
}

class _CatalogScreenState extends State<CatalogScreen> {
  final TextEditingController _query = TextEditingController();

  @override
  void dispose() {
    _query.dispose();
    super.dispose();
  }

  List<Disease> get _rows {
    final String q = _query.text.trim().toLowerCase();
    if (q.isEmpty) return DemoData.diseases;
    return DemoData.diseases.where((Disease d) {
      return '${d.name} ${d.en} ${d.cue}'.toLowerCase().contains(q);
    }).toList();
  }

  @override
  Widget build(BuildContext context) {
    final List<Disease> rows = _rows;

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
            'Danh mục bệnh cây trồng',
            style: agriStyle(size: 23, weight: FontWeight.w700, em: -0.02),
          ),
          const SizedBox(height: 3),
          Text(
            '10 loại — tra cứu được khi chưa đăng nhập',
            style: agriStyle(size: 13, color: AgriColors.inkA(.7)),
          ),
          const SizedBox(height: 16),
          GlassField(
            controller: _query,
            hintText: 'Tìm theo tên bệnh hoặc dấu hiệu',
            fontSize: 15,
            style: const GlassStyle(
              topOpacity: .82,
              bottomOpacity: .40,
              borderOpacity: .62,
              blurSigma: 26,
            ),
            prefix: AgriIcons.search(19, AgriColors.inkA(.62)),
            onChanged: (_) => setState(() {}),
          ),
          const SizedBox(height: 18),
          for (int i = 0; i < rows.length; i++) ...<Widget>[
            DiseaseRow(
              disease: rows[i],
              onTap: () => AppNav.push(
                context,
                (_) => DiseaseDetailScreen(diseaseKey: rows[i].key),
              ),
            ),
            if (i != rows.length - 1) const SizedBox(height: 10),
          ],
        ],
      ),
    );
  }
}
