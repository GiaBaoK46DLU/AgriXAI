import 'package:flutter/material.dart';

import '../core/app_glass.dart';

/// Thẻ kính mờ — công thức dùng lại khắp 12 màn hình.
///
/// Mặc định lấy [GlassStyle.card]; các tham số `gradient` / `color` /
/// `border` / `blurSigma` chỉ dùng cho vài chỗ thiết kế cố ý đổi công thức
/// (thẻ giải thích XAI, thẻ cảnh báo, thẻ "Nhận biết nhanh"…).
///
/// Lưu ý: `BackdropFilter` chỉ làm mờ những gì **nằm dưới nó trong cây
/// widget**, nên thẻ phải nằm trong [GlassBackground].
class GlassCard extends StatelessWidget {
  const GlassCard({
    required this.child,
    super.key,
    this.style = GlassStyle.card,
    this.radius = 28,
    this.borderRadius,
    this.padding,
    this.margin,
    this.shadows,
    this.gradient,
    this.color,
    this.border,
    this.blurSigma,
    this.onTap,
    this.width,
    this.height,
  });

  final Widget child;
  final GlassStyle style;
  final double radius;
  final BorderRadius? borderRadius;
  final EdgeInsetsGeometry? padding;
  final EdgeInsetsGeometry? margin;
  final List<BoxShadow>? shadows;
  final Gradient? gradient;
  final Color? color;
  final Border? border;
  final double? blurSigma;
  final VoidCallback? onTap;
  final double? width;
  final double? height;

  @override
  Widget build(BuildContext context) {
    final BorderRadius br = borderRadius ?? BorderRadius.circular(radius);
    final double sigma = blurSigma ?? style.blurSigma;

    Widget content = Padding(
      padding: padding ?? EdgeInsets.zero,
      child: child,
    );

    if (onTap != null) {
      content = Material(
        color: const Color(0x00000000),
        child: InkWell(
          onTap: onTap,
          borderRadius: br,
          child: content,
        ),
      );
    }

    Widget body = Container(
      width: width,
      height: height,
      decoration: BoxDecoration(
        color: color,
        gradient: color == null ? (gradient ?? style.gradient) : null,
        borderRadius: br,
      ),
      // Viền vẽ đè lên nội dung, giống `border` của CSS.
      foregroundDecoration: BoxDecoration(
        border: border ?? style.border,
        borderRadius: br,
      ),
      child: content,
    );

    body = ClipRRect(
      borderRadius: br,
      child: sigma > 0
          ? BackdropFilter(filter: glassFilter(sigma), child: body)
          : body,
    );

    if (shadows != null && shadows!.isNotEmpty) {
      body = DecoratedBox(
        decoration: BoxDecoration(borderRadius: br, boxShadow: shadows),
        child: body,
      );
    }

    if (margin != null) {
      body = Padding(padding: margin!, child: body);
    }
    return body;
  }
}
