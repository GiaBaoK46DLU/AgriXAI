import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import 'core/app_colors.dart';
import 'core/app_scope.dart';
import 'core/app_theme.dart';
import 'core/app_transitions.dart';
import 'screens/app_shell.dart';
import 'screens/login_screen.dart';
import 'services/auth_service.dart' show CurrentUser;
import 'services/session.dart' as session;
import 'widgets/agri_icons.dart';
import 'widgets/agri_screen.dart';

/// Điều hướng được ngoài `BuildContext` — `ApiClient.onSessionExpired` cần
/// đưa người dùng về màn Đăng nhập từ một callback thuần Dart (không có
/// widget nào gọi nó), nên phải qua khoá `Navigator` toàn cục thay vì
/// `Navigator.of(context)` như `AppNav`.
final GlobalKey<NavigatorState> appNavigatorKey = GlobalKey<NavigatorState>();

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  SystemChrome.setSystemUIOverlayStyle(AgriTheme.overlayStyle);
  runApp(const AgriXaiFarmerApp());
}

class AgriXaiFarmerApp extends StatefulWidget {
  const AgriXaiFarmerApp({super.key});

  @override
  State<AgriXaiFarmerApp> createState() => _AgriXaiFarmerAppState();
}

class _AgriXaiFarmerAppState extends State<AgriXaiFarmerApp> {
  final AppController _controller = AppController();

  @override
  void initState() {
    super.initState();
    // Gán lại mỗi lần widget này dựng (kể cả trong `flutter test`, nơi mỗi
    // test tự thay `session.apiClient` bằng bản giả trước khi `pumpWidget`)
    // để luôn trỏ đúng vào `ApiClient` đang dùng thật sự.
    session.apiClient.onSessionExpired = _handleSessionExpired;
  }

  /// Access token hết hạn và refresh token cũng không làm mới được nữa
  /// (xem `ApiClient._guarded`) — dọn phiên rồi đưa thẳng về màn Đăng nhập,
  /// bất kể đang ở màn nào. Không hiện thông báo lỗi riêng: `LoginScreen`
  /// hiện ra ngay là tín hiệu đủ rõ cho người dùng biết phải đăng nhập lại.
  void _handleSessionExpired() {
    session.currentUser = null;
    appNavigatorKey.currentState?.pushAndRemoveUntil<void>(
      AgriRiseRoute<void>(builder: (_) => const LoginScreen()),
      (Route<dynamic> route) => false,
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'AgriXAI',
      debugShowCheckedModeBanner: false,
      navigatorKey: appNavigatorKey,
      theme: AgriTheme.light,
      // Đặt trên Navigator để mọi route đọc được trạng thái tab.
      builder: (BuildContext context, Widget? child) => AppScope(
        controller: _controller,
        child: child ?? const SizedBox.shrink(),
      ),
      home: const _StartupGate(),
    );
  }
}

/// Bắt buộc đăng nhập trước khi vào app — không còn màn "dùng thử không cần
/// đăng nhập" (xem CLAUDE.md). Nếu máy đã có token hợp lệ từ lần đăng nhập
/// trước (`AuthService.tryRestore`) thì vào thẳng [AppShell], không bắt gõ
/// lại mật khẩu mỗi lần mở app.
class _StartupGate extends StatefulWidget {
  const _StartupGate();

  @override
  State<_StartupGate> createState() => _StartupGateState();
}

class _StartupGateState extends State<_StartupGate> {
  bool _checking = true;

  @override
  void initState() {
    super.initState();
    _restore();
  }

  Future<void> _restore() async {
    final CurrentUser? user = await session.authService.tryRestore();
    if (!mounted) return;
    session.currentUser = user;
    setState(() => _checking = false);
  }

  @override
  Widget build(BuildContext context) {
    if (_checking) {
      return AgriScreen(
        child: Center(child: AgriIcons.leaf(64, a: AgriColors.olive, b: AgriColors.primary)),
      );
    }
    return session.currentUser == null ? const LoginScreen() : const AppShell();
  }
}
