import 'package:flutter/material.dart';

import '../core/app_metrics.dart';
import 'glass_background.dart';

/// Khung chung của mọi màn hình: nền kính + dải trống dưới cùng.
///
/// Thiết kế luôn chừa 26px cuối màn (vùng home indicator), có thanh tab hay
/// không cũng vậy.
class AgriScreen extends StatelessWidget {
  const AgriScreen({
    required this.child,
    super.key,
    this.bottomBar,
    this.resizeToAvoidBottomInset = true,
  });

  final Widget child;
  final Widget? bottomBar;
  final bool resizeToAvoidBottomInset;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0x00000000),
      resizeToAvoidBottomInset: resizeToAvoidBottomInset,
      body: GlassBackground(
        child: Column(
          children: <Widget>[
            Expanded(child: child),
            if (bottomBar != null) bottomBar!,
            SizedBox(height: AgriMetrics.bottomInset(context)),
          ],
        ),
      ),
    );
  }
}
