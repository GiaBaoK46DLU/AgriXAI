import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_tts/flutter_tts.dart';

import '../../core/app_colors.dart';
import '../../core/app_glass.dart';
import '../../core/app_metrics.dart';
import '../../core/app_scope.dart';
import '../../core/app_typography.dart';
import '../../data/demo_data.dart';
import '../../models/models.dart';
import '../../widgets/agri_icons.dart';
import '../../widgets/agri_screen.dart';
import '../../widgets/buttons.dart';
import '../../widgets/chips.dart';
import '../../widgets/glass_card.dart';
import '../../widgets/image_slot.dart';
import '../../widgets/misc.dart';
import '../capture/capture_screen.dart';
import '../forum/forum_compose_screen.dart';
import 'treatment_screen.dart';

/// **05 Kết quả chẩn đoán** — UC-M8. Màn quan trọng nhất của đồ án: đây là
/// chỗ phần XAI hiện ra cho người dùng.
///
/// API khi nối thật: `POST /diagnoses` rồi `GET /diagnoses/{id}`. Nút gạt
/// "Vùng nghi ngờ / Ảnh gốc" chỉ đổi giữa `overlay_url` và `image_url`.
class ResultScreen extends StatefulWidget {
  const ResultScreen({required this.diagnosisCase, super.key});

  final DiagnosisCase diagnosisCase;

  @override
  State<ResultScreen> createState() => _ResultScreenState();
}

class _ResultScreenState extends State<ResultScreen> {
  bool _xai = true;
  bool _speaking = false;
  int _imagePage = 0;
  FlutterTts? _tts;

  DiagnosisCase get _case => widget.diagnosisCase;

  Disease get _disease => _case.disease;

  @override
  void dispose() {
    _tts?.stop();
    super.dispose();
  }

