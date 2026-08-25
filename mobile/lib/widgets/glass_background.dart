import 'dart:ui' as ui;

import 'package:flutter/material.dart';

import '../core/app_colors.dart';
import '../core/app_glass.dart';

/// Nền của toàn app: gradient xanh 168° cộng **ba quầng sáng** cố định phía
/// sau.
///
/// Ba quầng này bắt buộc phải có — nếu bỏ thì lớp kính mờ không có gì để làm
/// mờ và mọi thẻ trông như màu phẳng.
class GlassBackground extends StatelessWidget {
  const GlassBackground({required this.child, super.key});

  final Widget child;

  @override
  Widget build(BuildContext context) {
    final CssGradientAxis axis = cssGradient(168);
    return DecoratedBox(
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: axis.begin,
          end: axis.end,
          colors: const <Color>[
            AgriColors.bgTop,
            AgriColors.bgMid,
            AgriColors.bgBottom,
          ],
          stops: const <double>[0, .52, 1],
        ),
      ),
      child: Stack(
        clipBehavior: Clip.hardEdge,
        children: <Widget>[
          // top:-90 left:-70 · 300×300 · rgba(84,169,106,.34) · blur(26)
          Positioned(
            top: -90,
            left: -70,
            child: _Halo(
              size: 300,
              color: AgriColors.primaryLightA(.34),
              blur: 26,
            ),
          ),
          // top:210 right:-110 · 290×290 · rgba(195,210,74,.3) · blur(30)
          Positioned(
            top: 210,
            right: -110,
            child: _Halo(size: 290, color: AgriColors.oliveA(.3), blur: 30),
          ),
          // bottom:-70 left:20 · 280×280 · rgba(242,161,4,.22) · blur(34)
          Positioned(
            bottom: -70,
            left: 20,
            child: _Halo(size: 280, color: AgriColors.accentA(.22), blur: 34),
          ),
          Positioned.fill(child: child),
        ],
      ),
    );
  }
}

class _Halo extends StatelessWidget {
  const _Halo({required this.size, required this.color, required this.blur});

  final double size;
  final Color color;
  final double blur;

  @override
  Widget build(BuildContext context) {
    return IgnorePointer(
      child: ImageFiltered(
        imageFilter: ui.ImageFilter.blur(sigmaX: blur, sigmaY: blur),
        child: Container(
          width: size,
          height: size,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            gradient: RadialGradient(
              colors: <Color>[color, color.withAlpha(0)],
              stops: const <double>[0, .7],
            ),
          ),
        ),
      ),
    );
  }
}
