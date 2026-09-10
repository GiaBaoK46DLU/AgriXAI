import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:youtube_player_flutter/youtube_player_flutter.dart';

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
import '../../widgets/glass_bottom_bar.dart';
import '../../widgets/glass_card.dart';
import '../../widgets/misc.dart';
import '../../widgets/rows.dart';

Future<void> _openUrl(BuildContext context, String url) async {
  final Uri uri = Uri.parse(url);
  final bool opened = await launchUrl(uri, mode: LaunchMode.externalApplication);
  if (!opened && context.mounted) {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Không mở được liên kết này')),
    );
  }
}

/// **06 Gợi ý xử lý** — UC-M9. Bệnh + thuốc + video lấy nguyên từ
/// [DiagnosisCase.disease] — đã tải sẵn từ `GET /diseases/{key}` lúc chẩn
/// đoán, không gọi lại API ở màn này.
class TreatmentScreen extends StatelessWidget {
  const TreatmentScreen({required this.diagnosisCase, super.key});

  final DiagnosisCase diagnosisCase;

  @override
  Widget build(BuildContext context) {
    final Disease disease = diagnosisCase.disease;
    final SeverityStyle sev = DemoData.sev(diagnosisCase.severity);
    final List<ProductLink> products = disease.products;

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
              title: 'Gợi ý xử lý',
              onBack: () => Navigator.of(context).pop(),
            ),
            const SizedBox(height: 16),
            Text(
              disease.name,
              style: agriStyle(
                size: 25,
                weight: FontWeight.w800,
                em: -0.02,
                height: 1.12,
              ),
            ),
            const SizedBox(height: 10),
            Wrap(
              spacing: 7,
              runSpacing: 7,
              children: <Widget>[
                PillTag(
                  label: disease.pathogen,
                  background: AgriColors.oliveA(.14),
                  foreground: AgriColors.oliveInk,
                  border: Border.all(color: AgriColors.oliveA(.22)),
                ),
                PillTag(
                  label: 'Mức độ: ${sev.name}',
                  background: sev.bg,
                  foreground: sev.fg,
                  fontWeight: FontWeight.w700,
                ),
              ],
            ),
            const SizedBox(height: 20),
            if (diagnosisCase.urgent != null) ...<Widget>[
              _urgentCard(diagnosisCase.urgent!),
              const SizedBox(height: 22),
            ],
            Text(
              'Video hướng dẫn xử lý',
              style: AgriTextStyles.sectionTitle,
            ),
            const SizedBox(height: 12),
            _VideoBox(videoUrl: disease.videoUrl),
            const SizedBox(height: 26),
            Text('Cần làm ngay', style: AgriTextStyles.sectionTitle),
            const SizedBox(height: 12),
            for (int i = 0; i < disease.treatments.length; i++) ...<Widget>[
              TreatmentStep(index: i + 1, text: disease.treatments[i]),
              if (i != disease.treatments.length - 1)
                const SizedBox(height: 10),
            ],
            const SizedBox(height: 28),
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Expanded(
                  child: Text(
                    'Thuốc gợi ý',
                    style: AgriTextStyles.sectionTitle,
                  ),
                ),
                const SizedBox(width: 10),
                PillTag(
                  label: 'Có thể mua',
                  background: AgriColors.accentA(.16),
                  foreground: AgriColors.accentInk,
                  fontSize: 10.5,
                  fontWeight: FontWeight.w700,
                  padding: const EdgeInsets.symmetric(
                    horizontal: 10,
                    vertical: 5,
                  ),
                  border: Border.all(color: AgriColors.accentA(.3)),
                ),
              ],
            ),
            const SizedBox(height: 6),
            Text(
              'Nhấn vào một loại thuốc để mở trang sản phẩm của nhà phân phối.',
              style: agriStyle(
                size: 12.5,
                height: 1.5,
                color: AgriColors.inkA(.68),
              ),
            ),
            const SizedBox(height: 13),
            if (products.isNotEmpty) ...<Widget>[
              for (int i = 0; i < products.length; i++) ...<Widget>[
                ProductRow(
                  product: products[i],
                  onTap: products[i].productUrl == null
                      ? null
                      : () => _openUrl(context, products[i].productUrl!),
                ),
                if (i != products.length - 1) const SizedBox(height: 10),
              ],
              const SizedBox(height: 14),
              Text(
                'Luân phiên hoạt chất giữa các lần phun để tránh kháng thuốc. '
                'Đọc kỹ nhãn và thời gian cách ly trước khi dùng.',
                style: agriStyle(
                  size: 11.5,
                  height: 1.5,
                  color: AgriColors.inkA(.6),
                ),
              ),
              const SizedBox(height: 26),
            ] else ...<Widget>[
              _noProductsCard(disease.noProductText ?? ''),
              const SizedBox(height: 26),
            ],
            Text(
              'Phòng ngừa lâu dài',
              style: AgriTextStyles.sectionTitle,
            ),
            const SizedBox(height: 12),
            for (int i = 0; i < disease.prevention.length; i++) ...<Widget>[
              PreventionRow(text: disease.prevention[i]),
              if (i != disease.prevention.length - 1)
                const SizedBox(height: 11),
            ],
            const SizedBox(height: 24),
            PrimarySolidButton(
              label: 'Đã hiểu, về trang chủ',
              onPressed: () => AppNav.toTab(context, AgriTab.plots),
            ),
          ],
        ),
      ),
    );
  }

  Widget _urgentCard(String text) {
    return GlassCard(
      radius: 26,
      blurSigma: 26,
      color: AgriColors.accentA(.16),
      border: Border.all(color: AgriColors.accentA(.34)),
      padding: const EdgeInsets.all(16),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Padding(
            padding: const EdgeInsets.only(top: 1),
            child: AgriIcons.warning(
              21,
              triangle: AgriColors.accent,
              mark: AgriColors.inkOnAccent,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              text,
              style: agriStyle(
                size: 14,
                height: 1.5,
                color: AgriColors.inkSoftA(.86),
              ),
            ),
          ),
        ],
      ),
    );
  }

  /// Ba trường hợp thiết kế bắt phải xử lý đúng — đây là ca "không có thuốc":
  /// virus khảm và lá khoẻ. Không được hiện danh sách rỗng trơ.
  Widget _noProductsCard(String text) {
    return DashedRoundedBorder(
      radius: 24,
      color: AgriColors.whiteA(.94),
      child: GlassCard(
        style: GlassStyle.softFlat,
        radius: 24,
        border: const Border(),
        padding: const EdgeInsets.all(16),
        child: Text(
          text,
          style: agriStyle(
            size: 14,
            height: 1.55,
            color: AgriColors.inkSoftA(.78),
          ),
        ),
      ),
    );
  }
}