  Future<void> _toggleSpeak() async {
    if (_speaking) {
      await _tts?.stop();
      if (mounted) setState(() => _speaking = false);
      return;
    }

    final String text = '${_disease.name}. ${_case.explanation}'
        '${_case.urgent == null ? '' : ' ${_case.urgent}'}';

    try {
      final FlutterTts tts = _tts ??= FlutterTts();
      await tts.setLanguage('vi-VN');
      tts.setCompletionHandler(() {
        if (mounted) setState(() => _speaking = false);
      });
      tts.setCancelHandler(() {
        if (mounted) setState(() => _speaking = false);
      });
      tts.setErrorHandler((dynamic _) {
        if (mounted) setState(() => _speaking = false);
      });
      setState(() => _speaking = true);
      await tts.speak(text);
    } catch (_) {
      // Máy chưa cài giọng tiếng Việt thì chỉ trả nút về trạng thái ban đầu.
      if (mounted) setState(() => _speaking = false);
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
            // Nút "Chia sẻ kết quả" đã bỏ hẳn (từ #85 MB-16) — trước đây
            // `onPressed: () {}` không làm gì, để một nút chết trên màn còn
            // tệ hơn là không có nút.
            ScreenHeader(
              title: 'Kết quả chẩn đoán',
              onBack: () => Navigator.of(context).pop(),
            ),
            const SizedBox(height: 16),
            _imageFrame(),
            const SizedBox(height: 16),
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: <Widget>[
                      Text(
                        _disease.pathogen.toUpperCase(),
                        style: AgriTextStyles.kicker(AgriColors.oliveInk),
                      ),
                      const SizedBox(height: 5),
                      Text(
                        _disease.name,
                        style: agriStyle(
                          size: 26,
                          weight: FontWeight.w800,
                          em: -0.02,
                          height: 1.12,
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 11),
                SeverityChip(
                  severity: _case.severity,
                  fontSize: 13,
                  padding: const EdgeInsets.symmetric(
                    horizontal: 15,
                    vertical: 8,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            _top3Card(),
            const SizedBox(height: 14),
            _metricsCard(),
            const SizedBox(height: 14),
            _explainCard(),
            const SizedBox(height: 16),
            Wrap(
              spacing: 7,
              runSpacing: 7,
              children: <Widget>[
                MetaChip(label: _case.plot),
                MetaChip(label: _case.time),
                MetaChip(label: _case.modelBadge),
              ],
            ),
            const SizedBox(height: 14),
            Text(
              _case.disclaimer,
              style: agriStyle(
                size: 12,
                height: 1.55,
                color: AgriColors.inkA(.62),
              ),
            ),
            const SizedBox(height: 18),
            PrimaryPillButton(
              label: 'Xem gợi ý xử lý',
              icon: AgriIcons.arrowRight(22, AgriColors.primary),
              onPressed: () => AppNav.push(
                context,
                (_) => TreatmentScreen(diagnosisCase: _case),
              ),
            ),
            const SizedBox(height: 10),
            Row(
              children: <Widget>[
                Expanded(
                  child: GlassPillButton(
                    label: 'Thêm thảo luận',
                    onPressed: () => AppNav.push(
                      context,
                      (_) => ForumComposeScreen(
                        initialDiagnosisId: _case.id,
                        initialDiseaseKey: _case.diseaseKey,
                      ),
                    ),
                    minHeight: 48,
                    fontSize: 14.5,
                    style: GlassStyle.field,
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: GlassPillButton(
                    label: 'Chụp lại',
                    onPressed: () =>
                        AppNav.push(context, (_) => const CaptureScreen()),
                    minHeight: 48,
                    fontSize: 14.5,
                    style: GlassStyle.field,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  /// Khung ảnh 272px. Có `_case.images` (3–5 ảnh thật) thì lướt qua từng ảnh
  /// bằng `PageView`, mỗi ảnh gạt riêng được "Vùng nghi ngờ"/"Ảnh gốc"; dữ
  /// liệu mẫu cũ (`images` rỗng) rơi về hiện một ảnh duy nhất như trước.
  Widget _imageFrame() {
    final List<DiagnosisImageResult> images = _case.images;
    if (images.isEmpty) {
      return _singleImageFrame(
        overlayUrl: _case.overlayUrl,
        overlayFile: _case.overlayFile,
        imageUrl: _case.imageUrl,
        imageFile: _case.imageFile,
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: <Widget>[
        SizedBox(
          height: 272,
          child: PageView.builder(
            itemCount: images.length,
            onPageChanged: (int i) => setState(() => _imagePage = i),
            itemBuilder: (BuildContext context, int i) {
              final DiagnosisImageResult img = images[i];
              return Padding(
                padding: const EdgeInsets.symmetric(horizontal: 2),
                child: _singleImageFrame(
                  overlayUrl: img.overlayUrl,
                  overlayFile: img.overlayFile,
                  imageUrl: img.imageUrl,
                  imageFile: img.imageFile,
                  badge: '${i + 1}/${images.length} · ${img.diseaseName} '
                      '${img.confidence}',
                ),
              );
            },
          ),
        ),
        const SizedBox(height: 10),
        Center(
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: <Widget>[
              for (int i = 0; i < images.length; i++)
                Container(
                  margin: const EdgeInsets.symmetric(horizontal: 3),
                  width: i == _imagePage ? 18 : 6,
                  height: 6,
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(3),
                    color: i == _imagePage
                        ? AgriColors.primary
                        : AgriColors.inkSoftA(.24),
                  ),
                ),
            ],
          ),
        ),
      ],
    );
  }

  /// Một khung ảnh — gạt giữa `overlay` (elip khoanh vùng do backend vẽ sẵn)
  /// và ảnh gốc. Không có ảnh thật (dữ liệu mẫu) thì hiện placeholder; có
  /// overlay mới hiện được nút gạt. `badge` (nếu có) hiện ở góc trái thay vì
  /// chỗ nút gạt — dùng cho carousel đa ảnh để biết đang xem ảnh nào.
  Widget _singleImageFrame({
    required String? overlayUrl,
    required File? overlayFile,
    required String? imageUrl,
    required File? imageFile,
    String? badge,
  }) {
    final bool hasOverlay = overlayUrl != null || overlayFile != null;
    final bool showOverlay = _xai && hasOverlay;
    final File? shownFile = showOverlay ? overlayFile : imageFile;
    final String? shownUrl =
        shownFile != null ? null : (showOverlay ? overlayUrl : imageUrl);
    final bool zoomable = shownFile != null || shownUrl != null;

    return Container(
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
            Positioned.fill(
              child: GestureDetector(
                onTap: zoomable
                    ? () => AppNav.push(
                          context,
                          (_) => _FullScreenImageViewer(
                            file: shownFile,
                            url: shownUrl,
                          ),
                        )
                    : null,
                child: ImageSlot(
                  placeholder: 'Kéo ảnh lá bệnh vào đây',
                  onDark: true,
                  file: shownFile,
                  imageUrl: shownUrl,
                ),
              ),
            ),
            if (zoomable)
              const Positioned(
                right: 14,
                bottom: 14,
                child: GlassCard(
                  style: GlassStyle.overImage,
                  blurSigma: 26,
                  radius: 999,
                  padding: EdgeInsets.all(8),
                  child: Icon(
                    Icons.zoom_in,
                    size: 18,
                    color: AgriColors.ink,
                  ),
                ),
              ),
            if (badge != null)
              Positioned(
                left: 14,
                top: 14,
                child: GlassCard(
                  style: GlassStyle.overImage,
                  blurSigma: 26,
                  radius: 999,
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                  child: Text(
                    badge,
                    style: agriStyle(size: 11.5, weight: FontWeight.w700),
                  ),
                ),
              ),
            if (hasOverlay)
              Positioned(
                top: 14,
                right: 14,
                child: GlassCard(
                  style: GlassStyle.overImage,
                  blurSigma: 26,
                  radius: 999,
                  padding: const EdgeInsets.all(4),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: <Widget>[
                      _xaiToggle('Vùng nghi ngờ', _xai, () {
                        setState(() => _xai = true);
                      }),
                      const SizedBox(width: 4),
                      _xaiToggle('Ảnh gốc', !_xai, () {
                        setState(() => _xai = false);
                      }),
                    ],
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }

  Widget _xaiToggle(String label, bool active, VoidCallback onTap) {
    return Material(
      color: const Color(0x00000000),
      borderRadius: BorderRadius.circular(999),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(999),
        child: Ink(
          decoration: BoxDecoration(
            gradient: active ? agriPrimaryGradient : null,
            borderRadius: BorderRadius.circular(999),
          ),
          child: Container(
            constraints: const BoxConstraints(minHeight: 34),
            padding: const EdgeInsets.symmetric(horizontal: 14),
            alignment: Alignment.center,
            child: Text(
              label,
              style: agriStyle(
                size: 12,
                weight: FontWeight.w600,
                color: active ? const Color(0xFFFFFFFF) : AgriColors.ink,
              ),
            ),
          ),
        ),
      ),
    );
  }

  /// Tỉ lệ vùng nghi ngờ trên ảnh — "Độ tin cậy" đã nhường chỗ cho thẻ "Ba
  /// khả năng cao nhất" ở trên, tránh lặp lại cùng một con số hai lần.
  Widget _metricsCard() {
    return GlassCard(
      style: GlassStyle.card,
      radius: 28,
      padding: const EdgeInsets.all(18),
      shadows: AgriShadows.raised(.12),
      child: _metricRow(
        'Vùng nghi ngờ trên ảnh',
        _case.affected,
        color: AgriColors.accent,
      ),
    );
  }

  Widget _metricRow(
    String label,
    String value, {
    Gradient? gradient,
    Color? color,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: <Widget>[
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: <Widget>[
            Text(
              label,
              style: agriStyle(
                size: 13.5,
                weight: FontWeight.w600,
                color: AgriColors.inkA(.74),
              ),
            ),
            Text(
              value,
              style: agriStyle(size: 13.5, weight: FontWeight.w600),
            ),
          ],
        ),
        const SizedBox(height: 7),
        AgriProgressBar(
          value: DemoData.percentToFraction(value),
          gradient: gradient,
          color: color,
        ),
      ],
    );
  }

  /// Thẻ giải thích XAI — phần cốt lõi của đề tài.
  Widget _explainCard() {
    return GlassCard(
      radius: 28,
      blurSigma: 28,
      gradient: agriExplainGradient,
      border: Border.all(color: AgriColors.whiteA(.6)),
      padding: const EdgeInsets.all(18),
      shadows: <BoxShadow>[
        BoxShadow(
          color: AgriColors.shadowA(.14),
          offset: const Offset(0, 12),
          blurRadius: 28,
        ),
      ],
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          Row(
            children: <Widget>[
              AgriIcons.info(18),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  'VÌ SAO HỆ THỐNG KẾT LUẬN VẬY?',
                  style: AgriTextStyles.kicker(AgriColors.primary),
                ),
              ),
              const SizedBox(width: 8),
              _speakButton(),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            _case.explanation,
            style: agriStyle(size: 15, height: 1.58),
          ),
        ],
      ),
    );
  }

  Widget _speakButton() {
    return Material(
      color: const Color(0x00000000),
      borderRadius: BorderRadius.circular(999),
      child: InkWell(
        onTap: _toggleSpeak,
        borderRadius: BorderRadius.circular(999),
        child: Ink(
          decoration: BoxDecoration(
            color: _speaking ? null : AgriColors.whiteA(.55),
            gradient: _speaking ? agriPrimaryGradient : null,
            borderRadius: BorderRadius.circular(999),
            border: Border.all(color: AgriColors.primaryA(.34)),
          ),
          child: Container(
            constraints: const BoxConstraints(minHeight: 34),
            padding: const EdgeInsets.symmetric(horizontal: 13),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: <Widget>[
                if (_speaking)
                  AgriIcons.stopSquare(15, const Color(0xFFFFFFFF))
                else
                  AgriIcons.speaker(15, AgriColors.primary),
                const SizedBox(width: 6),
                Text(
                  _speaking ? 'Dừng đọc' : 'Nghe đọc',
                  style: agriStyle(
                    size: 12,
                    weight: FontWeight.w700,
                    color: _speaking
                        ? const Color(0xFFFFFFFF)
                        : AgriColors.primary,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _top3Card() {
    return GlassCard(
      radius: 26,
      blurSigma: 26,
      gradient: const GlassStyle(
        topOpacity: .8,
        bottomOpacity: .4,
        borderOpacity: .6,
      ).gradient,
      border: Border.all(color: AgriColors.whiteA(.6)),
      padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 16),
      shadows: <BoxShadow>[
        BoxShadow(
          color: AgriColors.shadowA(.12),
          offset: const Offset(0, 10),
          blurRadius: 24,
        ),
      ],
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          Text(
            'Ba khả năng cao nhất',
            style: agriStyle(
              size: 13,
              weight: FontWeight.w600,
              color: AgriColors.inkA(.74),
            ),
          ),
          const SizedBox(height: 11),
          for (int i = 0; i < _case.top3.length; i++) ...<Widget>[
            _top3Row(i),
            if (i != _case.top3.length - 1) const SizedBox(height: 10),
          ],
        ],
      ),
    );
  }

  Widget _top3Row(int index) {
    final (String name, String percent) = _case.top3[index];
    final bool first = index == 0;
    return Row(
      children: <Widget>[
        Expanded(
          child: Text(
            name,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: agriStyle(
              size: 14,
              weight: first ? FontWeight.w700 : FontWeight.w500,
              color: AgriColors.top3Ink,
            ),
          ),
        ),
        const SizedBox(width: 11),
        SizedBox(
          width: 86,
          child: AgriProgressBar(
            value: DemoData.percentToFraction(percent),
            height: 7,
            gradient: first ? agriProgressGradient : null,
            color: first ? null : AgriColors.inkSoftA(.18),
          ),
        ),
        const SizedBox(width: 11),
        SizedBox(
          width: 40,
          child: Text(
            percent,
            textAlign: TextAlign.right,
            style: agriStyle(size: 13, weight: FontWeight.w700),
          ),
        ),
      ],
    );
  }
}

/// Xem ảnh khoanh vùng/ảnh gốc toàn màn hình, phóng to được bằng
/// `InteractiveViewer` (kéo giãn hai ngón/double-tap) — trước đây ảnh chỉ
/// hiện cố định 272px, không xem chi tiết được vùng khoanh nhỏ.
class _FullScreenImageViewer extends StatelessWidget {
  const _FullScreenImageViewer({this.file, this.url});

  final File? file;
  final String? url;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF000000),
      appBar: AppBar(
        backgroundColor: const Color(0x00000000),
        elevation: 0,
        iconTheme: const IconThemeData(color: Color(0xFFFFFFFF)),
      ),
      body: Center(
        child: InteractiveViewer(
          minScale: 1,
          maxScale: 5,
          child: file != null
              ? Image.file(file!, fit: BoxFit.contain)
              : Image.network(url!, fit: BoxFit.contain),
        ),
      ),
    );
  }
}
