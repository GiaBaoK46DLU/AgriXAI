import 'package:flutter/material.dart';

import '../core/app_colors.dart';
import '../core/app_typography.dart';
import 'agri_icons.dart';
import 'buttons.dart';

/// Thanh tiến trình bo tròn — nền `rgba(23,58,36,.1)`.
class AgriProgressBar extends StatelessWidget {
  const AgriProgressBar({
    required this.value,
    super.key,
    this.height = 9,
    this.gradient,
    this.color,
    this.animate = false,
  });

  /// 0 → 1.
  final double value;
  final double height;
  final Gradient? gradient;
  final Color? color;

  /// Màn "Đang phân tích" có `transition: width .5s ease`.
  final bool animate;

  @override
  Widget build(BuildContext context) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(999),
      child: Container(
        height: height,
        color: AgriColors.inkSoftA(.1),
        child: Align(
          alignment: Alignment.centerLeft,
          child: LayoutBuilder(
            builder: (BuildContext context, BoxConstraints constraints) {
              final double width =
                  constraints.maxWidth * value.clamp(0.0, 1.0);
              final Widget fill = Container(
                height: height,
                width: width,
                decoration: BoxDecoration(
                  color: gradient == null ? color : null,
                  gradient: gradient,
                  borderRadius: BorderRadius.circular(999),
                ),
              );
              if (!animate) return fill;
              return AnimatedContainer(
                duration: const Duration(milliseconds: 500),
                curve: Curves.ease,
                height: height,
                width: width,
                decoration: BoxDecoration(
                  color: gradient == null ? color : null,
                  gradient: gradient,
                  borderRadius: BorderRadius.circular(999),
                ),
              );
            },
          ),
        ),
      ),
    );
  }
}

/// Hàng tiêu đề có nút back — dùng ở màn 03, 05, 06, 09, 11.
class ScreenHeader extends StatelessWidget {
  const ScreenHeader({
    required this.title,
    required this.onBack,
    super.key,
    this.fontSize = 21,
    this.trailing,
    this.expandTitle = false,
  });

  final String title;
  final VoidCallback onBack;
  final double fontSize;
  final Widget? trailing;

  /// Màn 05 cho tiêu đề `flex:1` để đẩy nút chia sẻ sang phải.
  final bool expandTitle;

  @override
  Widget build(BuildContext context) {
    final Widget titleText = Text(
      title,
      style: agriStyle(size: fontSize, weight: FontWeight.w700, em: -0.01),
    );
    return Row(
      children: <Widget>[
        GlassIconButton(
          icon: AgriIcons.chevronLeft(21, AgriColors.ink),
          onPressed: onBack,
          tooltip: 'Quay lại',
        ),
        const SizedBox(width: 11),
        if (expandTitle) Expanded(child: titleText) else titleText,
        if (trailing != null) ...<Widget>[
          if (!expandTitle) const Spacer(),
          const SizedBox(width: 11),
          trailing!,
        ],
      ],
    );
  }
}

/// Tiêu đề mục kèm nút hành động bên phải.
class SectionHeader extends StatelessWidget {
  const SectionHeader({
    required this.title,
    super.key,
    this.action,
    this.fontSize = 19,
  });

  final String title;
  final Widget? action;
  final double fontSize;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: <Widget>[
        Text(
          title,
          style: agriStyle(size: fontSize, weight: FontWeight.w700, em: -0.01),
        ),
        if (action != null) action!,
      ],
    );
  }
}

/// Viền nét đứt bo góc — dùng cho thẻ "không có thuốc" ở màn 06.
class DashedRoundedBorder extends StatelessWidget {
  const DashedRoundedBorder({
    required this.child,
    required this.radius,
    super.key,
    this.color = const Color(0xF0FFFFFF),
    this.strokeWidth = 1,
    this.dash = 6,
    this.gap = 5,
  });

  final Widget child;
  final double radius;
  final Color color;
  final double strokeWidth;
  final double dash;
  final double gap;

  @override
  Widget build(BuildContext context) {
    return CustomPaint(
      foregroundPainter: _DashedRRectPainter(
        radius: radius,
        color: color,
        strokeWidth: strokeWidth,
        dash: dash,
        gap: gap,
      ),
      child: child,
    );
  }
}

class _DashedRRectPainter extends CustomPainter {
  const _DashedRRectPainter({
    required this.radius,
    required this.color,
    required this.strokeWidth,
    required this.dash,
    required this.gap,
  });

  final double radius;
  final Color color;
  final double strokeWidth;
  final double dash;
  final double gap;

  @override
  void paint(Canvas canvas, Size size) {
    final Paint paint = Paint()
      ..color = color
      ..style = PaintingStyle.stroke
      ..strokeWidth = strokeWidth;
    final double inset = strokeWidth / 2;
    final Path path = Path()
      ..addRRect(
        RRect.fromRectAndRadius(
          Rect.fromLTWH(
            inset,
            inset,
            size.width - strokeWidth,
            size.height - strokeWidth,
          ),
          Radius.circular(radius),
        ),
      );

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
  bool shouldRepaint(_DashedRRectPainter oldDelegate) =>
      oldDelegate.color != color || oldDelegate.radius != radius;
}