/// Khung video 16:9. `videoUrl` là `null` cho tới khi web admin gán video cho
/// bệnh đó. Khi tách được ID YouTube từ URL thì nhúng thẳng trình phát ngay
/// trong app (WebView IFrame Player API của `youtube_player_flutter`) — mở
/// và phát tại chỗ, không nhảy qua app YouTube ngoài. Trình phát tự hiện
/// đúng ảnh thumbnail của video trước khi nhấn play nên không cần tự tải
/// ảnh riêng. Chỉ khi URL không phải link YouTube hợp lệ mới rơi về ô nhấn
/// mở ngoài như cũ — vẫn không để nền trống.
class _VideoBox extends StatefulWidget {
  const _VideoBox({required this.videoUrl});

  final String? videoUrl;

  @override
  State<_VideoBox> createState() => _VideoBoxState();
}

class _VideoBoxState extends State<_VideoBox> {
  YoutubePlayerController? _controller;

  @override
  void initState() {
    super.initState();
    _initController();
  }

  @override
  void didUpdateWidget(covariant _VideoBox oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.videoUrl != widget.videoUrl) {
      _controller?.dispose();
      _controller = null;
      _initController();
    }
  }

  void _initController() {
    final String? url = widget.videoUrl;
    if (url == null) return;
    final String? videoId = YoutubePlayer.convertUrlToId(url);
    if (videoId == null) return;
    _controller = YoutubePlayerController(
      initialVideoId: videoId,
      flags: const YoutubePlayerFlags(autoPlay: false, mute: false),
    );
  }

  @override
  void dispose() {
    _controller?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final YoutubePlayerController? controller = _controller;
    if (controller != null) {
      return ClipRRect(
        borderRadius: BorderRadius.circular(24),
        child: YoutubePlayer(
          controller: controller,
          showVideoProgressIndicator: true,
          progressIndicatorColor: AgriColors.primary,
        ),
      );
    }

    final bool hasVideo = widget.videoUrl != null;
    return AspectRatio(
      aspectRatio: 16 / 9,
      child: GlassCard(
        style: GlassStyle.soft,
        radius: 24,
        onTap: hasVideo ? () => _openUrl(context, widget.videoUrl!) : null,
        child: Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: <Widget>[
              Container(
                width: 52,
                height: 52,
                decoration: BoxDecoration(
                  gradient: agriPrimaryGradient,
                  shape: BoxShape.circle,
                  boxShadow: AgriShadows.playButton(),
                ),
                alignment: Alignment.center,
                child: AgriIcons.play(22, const Color(0xFFFFFFFF)),
              ),
              const SizedBox(height: 10),
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 24),
                child: Text(
                  hasVideo
                      ? 'Nhấn để xem video hướng dẫn trên YouTube'
                      : 'Video hướng dẫn sẽ được cập nhật sớm',
                  textAlign: TextAlign.center,
                  style: agriStyle(
                    size: 13.5,
                    weight: FontWeight.w600,
                    color: AgriColors.inkA(.68),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
