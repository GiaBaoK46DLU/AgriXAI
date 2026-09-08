import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import 'core/app_colors.dart';
import 'core/app_scope.dart';
import 'core/app_theme.dart';
import 'screens/app_shell.dart';
import 'screens/login_screen.dart';
import 'services/auth_service.dart' show CurrentUser;
import 'services/session.dart' as session;
import 'widgets/glass_background.dart';

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
  late final Future<CurrentUser?> _restore =
      session.authService.tryRestore();

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
      theme: AgriTheme.light,
      // Đặt trên Navigator để mọi route đọc được trạng thái tab.
      builder: (BuildContext context, Widget? child) => AppScope(
        controller: _controller,
        child: child ?? const SizedBox.shrink(),
      ),
      // Còn token đã lưu (đăng nhập lần trước) thì vào thẳng AppShell, không
      // bắt đăng nhập lại mỗi lần mở app.
      home: FutureBuilder<CurrentUser?>(
        future: _restore,
        builder: (BuildContext context, AsyncSnapshot<CurrentUser?> snapshot) {
          if (snapshot.connectionState != ConnectionState.done) {
            return const _SplashScreen();
          }
          session.currentUser = snapshot.data;
          return snapshot.data != null ? const AppShell() : const LoginScreen();
        },
      ),
    );
  }
}

class _SplashScreen extends StatelessWidget {
  const _SplashScreen();

  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      backgroundColor: Color(0x00000000),
      body: GlassBackground(
        child: Center(
          child: CircularProgressIndicator(color: AgriColors.primary),
        ),
      ),
    );
  }
}
