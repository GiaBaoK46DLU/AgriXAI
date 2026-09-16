import 'package:flutter/material.dart';

import 'app_colors.dart';

/// Font của thiết kế: Open Sans (400/500/600/700/800).
const String kAgriFontFamily = 'Open Sans';

/// Trả về weight number (400, 700, ...) của `FontWeight`.
int _wghtOf(FontWeight w) => w.value;

/// Tạo `TextStyle` theo đúng cách thiết kế mô tả: cỡ chữ px, weight, và
/// `letter-spacing` tính bằng **em** như trong CSS (Flutter tính bằng px nên
/// phải nhân với cỡ chữ).
///
/// `fontVariations` là phần bắt buộc: file font là bản variable, nếu chỉ đặt
/// `fontWeight` thì chữ vẫn ra weight mặc định.
TextStyle agriStyle({
  required double size,
  FontWeight weight = FontWeight.w400,
  Color? color,
  double? height,
  double em = 0,
  TextDecoration? decoration,
}) {
  return TextStyle(
    fontFamily: kAgriFontFamily,
    fontSize: size,
    fontWeight: weight,
    fontVariations: <FontVariation>[
      FontVariation('wght', _wghtOf(weight).toDouble()),
    ],
    color: color ?? AgriColors.ink,
    height: height,
    letterSpacing: em == 0 ? null : size * em,
    leadingDistribution: TextLeadingDistribution.even,
    decoration: decoration,
  );
}

/// Các cỡ chữ lặp lại nhiều lần trong 12 màn hình.
class AgriTextStyles {
  const AgriTextStyles._();

  /// body của app: `font-size:15px;line-height:1.5`
  static TextStyle get body => agriStyle(size: 15, height: 1.5);

  /// Tiêu đề màn hình có nút back — 21/700/-0.01em
  static TextStyle get screenTitle =>
      agriStyle(size: 21, weight: FontWeight.w700, em: -0.01);

  /// Tiêu đề màn hình dạng tab — 23/700/-0.02em
  static TextStyle get tabTitle =>
      agriStyle(size: 23, weight: FontWeight.w700, em: -0.02);

  /// Tiêu đề mục — 18.5/700/-0.01em
  static TextStyle get sectionTitle =>
      agriStyle(size: 18.5, weight: FontWeight.w700, em: -0.01);

  /// Tiêu đề mục lớn ở trang chủ — 19/700/-0.01em
  static TextStyle get sectionTitleLg =>
      agriStyle(size: 19, weight: FontWeight.w700, em: -0.01);

  /// Kicker in hoa — 11.5/700/0.08em
  static TextStyle kicker(Color color) => agriStyle(
        size: 11.5,
        weight: FontWeight.w700,
        em: 0.08,
        color: color,
      );

  /// Nhãn ô nhập liệu — 12.5/600
  static TextStyle get fieldLabel => agriStyle(
        size: 12.5,
        weight: FontWeight.w600,
        color: AgriColors.inkA(.74),
      );
}
