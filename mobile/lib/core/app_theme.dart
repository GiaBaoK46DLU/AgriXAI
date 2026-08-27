import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import 'app_colors.dart';
import 'app_typography.dart';

/// Theme của app. Thiết kế chỉ có một chế độ sáng — nền xanh, chữ mực đậm.
class AgriTheme {
  const AgriTheme._();

  static ThemeData get light {
    final TextStyle base = agriStyle(size: 15, height: 1.5);

    return ThemeData(
      useMaterial3: true,
      fontFamily: kAgriFontFamily,
      // Nền thật do GlassBackground vẽ; scaffold để trong suốt cho khỏi đè lên.
      scaffoldBackgroundColor: const Color(0x00000000),
      colorScheme: ColorScheme.fromSeed(
        seedColor: AgriColors.primary,
        primary: AgriColors.primary,
        onPrimary: const Color(0xFFFFFFFF),
        surface: AgriColors.bgMid,
        onSurface: AgriColors.ink,
      ),
      textTheme: TextTheme(
        bodyLarge: base,
        bodyMedium: base,
        bodySmall: agriStyle(size: 13, height: 1.5),
      ),
      splashFactory: InkRipple.splashFactory,
      highlightColor: AgriColors.whiteA(.18),
      splashColor: AgriColors.whiteA(.22),
      textSelectionTheme: TextSelectionThemeData(
        cursorColor: AgriColors.primary,
        selectionColor: AgriColors.primaryLightA(.32),
        selectionHandleColor: AgriColors.primary,
      ),
    );
  }

  /// Nền sáng nên icon thanh trạng thái phải là màu tối.
  static const SystemUiOverlayStyle overlayStyle = SystemUiOverlayStyle(
    statusBarColor: Color(0x00000000),
    statusBarIconBrightness: Brightness.dark,
    statusBarBrightness: Brightness.light,
    systemNavigationBarColor: Color(0x00000000),
    systemNavigationBarIconBrightness: Brightness.dark,
  );
}
