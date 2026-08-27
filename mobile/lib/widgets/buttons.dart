import 'package:flutter/material.dart';

import '../core/app_colors.dart';
import '../core/app_glass.dart';
import '../core/app_typography.dart';
import 'glass_card.dart';

/// Nút chính dạng viên thuốc, có nút tròn 48px ở đầu bên phải.
///
/// `padding:6px 6px 6px 22px` + vòng tròn 48 → cao 60. Dùng cho: Đăng nhập,
/// Chụp ảnh, Xem gợi ý xử lý.
class PrimaryPillButton extends StatelessWidget {
  const PrimaryPillButton({
    required this.label,
    required this.icon,
    required this.onPressed,
    super.key,
  });

  final String label;

  /// Icon nằm trong vòng tròn màu `#F1F6EF`.
  final Widget icon;
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(999),
        boxShadow: AgriShadows.primaryButton(),
      ),
      child: Material(
        color: const Color(0x00000000),
        borderRadius: BorderRadius.circular(999),
        child: InkWell(
          onTap: onPressed,
          borderRadius: BorderRadius.circular(999),
          child: Ink(
            decoration: BoxDecoration(
              gradient: agriPrimaryGradient,
              borderRadius: BorderRadius.circular(999),
            ),
            child: Padding(
              padding: const EdgeInsets.fromLTRB(22, 6, 6, 6),
              child: Row(
                children: <Widget>[
                  Expanded(
                    child: Text(
                      label,
                      style: agriStyle(
                        size: 16.5,
                        weight: FontWeight.w700,
                        color: const Color(0xFFFFFFFF),
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Container(
                    width: 48,
                    height: 48,
                    decoration: const BoxDecoration(
                      color: AgriColors.cream,
                      shape: BoxShape.circle,
                    ),
                    alignment: Alignment.center,
                    child: icon,
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

/// Nút chính đặc, chữ căn giữa — `min-height:54px`.
class PrimarySolidButton extends StatelessWidget {
  const PrimarySolidButton({
    required this.label,
    required this.onPressed,
    super.key,
    this.minHeight = 54,
    this.fontSize = 16.5,
  });

  final String label;
  final VoidCallback onPressed;
  final double minHeight;
  final double fontSize;

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(999),
        boxShadow: AgriShadows.primaryButton(),
      ),
      child: Material(
        color: const Color(0x00000000),
        borderRadius: BorderRadius.circular(999),
        child: InkWell(
          onTap: onPressed,
          borderRadius: BorderRadius.circular(999),
          child: Ink(
            decoration: BoxDecoration(
              gradient: agriPrimaryGradient,
              borderRadius: BorderRadius.circular(999),
            ),
            child: Container(
              constraints: BoxConstraints(minHeight: minHeight),
              alignment: Alignment.center,
              child: Text(
                label,
                textAlign: TextAlign.center,
                style: agriStyle(
                  size: fontSize,
                  weight: FontWeight.w700,
                  color: const Color(0xFFFFFFFF),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

/// Nút phụ dạng viên thuốc bằng kính mờ.
class GlassPillButton extends StatelessWidget {
  const GlassPillButton({
    required this.label,
    required this.onPressed,
    super.key,
    this.icon,
    this.minHeight = 48,
    this.fontSize = 15,
    this.fontWeight = FontWeight.w600,
    this.color = AgriColors.ink,
    this.style = GlassStyle.control,
    this.gradient,
    this.border,
    this.background,
  });

  final String label;
  final VoidCallback onPressed;
  final Widget? icon;
  final double minHeight;
  final double fontSize;
  final FontWeight fontWeight;
  final Color color;
  final GlassStyle style;
  final Gradient? gradient;
  final Border? border;
  final Color? background;

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      style: style,
      gradient: gradient,
      color: background,
      border: border,
      radius: 999,
      onTap: onPressed,
      child: Container(
        constraints: BoxConstraints(minHeight: minHeight),
        alignment: Alignment.center,
        padding: const EdgeInsets.symmetric(horizontal: 18),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          mainAxisSize: MainAxisSize.min,
          children: <Widget>[
            if (icon != null) ...<Widget>[icon!, const SizedBox(width: 10)],
            Flexible(
              child: Text(
                label,
                textAlign: TextAlign.center,
                style: agriStyle(
                  size: fontSize,
                  weight: fontWeight,
                  color: color,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// Nút chữ trơn, không nền — "Tất cả", "Tra cứu bệnh mà không cần đăng nhập".
class GhostButton extends StatelessWidget {
  const GhostButton({
    required this.label,
    required this.onPressed,
    super.key,
    this.color = AgriColors.primary,
    this.fontSize = 13.5,
    this.minHeight = 40,
    this.padding = const EdgeInsets.symmetric(horizontal: 12),
  });

  final String label;
  final VoidCallback onPressed;
  final Color color;
  final double fontSize;
  final double minHeight;
  final EdgeInsets padding;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: const Color(0x00000000),
      borderRadius: BorderRadius.circular(999),
      child: InkWell(
        onTap: onPressed,
        borderRadius: BorderRadius.circular(999),
        child: Container(
          constraints: BoxConstraints(minHeight: minHeight),
          padding: padding,
          alignment: Alignment.center,
          child: Text(
            label,
            style: agriStyle(
              size: fontSize,
              weight: FontWeight.w600,
              color: color,
            ),
          ),
        ),
      ),
    );
  }
}

/// Nút icon vuông 44×44 bo 16 — nút back, nút chia sẻ, nút sửa lô.
class GlassIconButton extends StatelessWidget {
  const GlassIconButton({
    required this.icon,
    required this.onPressed,
    super.key,
    this.size = 44,
    this.radius = 16,
    this.style = GlassStyle.control,
    this.tooltip,
  });

  final Widget icon;
  final VoidCallback onPressed;
  final double size;
  final double radius;
  final GlassStyle style;
  final String? tooltip;

  @override
  Widget build(BuildContext context) {
    final Widget button = GlassCard(
      style: style,
      radius: radius,
      width: size,
      height: size,
      onTap: onPressed,
      child: Center(child: icon),
    );
    if (tooltip == null) return button;
    return Tooltip(message: tooltip!, child: button);
  }
}
