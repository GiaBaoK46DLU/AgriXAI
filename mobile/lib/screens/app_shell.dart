import 'package:flutter/material.dart';

import '../core/app_scope.dart';
import '../core/app_transitions.dart';
import '../widgets/agri_screen.dart';
import '../widgets/glass_bottom_bar.dart';
import 'capture/capture_screen.dart';
import 'catalog/catalog_screen.dart';
import 'history/history_screen.dart';
import 'home/home_screen.dart';
import 'profile/profile_screen.dart';

export '../widgets/glass_bottom_bar.dart' show AgriTab;

/// Khung chính chứa bốn màn hình có thanh tab: 02 · 07 · 10 · 12.
///
/// Các màn còn lại được đẩy chồng lên bằng `Navigator` và không có thanh tab
/// — đúng như `showTabs` trong bản thiết kế.
class AppShell extends StatelessWidget {
  const AppShell({super.key});

  @override
  Widget build(BuildContext context) {
    final AppController controller = AppScope.watch(context);
    final AgriTab tab = controller.tab;

    return AgriScreen(
      bottomBar: GlassBottomBar(
        current: tab,
        onSelect: controller.select,
        onCapture: () => AppNav.push(
          context,
          (_) => const CaptureScreen(),
        ),
      ),
      // Đổi tab thì nội dung "nổi lên" lại, giống prototype vẽ lại màn hình.
      child: RiseIn(key: ValueKey<AgriTab>(tab), child: _screenFor(tab)),
    );
  }

  Widget _screenFor(AgriTab tab) {
    switch (tab) {
      case AgriTab.plots:
        return const HomeScreen();
      case AgriTab.history:
        return const HistoryScreen();
      case AgriTab.catalog:
        return const CatalogScreen();
      case AgriTab.profile:
        return const ProfileScreen();
    }
  }
}
