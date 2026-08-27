import 'package:flutter/material.dart';

/// Đường chuyển trang của thiết kế: `animation: agriRise .32s ease-out`
/// (`opacity 0 → 1`, `translateY 12px → 0`).
///
/// Thiết kế không có hiệu ứng trượt ngang kiểu iOS — mọi màn hình đều "nổi
/// lên" tại chỗ, nên dùng đúng một route này cho toàn app.
class AgriRiseRoute<T> extends PageRouteBuilder<T> {
  AgriRiseRoute({required WidgetBuilder builder, super.settings})
      : super(
          transitionDuration: const Duration(milliseconds: 320),
          reverseTransitionDuration: const Duration(milliseconds: 200),
          pageBuilder: (BuildContext context, _, __) => builder(context),
          transitionsBuilder: _buildTransition,
        );

  static Widget _buildTransition(
    BuildContext context,
    Animation<double> animation,
    Animation<double> secondaryAnimation,
    Widget child,
  ) {
    final Animation<double> curved = CurvedAnimation(
      parent: animation,
      curve: Curves.easeOut,
      reverseCurve: Curves.easeIn,
    );
    return FadeTransition(
      opacity: curved,
      child: AnimatedBuilder(
        animation: curved,
        builder: (BuildContext context, Widget? inner) => Transform.translate(
          offset: Offset(0, 12 * (1 - curved.value)),
          child: inner,
        ),
        child: child,
      ),
    );
  }
}

/// Cùng hiệu ứng nhưng dùng cho phần nội dung đổi tại chỗ (đổi tab), nơi
/// không có route mới nào được đẩy vào.
class RiseIn extends StatefulWidget {
  const RiseIn({required this.child, super.key});

  final Widget child;

  @override
  State<RiseIn> createState() => _RiseInState();
}

class _RiseInState extends State<RiseIn> with SingleTickerProviderStateMixin {
  late final AnimationController _controller = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 320),
  )..forward();

  late final Animation<double> _curve =
      CurvedAnimation(parent: _controller, curve: Curves.easeOut);

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return FadeTransition(
      opacity: _curve,
      child: AnimatedBuilder(
        animation: _curve,
        builder: (BuildContext context, Widget? child) => Transform.translate(
          offset: Offset(0, 12 * (1 - _curve.value)),
          child: child,
        ),
        child: widget.child,
      ),
    );
  }
}

/// `@keyframes agriPulse{0%,100%{scale(1);opacity:.9}50%{scale(1.07);opacity:1}}`
/// chạy `1.6s ease-in-out infinite` — vòng tròn ở màn "Đang phân tích".
class AgriPulse extends StatefulWidget {
  const AgriPulse({required this.child, super.key});

  final Widget child;

  @override
  State<AgriPulse> createState() => _AgriPulseState();
}

class _AgriPulseState extends State<AgriPulse>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 800),
  )..repeat(reverse: true);

  late final Animation<double> _t =
      CurvedAnimation(parent: _controller, curve: Curves.easeInOut);

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _t,
      builder: (BuildContext context, Widget? child) => Opacity(
        opacity: 0.9 + 0.1 * _t.value,
        child: Transform.scale(scale: 1 + 0.07 * _t.value, child: child),
      ),
      child: widget.child,
    );
  }
}
