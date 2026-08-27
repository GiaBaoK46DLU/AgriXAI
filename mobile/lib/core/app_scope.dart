import 'package:flutter/widgets.dart';

import '../widgets/glass_bottom_bar.dart';
import 'app_transitions.dart';

/// Trạng thái dùng chung giữa các route: tab nào đang mở ở khung chính.
///
/// Prototype giữ tất cả trong một biến `screen`; app thật dùng `Navigator`
/// cho các màn hình đẩy chồng lên, còn bốn màn có thanh tab thì đổi qua đây.
class AppController extends ChangeNotifier {
  AgriTab _tab = AgriTab.plots;

  AgriTab get tab => _tab;

  void select(AgriTab value) {
    if (_tab == value) return;
    _tab = value;
    notifyListeners();
  }
}

/// Đặt trên `Navigator` (qua `MaterialApp.builder`) nên mọi route đều đọc được.
class AppScope extends InheritedNotifier<AppController> {
  const AppScope({
    required AppController controller,
    required super.child,
    super.key,
  }) : super(notifier: controller);

  /// Đọc và **đăng ký rebuild** khi tab đổi.
  static AppController watch(BuildContext context) =>
      context.dependOnInheritedWidgetOfExactType<AppScope>()!.notifier!;

  /// Chỉ đọc để gọi hành động, không rebuild.
  static AppController read(BuildContext context) =>
      context.getInheritedWidgetOfExactType<AppScope>()!.notifier!;
}

/// Các thao tác điều hướng dùng chung, tất cả đi qua [AgriRiseRoute] để giữ
/// đúng hiệu ứng chuyển trang của thiết kế.
class AppNav {
  const AppNav._();

  static Future<T?> push<T>(BuildContext context, WidgetBuilder builder) {
    return Navigator.of(context).push<T>(AgriRiseRoute<T>(builder: builder));
  }

  static Future<T?> replace<T>(BuildContext context, WidgetBuilder builder) {
    return Navigator.of(context)
        .pushReplacement<T, dynamic>(AgriRiseRoute<T>(builder: builder));
  }

  static Future<T?> reset<T>(BuildContext context, WidgetBuilder builder) {
    return Navigator.of(context).pushAndRemoveUntil<T>(
      AgriRiseRoute<T>(builder: builder),
      (Route<dynamic> route) => false,
    );
  }

  /// Về khung chính và chuyển sang tab chỉ định.
  static void toTab(BuildContext context, AgriTab tab) {
    AppScope.read(context).select(tab);
    Navigator.of(context).popUntil((Route<dynamic> route) => route.isFirst);
  }
}
