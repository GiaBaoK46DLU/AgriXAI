import 'dart:math' as math;

import 'package:flutter/widgets.dart';

/// Khoảng cách và kích thước lặp lại trong thiết kế.
class AgriMetrics {
  const AgriMetrics._();

  /// Padding ngang của phần lớn màn hình.
  static const double screenH = 16;

  /// Padding trên trong thiết kế đã tính cả thanh trạng thái (62px trên khung
  /// 402×874). Trên máy thật thanh trạng thái cao khác nhau nên lấy
  /// `viewPadding.top + 15`, và không bao giờ nhỏ hơn 62 để giữ đúng nhịp
  /// khoảng trắng của thiết kế.
  static double screenTop(BuildContext context) {
    final double statusBar = MediaQuery.viewPaddingOf(context).top;
    return math.max(statusBar + 15, 62);
  }

  /// Màn 01 dùng padding trên 74px.
  static double loginTop(BuildContext context) {
    final double statusBar = MediaQuery.viewPaddingOf(context).top;
    return math.max(statusBar + 27, 74);
  }

  /// Dải trống dưới thanh tab — trong thiết kế là 26px (vùng home indicator).
  static double bottomInset(BuildContext context) {
    final double gesture = MediaQuery.viewPaddingOf(context).bottom;
    return math.max(gesture, 26);
  }

  /// Vùng bấm tối thiểu — người dùng là nông dân ngoài đồng, một tay cầm máy.
  static const double minTap = 44;
}
