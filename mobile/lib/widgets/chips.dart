import 'package:flutter/material.dart';

import '../core/app_colors.dart';
import '../core/app_glass.dart';
import '../core/app_typography.dart';
import '../data/demo_data.dart';
import '../models/models.dart';

/// Nhãn dạng viên thuốc, không bấm được.
class PillTag extends StatelessWidget {
  const PillTag({
    required this.label,
    required this.background,
    required this.foreground,
    super.key,
    this.fontSize = 12,
    this.fontWeight = FontWeight.w600,
    this.padding = const EdgeInsets.symmetric(horizontal: 13, vertical: 6),
    this.border,
    this.gradient,
  });

  final String label;
  final Color background;
  final Color foreground;
  final double fontSize;
  final FontWeight fontWeight;
  final EdgeInsets padding;
  final BoxBorder? border;
  final Gradient? gradient;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: padding,
      decoration: BoxDecoration(
        color: gradient == null ? background : null,
        gradient: gradient,
        borderRadius: BorderRadius.circular(999),
        border: border,
      ),
      child: Text(
        label,
        style: agriStyle(
          size: fontSize,
          weight: fontWeight,
          color: foreground,
        ),
      ),
    );
  }
}

/// Chip mức độ — bốn bậc, màu lấy từ [DemoData.severity].
class SeverityChip extends StatelessWidget {
  const SeverityChip({
    required this.severity,
    super.key,
    this.prefix = '',
    this.fontSize = 11,
    this.fontWeight = FontWeight.w700,
    this.padding = const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
  });

  final Severity severity;

  /// Ví dụ `'Mức độ: '` ở màn 06.
  final String prefix;
  final double fontSize;
  final FontWeight fontWeight;
  final EdgeInsets padding;

  @override
  Widget build(BuildContext context) {
    final SeverityStyle s = DemoData.sev(severity);
    return PillTag(
      label: '$prefix${s.name}',
      background: s.bg,
      foreground: s.fg,
      fontSize: fontSize,
      fontWeight: fontWeight,
      padding: padding,
    );
  }
}

/// Chip chọn được: gán lô đất khi chụp, lọc lịch sử, trạng thái lô.
///
/// Trạng thái bật dùng gradient xanh; tắt dùng `rgba(255,255,255,.72)`.
class SelectableChip extends StatelessWidget {
  const SelectableChip({
    required this.label,
    required this.selected,
    required this.onPressed,
    super.key,
    this.minHeight = 46,
    this.fontSize = 13.5,
    this.horizontalPadding = 18,
    this.expand = false,
  });

  final String label;
  final bool selected;
  final VoidCallback onPressed;
  final double minHeight;
  final double fontSize;
  final double horizontalPadding;

  /// `flex:1` — dùng cho hàng chip Trạng thái ở màn 09.
  final bool expand;

  @override
  Widget build(BuildContext context) {
    final Widget chip = Material(
      color: const Color(0x00000000),
      borderRadius: BorderRadius.circular(999),
      child: InkWell(
        onTap: onPressed,
        borderRadius: BorderRadius.circular(999),
        child: Ink(
          decoration: BoxDecoration(
            color: selected ? null : AgriColors.whiteA(.72),
            gradient: selected ? agriPrimaryGradient : null,
            borderRadius: BorderRadius.circular(999),
            border: Border.all(
              color: AgriColors.whiteA(selected ? .96 : .88),
            ),
          ),
          child: Container(
            constraints: BoxConstraints(minHeight: minHeight),
            padding: EdgeInsets.symmetric(horizontal: horizontalPadding),
            alignment: Alignment.center,
            child: Text(
              label,
              textAlign: TextAlign.center,
              style: agriStyle(
                size: fontSize,
                weight: FontWeight.w600,
                color: selected
                    ? const Color(0xFFFFFFFF)
                    : AgriColors.inkA(.9),
              ),
            ),
          ),
        ),
      ),
    );
    return expand ? Expanded(child: chip) : chip;
  }
}

/// Chip mẹo chụp ảnh — nền ô liu nhạt, viền ô liu.
class HintChip extends StatelessWidget {
  const HintChip({required this.label, super.key});

  final String label;

  @override
  Widget build(BuildContext context) {
    return PillTag(
      label: label,
      background: AgriColors.oliveA(.14),
      foreground: AgriColors.oliveInk,
      padding: const EdgeInsets.symmetric(horizontal: 13, vertical: 7),
      border: Border.all(color: AgriColors.oliveA(.22)),
    );
  }
}

/// Chip meta ở màn kết quả — lô đất · thời gian · model.
class MetaChip extends StatelessWidget {
  const MetaChip({required this.label, super.key});

  final String label;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        gradient: GlassStyle.metaChip.gradient,
        borderRadius: BorderRadius.circular(999),
        border: GlassStyle.metaChip.border,
      ),
      child: Text(
        label,
        style: agriStyle(
          size: 11.5,
          weight: FontWeight.w600,
          color: AgriColors.inkSoftA(.7),
        ),
      ),
    );
  }
}
