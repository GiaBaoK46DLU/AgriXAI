import 'package:flutter/material.dart';

import '../core/app_colors.dart';
import '../core/app_glass.dart';
import '../core/app_typography.dart';
import '../data/demo_data.dart';
import '../models/models.dart';
import 'agri_icons.dart';
import 'chips.dart';
import 'glass_card.dart';

/// Thẻ lô đất ở trang chủ — icon lá 46px, tên lô, khu vực · diện tích,
/// chip mức độ lần chẩn đoán gần nhất.
class PlotCard extends StatelessWidget {
  const PlotCard({required this.plot, required this.onTap, super.key});

  final Plot plot;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final SeverityStyle s = DemoData.sev(plot.lastSeverity);
    return GlassCard(
      style: GlassStyle.listRow,
      radius: 26,
      shadows: AgriShadows.card(),
      onTap: onTap,
      padding: const EdgeInsets.all(15),
      child: Row(
        children: <Widget>[
          Container(
            width: 46,
            height: 46,
            decoration: BoxDecoration(
              color: s.iconBg,
              borderRadius: BorderRadius.circular(16),
            ),
            alignment: Alignment.center,
            child: AgriIcons.leaf(24, a: s.leafA, b: s.leafB),
          ),
          const SizedBox(width: 13),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(
                  plot.name,
                  style:
                      agriStyle(size: 16, weight: FontWeight.w700, em: -0.01),
                ),
                const SizedBox(height: 2),
                Text(
                  '${plot.region} · ${plot.area}',
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: agriStyle(size: 12.5, color: AgriColors.inkA(.72)),
                ),
                const SizedBox(height: 6),
                PillTag(
                  label: '${plot.lastDisease} · ${plot.last}',
                  background: s.bg,
                  foreground: s.fg,
                  fontSize: 11.5,
                  padding:
                      const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                ),
              ],
            ),
          ),
          const SizedBox(width: 13),
          AgriIcons.chevronRight(20, AgriColors.inkA(.55)),
        ],
      ),
    );
  }
}

/// Hàng chẩn đoán gọn — chấm màu mức độ, tên bệnh, "lô · thời gian", chip.
/// Dùng ở trang chủ (mục "Chẩn đoán gần đây") và ở chi tiết lô đất.
class DiagnosisMiniRow extends StatelessWidget {
  const DiagnosisMiniRow({
    required this.entry,
    required this.onTap,
    super.key,
    this.style = GlassStyle.faint,
    this.padding = const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
  });

  final DiagnosisEntry entry;
  final VoidCallback onTap;
  final GlassStyle style;
  final EdgeInsets padding;

  @override
  Widget build(BuildContext context) {
    final SeverityStyle s = DemoData.sev(entry.severity);
    return GlassCard(
      style: style,
      radius: 22,
      onTap: onTap,
      padding: padding,
      child: Row(
        children: <Widget>[
          Container(
            width: 9,
            height: 9,
            decoration: BoxDecoration(color: s.dot, shape: BoxShape.circle),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(
                  entry.disease,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: agriStyle(size: 14.5, weight: FontWeight.w600),
                ),
                Text(
                  entry.meta,
                  style: agriStyle(size: 12, color: AgriColors.inkA(.68)),
                ),
              ],
            ),
          ),
          const SizedBox(width: 12),
          SeverityChip(severity: entry.severity),
        ],
      ),
    );
  }
}

/// Hàng lịch sử đầy đủ ở màn 07 — icon lá 50px, chip mức độ và % tin cậy.
class DiagnosisCard extends StatelessWidget {
  const DiagnosisCard({required this.entry, required this.onTap, super.key});

