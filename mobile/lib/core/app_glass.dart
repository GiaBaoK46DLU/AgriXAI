import 'dart:math' as math;
import 'dart:ui' as ui;

import 'package:flutter/material.dart';

import 'app_colors.dart';

/// Cặp `begin`/`end` tương ứng một góc `linear-gradient(Ndeg, …)` của CSS.
class CssGradientAxis {
  const CssGradientAxis(this.begin, this.end);

  final Alignment begin;
  final Alignment end;
}

/// Đổi góc `linear-gradient(Ndeg, …)` của CSS sang cặp `begin`/`end` của
/// Flutter. CSS đo góc theo chiều kim đồng hồ tính từ hướng "lên trên";
/// Flutter dùng hệ toạ độ có trục y hướng xuống.
CssGradientAxis cssGradient(double degrees) {
  final double rad = degrees * math.pi / 180.0;
  final double dx = math.sin(rad);
  final double dy = -math.cos(rad);
  return CssGradientAxis(Alignment(-dx, -dy), Alignment(dx, dy));
}

/// `saturate(200%)` của CSS. Flutter không có sẵn nên dựng bằng ma trận màu
/// rồi ghép trước lớp blur bằng `ImageFilter.compose`.
ui.ImageFilter _saturate(double s) {
  const double lr = 0.213, lg = 0.715, lb = 0.072;
  return ColorFilter.matrix(<double>[
    lr + s * (1 - lr), lg * (1 - s), lb * (1 - s), 0, 0, //
    lr * (1 - s), lg + s * (1 - lg), lb * (1 - s), 0, 0, //
    lr * (1 - s), lg * (1 - s), lb + s * (1 - lb), 0, 0, //
    0, 0, 0, 1, 0, //
  ]);
}

/// `backdrop-filter: blur(Npx) saturate(S%)`.
ui.ImageFilter glassFilter(double blurSigma, {double saturation = 2.0}) {
  final ui.ImageFilter blur =
      ui.ImageFilter.blur(sigmaX: blurSigma, sigmaY: blurSigma);
  if (saturation == 1.0) return blur;
  return ui.ImageFilter.compose(outer: _saturate(saturation), inner: blur);
}

/// Một công thức kính mờ: nền gradient trắng 165°, viền trắng mảnh, blur.
///
/// Các bản dựng sẵn bên dưới lấy đúng số của thiết kế v4 — mỗi hằng số ghi
/// kèm chuỗi CSS gốc để đối chiếu.
@immutable
class GlassStyle {
  const GlassStyle({
    required this.topOpacity,
    required this.bottomOpacity,
    required this.borderOpacity,
    this.blurSigma = 0,
    this.borderWidth = 1,
    this.angle = 165,
  });

  final double topOpacity;
  final double bottomOpacity;
  final double borderOpacity;
  final double blurSigma;
  final double borderWidth;
  final double angle;

  Gradient get gradient {
    final CssGradientAxis g = cssGradient(angle);
    return LinearGradient(
      begin: g.begin,
      end: g.end,
      colors: <Color>[
        AgriColors.whiteA(topOpacity),
        AgriColors.whiteA(bottomOpacity),
      ],
    );
  }

  Border get border => Border.all(
        color: AgriColors.whiteA(borderOpacity),
        width: borderWidth,
      );

  /// rgba(255,255,255,.82) → rgba(255,255,255,.43), blur(32) saturate(200%).
  /// Thẻ nổi trên ảnh: ô thời tiết, thẻ đăng nhập.
  static const GlassStyle floating = GlassStyle(
    topOpacity: .82,
    bottomOpacity: .43,
    borderOpacity: .62,
    blurSigma: 32,
  );

  /// .81 → .38, blur(28) — thẻ nội dung chuẩn.
  static const GlassStyle card = GlassStyle(
    topOpacity: .81,
    bottomOpacity: .38,
    borderOpacity: .62,
    blurSigma: 28,
  );

  /// .81 → .38, blur(26), viền .72 — hàng danh sách bấm được.
  static const GlassStyle listRow = GlassStyle(
    topOpacity: .81,
    bottomOpacity: .38,
    borderOpacity: .72,
    blurSigma: 26,
  );

