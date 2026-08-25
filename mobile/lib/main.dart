import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import 'core/app_scope.dart';
import 'core/app_theme.dart';
import 'screens/login_screen.dart';

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
      home: const LoginScreen(),
    );
  }
}
