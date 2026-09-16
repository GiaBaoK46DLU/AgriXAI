import 'package:flutter/material.dart';

import '../../core/app_colors.dart';
import '../../core/app_glass.dart';
import '../../core/app_metrics.dart';
import '../../core/app_scope.dart';
import '../../core/app_typography.dart';
import '../../models/models.dart';
import '../../services/session.dart' as session;
import '../../widgets/agri_icons.dart';
import '../../widgets/inputs.dart';
import '../../widgets/rows.dart';
import 'disease_detail_screen.dart';

/// **10 Danh mục bệnh** — UC-M13. Tra cứu được khi chưa đăng nhập.
///
/// API: `GET /diseases` — public, không cần token.
class CatalogScreen extends StatefulWidget {
  const CatalogScreen({super.key});

  @override
  State<CatalogScreen> createState() => _CatalogScreenState();
}

class _CatalogScreenState extends State<CatalogScreen> {
  final TextEditingController _query = TextEditingController();
  late Future<List<Disease>> _future;

  @override
  void initState() {
    super.initState();
    _future = session.diseaseService.fetchAll();
  }

  @override
  void dispose() {
    _query.dispose();
    super.dispose();
  }

  List<Disease> _filter(List<Disease> all) {
    final String q = _query.text.trim().toLowerCase();
    if (q.isEmpty) return all;
    return all.where((Disease d) {
      return '${d.name} ${d.en} ${d.cue}'.toLowerCase().contains(q);
    }).toList();
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<List<Disease>>(
      future: _future,
      builder: (BuildContext context, AsyncSnapshot<List<Disease>> snapshot) {
        if (snapshot.connectionState != ConnectionState.done) {
          return const Center(child: CircularProgressIndicator());
        }
        if (snapshot.hasError) {
          return _errorState(() => setState(() {
                _future = session.diseaseService.fetchAll();
              }));
        }
        return _list(context, _filter(snapshot.data!));
      },
    );
  }

  Widget _errorState(VoidCallback onRetry) {
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
          const SizedBox(height: 60),
          Center(
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: <Widget>[
                  Text(
                    'Không tải được danh mục bệnh. Kiểm tra kết nối mạng.',
                    textAlign: TextAlign.center,
                    style: agriStyle(size: 14, color: AgriColors.inkA(.72)),
                  ),
                  const SizedBox(height: 12),
                  TextButton(onPressed: onRetry, child: const Text('Thử lại')),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _list(BuildContext context, List<Disease> rows) {
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
                (_) => DiseaseDetailScreen(
                  diseaseKey: rows[i].key,
                  disease: rows[i],
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
