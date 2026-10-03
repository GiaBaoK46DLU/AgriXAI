import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

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
import '../../widgets/inline_youtube_player.dart';
import '../../widgets/misc.dart';
import '../../widgets/rows.dart';
import '../forum/forum_compose_screen.dart';

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
            Row(
              children: <Widget>[
                Expanded(
                  child: Text(
                    'Video hướng dẫn xử lý',
                    style: AgriTextStyles.sectionTitle,
                  ),
                ),
                if (disease.videoUrl != null)
                  GhostButton(
                    label: 'Mở trên YouTube',
                    onPressed: () => _openUrl(context, disease.videoUrl!),
                    fontSize: 12.5,
                    minHeight: 28,
                    padding: const EdgeInsets.symmetric(horizontal: 4),
                  ),
              ],
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
            if (disease.referenceUrl != null) ...<Widget>[
              const SizedBox(height: 18),
              GestureDetector(
                onTap: () => _openUrl(context, disease.referenceUrl!),
                child: Row(
                  children: <Widget>[
                    AgriIcons.info(15),
                    const SizedBox(width: 7),
                    Expanded(
                      child: Text(
                        'Xem nguồn tham khảo',
                        style: agriStyle(
                          size: 13,
                          weight: FontWeight.w600,
                          color: AgriColors.primary,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],
            if (diagnosisCase.disclaimer.isNotEmpty) ...<Widget>[
              const SizedBox(height: 14),
              Text(
                diagnosisCase.disclaimer,
                style: agriStyle(
                  size: 12,
                  height: 1.55,
                  color: AgriColors.inkA(.62),
                ),
              ),
            ],
            const SizedBox(height: 24),
            GlassPillButton(
              label: 'Phản hồi về gợi ý xử lý này',
              onPressed: () => AppNav.push(
                context,
                (_) => ForumComposeScreen(
                  initialDiagnosisId: diagnosisCase.id,
                  initialDiseaseKey: diagnosisCase.diseaseKey,
                  initialKind: ForumPostKind.medicineIssue,
                ),
              ),
              minHeight: 50,
              fontSize: 14.5,
              style: GlassStyle.field,
            ),
            const SizedBox(height: 10),
            PrimarySolidButton(
              label: 'Đã hiểu, về trang chủ',
              onPressed: () => AppNav.toTab(context, AgriTab.plots),
            ),
          ],
        ),
      ),
    );
  }

  /// Cảnh báo "bệnh lan nhanh" cho các ca mức độ Nặng — cố ý dùng nền vàng
  /// cam ĐẶC (không phải bản tint nhạt như các thẻ khác trong màn này) kèm
  /// viền và bóng đổ đậm, để nổi bật rõ ràng thay vì chìm lẫn vào các thẻ
  /// thông tin trung tính xung quanh.
  Widget _urgentCard(String text) {
    return GlassCard(
      radius: 24,
      color: AgriColors.accent,
      border: Border.all(color: AgriColors.accentInkDeep, width: 1.5),
      padding: const EdgeInsets.all(16),
      shadows: AgriShadows.amberButton(),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Padding(
            padding: const EdgeInsets.only(top: 1),
            child: AgriIcons.warning(
              24,
              triangle: const Color(0xFFFFFFFF),
              mark: AgriColors.accent,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(
                  'CẢNH BÁO: BỆNH CÓ THỂ LAN NHANH',
                  style: agriStyle(
                    size: 11.5,
                    weight: FontWeight.w800,
                    em: 0.02,
                    color: AgriColors.accentInkDarkest,
                  ),
                ),
                const SizedBox(height: 5),
                Text(
                  text,
                  style: agriStyle(
                    size: 14.5,
                    weight: FontWeight.w700,
                    height: 1.5,
                    color: AgriColors.accentInkDarkest,
                  ),
                ),
              ],
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

/// Tách ID video từ URL YouTube — chỉ cần đủ để dựng link ảnh thumbnail và
/// nhận diện "đây có phải link YouTube hợp lệ không", không cần đầy đủ mọi
/// dạng URL YouTube từng tồn tại.
String? _youtubeVideoId(String url) {
  final Uri? uri = Uri.tryParse(url);
  if (uri == null) return null;
  final String host = uri.host.toLowerCase();

  if (host.contains('youtu.be')) {
    return uri.pathSegments.isNotEmpty ? uri.pathSegments.first : null;
  }
  if (host.contains('youtube.com')) {
    final String? v = uri.queryParameters['v'];
    if (v != null && v.isNotEmpty) return v;
    final List<String> segments = uri.pathSegments;
    for (final String marker in <String>['embed', 'shorts']) {
      final int i = segments.indexOf(marker);
      if (i != -1 && i + 1 < segments.length) return segments[i + 1];
    }
  }
  return null;
}

/// Khung video 16:9. `videoUrl` là `null` cho tới khi web admin gán video cho
/// bệnh đó.
///
/// ⚠️ Ngày 18/09/2026 từng bỏ hẳn nhúng WebView sau khi kiểm thử thật (dùng
/// `youtube_player_flutter`) bắt được crash gốc thật sự (`SIGTRAP` trong
/// `libwebviewchromium.so`, thread `NetworkService`, qua `adb logcat`) kèm
/// lỗi phải nhấn hai lần mới dừng video và có lúc tải mãi không phát được.
/// Cùng ngày, theo yêu cầu trực tiếp của Học, phục hồi phát tại chỗ nhưng đổi
/// gói: `youtube_player_iframe` thay vì `youtube_player_flutter`. Khác biệt
/// quan trọng — `youtube_player_iframe` dùng `webview_flutter` (gói chính chủ
/// Flutter team) và để nguyên khung điều khiển play/pause/seek của chính
/// YouTube chạy trong WebView, không vẽ thêm một lớp nút bấm Flutter đè lên
/// trên; `youtube_player_flutter` (gói cũ) vẽ nút play/pause bằng Flutter đè
/// lên WebView nên có hai lớp bắt cử chỉ tranh nhau, đó là gốc rễ lỗi "nhấn
/// hai lần". Xem CLAUDE.md mục video để biết đầy đủ rủi ro còn lại — bản
/// chất `SIGTRAP` là lỗi ở System WebView của máy/máy ảo, đổi gói Flutter
/// không đảm bảo hết được rủi ro tận gốc, chỉ giảm bớt so với gói cũ.
///
/// Chỉ dựng `InlineYoutubePlayer`/nạp WebView khi người dùng bấm play —
/// trước đó chỉ hiện ảnh thumbnail tĩnh (`Image.network` thường), để không
/// tốn tài nguyên WebView cho những lượt xem màn này mà không xem video.
///
/// ⚠️ 21/09/2026 mọi video báo "Video unavailable — Error code: 152" khi
/// phát trong app. Nguyên nhân thật (sửa 03/10/2026): YouTube bắt trình phát
/// nhúng phải có `Referer`/`origin` định danh nơi nhúng, còn
/// `youtube_player_iframe` cố định trang chứa ở origin `www.youtube.com` —
/// không phải userAgent hay cookie như phỏng đoán ban đầu. Nay phát bằng
/// `InlineYoutubePlayer` (tự nhúng iframe, origin `https://<applicationId>`).
/// Nút "Mở trên YouTube" cạnh tiêu đề mục vẫn giữ làm lối thoát thủ công.
class _VideoBox extends StatefulWidget {
  const _VideoBox({required this.videoUrl});

  final String? videoUrl;

  @override
  State<_VideoBox> createState() => _VideoBoxState();
}

class _VideoBoxState extends State<_VideoBox> {
  bool _playing = false;

  String? get _videoId =>
      widget.videoUrl == null ? null : _youtubeVideoId(widget.videoUrl!);

  @override
  void didUpdateWidget(covariant _VideoBox oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.videoUrl != widget.videoUrl) _playing = false;
  }

  void _startPlayback() {
    if (_videoId == null) return;
    setState(() => _playing = true);
  }

  @override
  Widget build(BuildContext context) {
    final String? url = widget.videoUrl;
    final bool hasVideo = url != null;
    final String? videoId = _videoId;

    if (_playing && videoId != null) {
      return ClipRRect(
        borderRadius: BorderRadius.circular(24),
        child: InlineYoutubePlayer(key: ValueKey<String>(videoId), videoId: videoId),
      );
    }

    return AspectRatio(
      aspectRatio: 16 / 9,
      child: GlassCard(
        style: GlassStyle.soft,
        radius: 24,
        onTap: videoId != null
            ? _startPlayback
            : (hasVideo ? () => _openUrl(context, url) : null),
        child: Stack(
          fit: StackFit.expand,
          children: <Widget>[
            if (videoId != null)
              Image.network(
                'https://img.youtube.com/vi/$videoId/hqdefault.jpg',
                fit: BoxFit.cover,
                errorBuilder: (_, __, ___) => const SizedBox.shrink(),
              ),
            if (videoId != null)
              DecoratedBox(decoration: BoxDecoration(color: AgriColors.shadowA(.32))),
            Center(
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
                      videoId != null
                          ? 'Nhấn để phát video'
                          : (hasVideo
                              ? 'Nhấn để xem video hướng dẫn trên YouTube'
                              : 'Video hướng dẫn sẽ được cập nhật sớm'),
                      textAlign: TextAlign.center,
                      style: agriStyle(
                        size: 13.5,
                        weight: FontWeight.w600,
                        color: videoId != null
                            ? const Color(0xFFFFFFFF)
                            : AgriColors.inkA(.68),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
