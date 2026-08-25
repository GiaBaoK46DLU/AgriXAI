import 'dart:io';

import 'package:flutter/material.dart';

import '../core/app_colors.dart';
import '../core/app_typography.dart';

/// Chỗ đặt ảnh — thay cho `<image-slot>` của bản thiết kế.
///
/// Có ảnh thì hiện ảnh; chưa có thì hiện khung nét đứt kèm câu mô tả, đúng
/// như trạng thái rỗng trong prototype. App thật lấy ảnh từ camera / thư viện
/// và từ `image_url` / `overlay_url` của backend.
class ImageSlot extends StatelessWidget {
  const ImageSlot({
    required this.placeholder,
    super.key,
    this.assetPath,
    this.file,
    this.imageUrl,
    this.onDark = false,
    this.fit = BoxFit.cover,
  });

  /// Câu mô tả hiện khi chưa có ảnh.
  final String placeholder;

  final String? assetPath;
  final File? file;
  final String? imageUrl;

  /// Khung ngắm và khung kết quả có nền tối `#081711`.
  final bool onDark;
  final BoxFit fit;

  @override
  Widget build(BuildContext context) {
    if (file != null) {
      return Image.file(file!, fit: fit, width: double.infinity, height: double.infinity);
    }
    if (assetPath != null) {
      return Image.asset(assetPath!, fit: fit, width: double.infinity, height: double.infinity);
    }
    if (imageUrl != null) {
      return Image.network(
        imageUrl!,
        fit: fit,
        width: double.infinity,
        height: double.infinity,
        errorBuilder: (_, __, ___) => _placeholder(),
      );
    }
    return _placeholder();
  }

  Widget _placeholder() {
    final Color tone =
        onDark ? AgriColors.whiteA(.62) : AgriColors.inkA(.42);
    return CustomPaint(
      painter: _DashedBorderPainter(color: tone),
      child: Container(
        width: double.infinity,
        height: double.infinity,
        color: onDark
            ? AgriColors.whiteA(.04)
            : AgriColors.whiteA(.22),
        alignment: Alignment.center,
        padding: const EdgeInsets.symmetric(horizontal: 24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: <Widget>[
            Icon(Icons.image_outlined, size: 26, color: tone),
            const SizedBox(height: 8),
            Text(
              placeholder,
              textAlign: TextAlign.center,
              style: agriStyle(
                size: 12.5,
                weight: FontWeight.w600,
                color: tone,
                height: 1.45,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// Viền `1.5px dashed` của trạng thái rỗng.
class _DashedBorderPainter extends CustomPainter {
  const _DashedBorderPainter({required this.color});

  final Color color;

  @override
  void paint(Canvas canvas, Size size) {
    final Paint paint = Paint()
      ..color = color
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.5;

    const double dash = 7;
    const double gap = 6;
    final Path path = Path()
      ..addRect(Rect.fromLTWH(0.75, 0.75, size.width - 1.5, size.height - 1.5));

    for (final metric in path.computeMetrics()) {
      double distance = 0;
      while (distance < metric.length) {
        final double next = distance + dash;
        canvas.drawPath(
          metric.extractPath(distance, next.clamp(0, metric.length)),
          paint,
        );
        distance = next + gap;
      }
    }
  }

  @override
  bool shouldRepaint(_DashedBorderPainter oldDelegate) =>
      oldDelegate.color != color;
}