  /// .76 → .35, blur(26), viền .72 — thẻ phụ (bước xử lý, thẻ thuốc…).
  static const GlassStyle soft = GlassStyle(
    topOpacity: .76,
    bottomOpacity: .35,
    borderOpacity: .72,
    blurSigma: 26,
  );

  /// .76 → .35, viền .72, không blur — chỗ thiết kế cố ý bỏ blur.
  static const GlassStyle softFlat = GlassStyle(
    topOpacity: .76,
    bottomOpacity: .35,
    borderOpacity: .72,
  );

  /// .72 → .34, viền .72, không blur — hàng "Chẩn đoán gần đây".
  static const GlassStyle faint = GlassStyle(
    topOpacity: .72,
    bottomOpacity: .34,
    borderOpacity: .72,
  );

  /// .82 → .40, blur(22) — nút icon vuông, nút pill phụ.
  static const GlassStyle control = GlassStyle(
    topOpacity: .82,
    bottomOpacity: .40,
    borderOpacity: .62,
    blurSigma: 22,
  );

  /// .82 → .40, không blur — ô nhập liệu nằm sẵn trong thẻ kính.
  static const GlassStyle field = GlassStyle(
    topOpacity: .82,
    bottomOpacity: .40,
    borderOpacity: .62,
  );

  /// .82 → .43, không blur — ô nhập liệu ở thẻ đăng nhập.
  static const GlassStyle fieldOnFloating = GlassStyle(
    topOpacity: .82,
    bottomOpacity: .43,
    borderOpacity: .62,
  );

  /// .82 → .47, blur(24) — nút/chip nổi trên ảnh.
  static const GlassStyle overImage = GlassStyle(
    topOpacity: .82,
    bottomOpacity: .47,
    borderOpacity: .62,
    blurSigma: 24,
  );

  /// .82 → .41, blur(34) — thanh tab.
  static const GlassStyle tabBar = GlassStyle(
    topOpacity: .82,
    bottomOpacity: .41,
    borderOpacity: .62,
    blurSigma: 34,
  );

  /// .81 → .38, viền .72, không blur — chip meta ở màn kết quả.
  static const GlassStyle metaChip = GlassStyle(
    topOpacity: .81,
    bottomOpacity: .38,
    borderOpacity: .72,
  );
}

/// Bộ đổ bóng của thiết kế.
class AgriShadows {
  const AgriShadows._();

  /// 0 10px 26px rgba(26,60,38,·)
  static List<BoxShadow> card([double o = .11]) => <BoxShadow>[
        BoxShadow(
          color: AgriColors.shadowA(o),
          offset: const Offset(0, 10),
          blurRadius: 26,
        ),
      ];

  /// 0 12px 30px rgba(26,60,38,·)
  static List<BoxShadow> raised([double o = .11]) => <BoxShadow>[
        BoxShadow(
          color: AgriColors.shadowA(o),
          offset: const Offset(0, 12),
          blurRadius: 30,
        ),
      ];

  /// 0 18px 40px rgba(26,60,38,·) — ảnh / hero
  static List<BoxShadow> hero([double o = .14]) => <BoxShadow>[
        BoxShadow(
          color: AgriColors.shadowA(o),
          offset: const Offset(0, 18),
          blurRadius: 40,
        ),
      ];

  /// 0 20px 46px rgba(26,60,38,.15) — thẻ đăng nhập
  static List<BoxShadow> login() => <BoxShadow>[
        BoxShadow(
          color: AgriColors.shadowA(.15),
          offset: const Offset(0, 20),
          blurRadius: 46,
        ),
      ];

  /// 0 14px 30px rgba(24,86,45,.5) — nút chính
  static List<BoxShadow> primaryButton() => <BoxShadow>[
        BoxShadow(
          color: AgriColors.primaryShadowA(.5),
          offset: const Offset(0, 14),
          blurRadius: 30,
        ),
      ];

