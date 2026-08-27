import 'package:flutter/material.dart';

import '../core/app_colors.dart';
import '../core/app_glass.dart';
import '../core/app_typography.dart';
import 'agri_icons.dart';
import 'glass_card.dart';

/// Bốn tab của thanh dưới. Nút camera ở giữa không phải tab — nó mở màn 03.
enum AgriTab { plots, history, catalog, profile }

/// Thanh tab kính mờ trôi nổi, chỉ hiện ở màn 02, 07, 10, 12.
class GlassBottomBar extends StatelessWidget {
  const GlassBottomBar({
    required this.current,
    required this.onSelect,
    required this.onCapture,
    super.key,
  });

  final AgriTab current;
  final ValueChanged<AgriTab> onSelect;
  final VoidCallback onCapture;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(left: 12, right: 12, bottom: 6),
      child: Stack(
        clipBehavior: Clip.none,
        alignment: Alignment.bottomCenter,
        children: <Widget>[
          GlassCard(
            style: GlassStyle.tabBar,
            radius: 28,
            shadows: AgriShadows.tabBar(),
            padding: const EdgeInsets.fromLTRB(6, 7, 6, 6),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: <Widget>[
                _tab(
                  tab: AgriTab.plots,
                  label: 'Lô đất',
                  builder: (Color c) => AgriIcons.tabPlots(
                    23,
                    c,
                    current == AgriTab.plots
                        ? AgriColors.olive
                        : AgriColors.inkA(.45),
                  ),
                ),
                _tab(
                  tab: AgriTab.history,
                  label: 'Lịch sử',
                  builder: (Color c) => AgriIcons.tabHistory(23, c),
                ),
                // Chỗ trống cho nút camera nhô lên ở lớp trên.
                const Expanded(child: SizedBox(height: 52)),
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
          Positioned(bottom: 7, child: _captureButton()),
        ],
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

  Widget _captureButton() {
    return DecoratedBox(
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        boxShadow: AgriShadows.fab(),
      ),
      child: Material(
        color: const Color(0x00000000),
        shape: const CircleBorder(),
        clipBehavior: Clip.antiAlias,
        child: InkWell(
          onTap: onCapture,
          customBorder: const CircleBorder(),
          child: Ink(
            width: 62,
            height: 62,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              gradient: agriPrimaryGradient,
              border: Border.all(color: AgriColors.whiteA(.5), width: 3),
            ),
            child: Center(
              child: AgriIcons.camera(
                29,
                body: AgriColors.cream,
                lens: AgriColors.primary,
              ),
            ),
          ),
        ),
      ),
    );
  }
}
