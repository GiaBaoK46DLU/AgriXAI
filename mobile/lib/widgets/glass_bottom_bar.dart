import 'package:flutter/material.dart';

import '../core/app_colors.dart';
import '../core/app_glass.dart';
import '../core/app_typography.dart';
import 'agri_icons.dart';
import 'glass_card.dart';

/// Năm tab của thanh dưới. `plots` giữ tên nội bộ cũ (khỏi phải sửa lại mọi
/// nơi đang gọi `AppScope.read(context).select(AgriTab.plots)`) nhưng hiển
/// thị label/icon "Trang chủ" — xem CLAUDE.md mục Diễn đàn nông dân.
enum AgriTab { forum, history, plots, catalog, profile }

/// Thanh tab kính mờ trôi nổi, chỉ hiện ở các màn có tab.
///
/// Không còn nút camera nổi ở giữa — chụp ảnh chẩn đoán giờ chỉ vào được qua
/// nút "Chẩn đoán bệnh" ở trang chủ, để nhường chỗ cho tab Diễn đàn.
class GlassBottomBar extends StatelessWidget {
  const GlassBottomBar({
    required this.current,
    required this.onSelect,
    super.key,
  });

  final AgriTab current;
  final ValueChanged<AgriTab> onSelect;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(left: 12, right: 12, bottom: 6),
      child: GlassCard(
        style: GlassStyle.tabBar,
        radius: 28,
        shadows: AgriShadows.tabBar(),
        padding: const EdgeInsets.fromLTRB(6, 7, 6, 6),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.end,
          children: <Widget>[
            _tab(
              tab: AgriTab.forum,
              label: 'Diễn đàn',
              builder: (Color c) => AgriIcons.tabForum(23, c),
            ),
            _tab(
              tab: AgriTab.history,
              label: 'Lịch sử',
              builder: (Color c) => AgriIcons.tabHistory(23, c),
            ),
            _tab(
              tab: AgriTab.plots,
              label: 'Trang chủ',
              builder: (Color c) => AgriIcons.tabHome(23, c),
            ),
            _tab(
              tab: AgriTab.catalog,
              label: 'Danh mục',
              builder: (Color c) => AgriIcons.tabCatalog(23, c),
            ),
            _tab(
              tab: AgriTab.profile,
              label: 'Tôi',
              builder: (Color c) => AgriIcons.tabProfile(23, c),
            ),
          ],
        ),
      ),
    );
  }

  Widget _tab({
    required AgriTab tab,
    required String label,
    required Widget Function(Color) builder,
  }) {
    final bool active = current == tab;
    final Color color = active ? AgriColors.primary : AgriColors.inkA(.62);
    return Expanded(
      child: Material(
        color: const Color(0x00000000),
        borderRadius: BorderRadius.circular(20),
        child: InkWell(
          onTap: () => onSelect(tab),
          borderRadius: BorderRadius.circular(20),
          child: Container(
            constraints: const BoxConstraints(minHeight: 52),
            padding: const EdgeInsets.only(top: 7),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              mainAxisAlignment: MainAxisAlignment.start,
              children: <Widget>[
                builder(color),
                const SizedBox(height: 3),
                Text(
                  label,
                  style: agriStyle(
                    size: 10.5,
                    weight: FontWeight.w600,
                    color: color,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