  /// 0 16px 34px rgba(12,58,29,.46) — nút "Chẩn đoán bệnh" ở trang chủ
  static List<BoxShadow> bigAction() => <BoxShadow>[
        const BoxShadow(
          color: Color.fromRGBO(12, 58, 29, .46),
          offset: Offset(0, 16),
          blurRadius: 34,
        ),
      ];

  /// 0 12px 28px rgba(16,70,36,.6) — FAB
  static List<BoxShadow> fab() => <BoxShadow>[
        BoxShadow(
          color: AgriColors.fabShadowA(.6),
          offset: const Offset(0, 12),
          blurRadius: 28,
        ),
      ];

  /// 0 -6px 30px rgba(26,60,38,.14) — thanh tab
  static List<BoxShadow> tabBar() => <BoxShadow>[
        BoxShadow(
          color: AgriColors.shadowA(.14),
          offset: const Offset(0, -6),
          blurRadius: 30,
        ),
      ];

  /// 0 10px 22px rgba(24,86,45,.32) — nút play trong khung video
  static List<BoxShadow> playButton() => <BoxShadow>[
        BoxShadow(
          color: AgriColors.primaryShadowA(.32),
          offset: const Offset(0, 10),
          blurRadius: 22,
        ),
      ];

  /// 0 8px 18px rgba(122,79,0,.38) — nút "Xem kết quả" trong thẻ cảnh báo
  static List<BoxShadow> amberButton() => <BoxShadow>[
        BoxShadow(
          color: AgriColors.amberShadowA(.38),
          offset: const Offset(0, 8),
          blurRadius: 18,
        ),
      ];

  /// 0 10px 22px rgba(24,86,45,.3) — ô logo ở trang trình bày
  static List<BoxShadow> logo() => <BoxShadow>[
        BoxShadow(
          color: AgriColors.primaryShadowA(.3),
          offset: const Offset(0, 10),
          blurRadius: 22,
        ),
      ];
}

/// Gradient nút chính: `linear-gradient(135deg,#54A96A,#2E6F40)`
LinearGradient get agriPrimaryGradient {
  final CssGradientAxis g = cssGradient(135);
  return LinearGradient(
    begin: g.begin,
    end: g.end,
    colors: const <Color>[AgriColors.primaryLight, AgriColors.primary],
  );
}

/// Gradient thanh tiến trình: `linear-gradient(90deg,#C3D24A,#54A96A)`
const LinearGradient agriProgressGradient = LinearGradient(
  begin: Alignment.centerLeft,
  end: Alignment.centerRight,
  colors: <Color>[AgriColors.olive, AgriColors.primaryLight],
);

/// Thẻ "Vì sao hệ thống kết luận vậy?" và các bước phân tích đã xong:
/// `linear-gradient(165deg,rgba(216,236,208,.86),rgba(178,213,164,.5))`
LinearGradient get agriExplainGradient {
  final CssGradientAxis g = cssGradient(165);
  return LinearGradient(
    begin: g.begin,
    end: g.end,
    colors: const <Color>[
      Color.fromRGBO(216, 236, 208, .86),
      Color.fromRGBO(178, 213, 164, .5),
    ],
  );
}

/// Nút "Chẩn đoán bệnh" ở trang chủ:
/// `linear-gradient(135deg,rgba(84,169,106,.9),rgba(46,111,64,.86))`
LinearGradient get agriBigActionGradient {
  final CssGradientAxis g = cssGradient(135);
  return LinearGradient(
    begin: g.begin,
    end: g.end,
    colors: const <Color>[
      Color.fromRGBO(84, 169, 106, .9),
      Color.fromRGBO(46, 111, 64, .86),
    ],
  );
}

/// Nút "Xoá lô đất":
/// `linear-gradient(165deg,rgba(250,204,128,.62),rgba(242,161,4,.34))`
LinearGradient get agriDangerGradient {
  final CssGradientAxis g = cssGradient(165);
  return LinearGradient(
    begin: g.begin,
    end: g.end,
    colors: const <Color>[
      Color.fromRGBO(250, 204, 128, .62),
      Color.fromRGBO(242, 161, 4, .34),
    ],
  );
}