  final DiagnosisEntry entry;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final SeverityStyle s = DemoData.sev(entry.severity);
    return GlassCard(
      style: GlassStyle.listRow,
      radius: 24,
      shadows: AgriShadows.card(.1),
      onTap: onTap,
      padding: const EdgeInsets.all(13),
      child: Row(
        children: <Widget>[
          Container(
            width: 50,
            height: 50,
            decoration: BoxDecoration(
              color: s.iconBg,
              borderRadius: BorderRadius.circular(18),
            ),
            alignment: Alignment.center,
            child: AgriIcons.leaf(26, a: s.leafA, b: s.leafB),
          ),
          const SizedBox(width: 13),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(
                  entry.disease,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style:
                      agriStyle(size: 15.5, weight: FontWeight.w700, em: -0.01),
                ),
                const SizedBox(height: 2),
                Text(
                  entry.meta,
                  style: agriStyle(size: 12.5, color: AgriColors.inkA(.68)),
                ),
              ],
            ),
          ),
          const SizedBox(width: 13),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: <Widget>[
              SeverityChip(severity: entry.severity),
              const SizedBox(height: 6),
              Text(
                entry.confidence,
                style: agriStyle(
                  size: 11.5,
                  weight: FontWeight.w600,
                  color: AgriColors.inkA(.62),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

/// Hàng bệnh trong danh mục (màn 10).
class DiseaseRow extends StatelessWidget {
  const DiseaseRow({required this.disease, required this.onTap, super.key});

  final Disease disease;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final PathogenTypeStyle t = DemoData.tag(disease.type);
    return GlassCard(
      style: GlassStyle.listRow,
      radius: 24,
      shadows: AgriShadows.card(.1),
      onTap: onTap,
      padding: const EdgeInsets.all(15),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Container(
            width: 42,
            height: 42,
            decoration: BoxDecoration(
              color: t.bg,
              borderRadius: BorderRadius.circular(15),
            ),
            alignment: Alignment.center,
            child: AgriIcons.leaf(22, a: t.dot, b: t.fg),
          ),
          const SizedBox(width: 13),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Wrap(
                  spacing: 8,
                  runSpacing: 4,
                  crossAxisAlignment: WrapCrossAlignment.center,
                  children: <Widget>[
                    Text(
                      disease.name,
                      style: agriStyle(
                        size: 16,
                        weight: FontWeight.w700,
                        em: -0.01,
                      ),
                    ),
                    PillTag(
                      label: t.label,
                      background: t.bg,
                      foreground: t.fg,
                      fontSize: 10.5,
                      fontWeight: FontWeight.w700,
                      padding: const EdgeInsets.symmetric(
                        horizontal: 9,
                        vertical: 3,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 4),
                Text(
                  disease.cue,
                  style: agriStyle(
                    size: 13,
                    height: 1.45,
                    color: AgriColors.inkA(.7),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

/// Bước xử lý đánh số — dùng ở màn 06 (ô 28px) và màn 11 (ô 26px).
class TreatmentStep extends StatelessWidget {
  const TreatmentStep({
    required this.index,
    required this.text,
    super.key,
    this.compact = false,
  });

  final int index;
  final String text;
  final bool compact;

  @override
  Widget build(BuildContext context) {
    final double box = compact ? 26 : 28;
    return GlassCard(
      style: compact ? GlassStyle.softFlat : GlassStyle.soft,
      radius: compact ? 22 : 24,
      padding: EdgeInsets.all(compact ? 14 : 15),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Container(
            width: box,
            height: box,
            decoration: BoxDecoration(
              gradient: agriPrimaryGradient,
              borderRadius: BorderRadius.circular(compact ? 9 : 10),
            ),
            alignment: Alignment.center,
            child: Text(
              '$index',
              style: agriStyle(
                size: compact ? 13 : 13.5,
                weight: FontWeight.w700,
                color: const Color(0xFFFFFFFF),
              ),
            ),
          ),
          SizedBox(width: compact ? 12 : 13),
          Expanded(
            child: Text(
              text,
              style: agriStyle(size: compact ? 14 : 14.5, height: 1.5),
            ),
          ),
        ],
      ),
    );
  }
}

/// Dòng phòng ngừa — icon tick ô liu, không có nền.
class PreventionRow extends StatelessWidget {
  const PreventionRow({
    required this.text,
    super.key,
    this.compact = false,
  });

  final String text;
  final bool compact;

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        Padding(
          padding: const EdgeInsets.only(top: 1),
          child: AgriIcons.checkCircle(compact ? 18 : 19),
        ),
        const SizedBox(width: 11),
        Expanded(
          child: Text(
            text,
            style: agriStyle(size: compact ? 14 : 14.5, height: 1.5),
          ),
        ),
      ],
    );
  }
}

/// Thẻ thuốc gợi ý (màn 06) — chỗ đã dựng sẵn để gắn link nhà phân phối.
class ProductRow extends StatelessWidget {
  const ProductRow({required this.product, required this.onTap, super.key});

  final ProductLink product;

  /// `null` khi thuốc chưa có `product_url` — khi đó ẩn luôn nhãn "Xem".
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      style: GlassStyle.card,
      radius: 24,
      shadows: AgriShadows.card(),
      onTap: onTap,
      padding: const EdgeInsets.all(15),
      child: Row(
        children: <Widget>[
          Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(
              color: AgriColors.accentA(.16),
              borderRadius: BorderRadius.circular(15),
              border: Border.all(color: AgriColors.accentA(.26)),
            ),
            alignment: Alignment.center,
            child: AgriIcons.bottle(22),
          ),
          const SizedBox(width: 13),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(
                  product.name,
                  style: agriStyle(
                    size: 15.5,
                    weight: FontWeight.w700,
                    em: -0.01,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  product.group,
                  style: agriStyle(size: 12.5, color: AgriColors.inkA(.7)),
                ),
              ],
            ),
          ),
          if (onTap != null) ...<Widget>[
            const SizedBox(width: 13),
            Row(
              mainAxisSize: MainAxisSize.min,
              children: <Widget>[
                Text(
                  'Xem',
                  style: agriStyle(
                    size: 11.5,
                    weight: FontWeight.w700,
                    color: AgriColors.accentInk,
                  ),
                ),
                const SizedBox(width: 6),
                AgriIcons.externalLink(15, AgriColors.accentInk),
              ],
            ),
          ],
        ],
      ),
    );
  }
}
