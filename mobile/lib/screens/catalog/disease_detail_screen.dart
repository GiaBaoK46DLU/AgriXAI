import 'package:flutter/material.dart';

import '../../core/app_colors.dart';
import '../../core/app_metrics.dart';
import '../../core/app_scope.dart';
import '../../core/app_typography.dart';
import '../../data/demo_data.dart';
import '../../models/models.dart';
import '../../services/session.dart' as session;
import '../../widgets/agri_screen.dart';
import '../../widgets/buttons.dart';
import '../../widgets/chips.dart';
import '../../widgets/glass_card.dart';
import '../../widgets/misc.dart';
import '../../widgets/rows.dart';
import '../capture/capture_screen.dart';

/// **11 Chi tiết bệnh** — UC-M13.
///
/// API: `GET /diseases/{key}`. Nếu đã có sẵn [disease] (đến từ màn danh mục)
/// thì dùng luôn, không gọi lại API.
class DiseaseDetailScreen extends StatefulWidget {
  const DiseaseDetailScreen({required this.diseaseKey, this.disease, super.key});

  final String diseaseKey;
  final Disease? disease;

  @override
  State<DiseaseDetailScreen> createState() => _DiseaseDetailScreenState();
}

class _DiseaseDetailScreenState extends State<DiseaseDetailScreen> {
  late Future<Disease> _future;

  @override
  void initState() {
    super.initState();
    _future = widget.disease != null
        ? Future<Disease>.value(widget.disease)
        : session.diseaseService.fetchOne(widget.diseaseKey);
  }

  @override
  Widget build(BuildContext context) {
    return AgriScreen(
      child: FutureBuilder<Disease>(
        future: _future,
        builder: (BuildContext context, AsyncSnapshot<Disease> snapshot) {
          if (snapshot.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) {
            return Center(
              child: Text(
                'Không tải được thông tin bệnh.',
                style: agriStyle(size: 14, color: AgriColors.inkA(.72)),
              ),
            );
          }
          return _body(context, snapshot.data!);
        },
      ),
    );
  }

  Widget _body(BuildContext context, Disease disease) {
    final PathogenTypeStyle tag = DemoData.tag(disease.type);

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
            ScreenHeader(
              title: 'Chi tiết bệnh',
              onBack: () => Navigator.of(context).pop(),
              fontSize: 19,
            ),
            const SizedBox(height: 18),
            Text(
              disease.name,
              style: agriStyle(
                size: 26,
                weight: FontWeight.w800,
                em: -0.02,
                height: 1.12,
              ),
            ),
            const SizedBox(height: 5),
            Text(
              disease.en,
              style: agriStyle(size: 13.5, color: AgriColors.inkA(.68)),
            ),
            const SizedBox(height: 14),
            Align(
              alignment: Alignment.centerLeft,
              child: PillTag(
                label: disease.pathogen,
                background: tag.bg,
                foreground: tag.fg,
                border: Border.all(color: AgriColors.diseaseTagBorder),
              ),
            ),
            const SizedBox(height: 20),
            GlassCard(
              radius: 28,
              blurSigma: 28,
              color: AgriColors.primaryLightA(.16),
              border: Border.all(color: AgriColors.paleLime),
              padding: const EdgeInsets.all(18),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: <Widget>[
                  Text(
                    'NHẬN BIẾT NHANH',
                    style: AgriTextStyles.kicker(AgriColors.primary),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    disease.cue,
                    style: agriStyle(size: 15.5, height: 1.52),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 22),
            _heading('Triệu chứng'),
            const SizedBox(height: 8),
            _paragraph(disease.symptoms),
            const SizedBox(height: 20),
            _heading('Điều kiện phát sinh'),
            const SizedBox(height: 8),
            _paragraph(disease.conditions),
            const SizedBox(height: 22),
            _heading('Xử lý'),
            const SizedBox(height: 12),
            for (int i = 0; i < disease.treatments.length; i++) ...<Widget>[
              TreatmentStep(
                index: i + 1,
                text: disease.treatments[i],
                compact: true,
              ),
              if (i != disease.treatments.length - 1)
                const SizedBox(height: 10),
            ],
            const SizedBox(height: 22),
            _heading('Phòng ngừa'),
            const SizedBox(height: 12),
            for (int i = 0; i < disease.prevention.length; i++) ...<Widget>[
              PreventionRow(text: disease.prevention[i], compact: true),
              if (i != disease.prevention.length - 1)
                const SizedBox(height: 11),
            ],
            const SizedBox(height: 24),
            PrimarySolidButton(
              label: 'Chụp ảnh để so sánh',
              onPressed: () =>
                  AppNav.push(context, (_) => const CaptureScreen()),
            ),
          ],
        ),
      );
  }

  Widget _heading(String text) => Text(
        text,
        style: agriStyle(size: 18, weight: FontWeight.w700),
      );

  Widget _paragraph(String text) => Text(
        text,
        style: agriStyle(
          size: 14.5,
          height: 1.6,
          color: AgriColors.inkSoftA(.86),
        ),
      );
}
