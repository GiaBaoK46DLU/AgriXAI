import 'package:flutter/widgets.dart';
import 'package:flutter_svg/flutter_svg.dart';

import '../core/app_colors.dart';

/// Bộ icon của thiết kế, chép nguyên path SVG từ file `.dc.html`.
///
/// Thiết kế dùng icon **hai tông màu** tự vẽ (lá, mặt trời, camera, lọ thuốc)
/// — cố ý không dùng icon nét mảnh của Material. Mỗi tông là một lớp SVG
/// riêng được tô bằng `ColorFilter`, nhờ vậy không phải đổi màu thành chuỗi
/// hex trong XML và vẫn đúng màu tuyệt đối.
class _Layer {
  const _Layer(this.body, this.color);

  final String body;
  final Color color;
}

Widget _icon(double size, List<_Layer> layers, {String viewBox = '0 0 24 24'}) {
  return SizedBox(
    width: size,
    height: size,
    child: Stack(
      children: <Widget>[
        for (final _Layer layer in layers)
          SvgPicture.string(
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="$viewBox">'
            '${layer.body}</svg>',
            width: size,
            height: size,
            fit: BoxFit.fill,
            colorFilter: ColorFilter.mode(layer.color, BlendMode.srcIn),
          ),
      ],
    ),
  );
}

/// Icon nét: tất cả path dùng chung một màu.
Widget _stroke(
  double size,
  String paths,
  Color color, {
  double width = 2.6,
  String linecap = 'round',
  String linejoin = 'round',
}) {
  return _icon(size, <_Layer>[
    _Layer(
      '<g fill="none" stroke="#000" stroke-width="$width" '
      'stroke-linecap="$linecap" stroke-linejoin="$linejoin">$paths</g>',
      color,
    ),
  ]);
}

class AgriIcons {
  const AgriIcons._();

  // ── Lá hai tông — logo, thẻ lô đất, hàng lịch sử, danh mục ─────────────
  static Widget leaf(
    double size, {
    Color a = AgriColors.olive,
    Color b = AgriColors.cream,
  }) {
    return _icon(size, <_Layer>[
      _Layer('<path d="M12 22C12 13 16 4 22 2c0 10-4 18-10 20Z" fill="#000"/>', a),
      _Layer('<path d="M12 22C12 14 8 6 2 5c0 9 4 16 10 17Z" fill="#000"/>', b),
    ]);
  }

  // ── Mặt trời — ô thời tiết ─────────────────────────────────────────────
  static Widget sun(double size, {Color color = AgriColors.accent}) {
    return _icon(size, <_Layer>[
      _Layer(
        '<circle cx="12" cy="12" r="5.2" fill="#000"/>'
        '<g fill="none" stroke="#000" stroke-width="2.1" stroke-linecap="round">'
        '<path d="M12 2.4v2.2"/><path d="M12 19.4v2.2"/>'
        '<path d="M2.4 12h2.2"/><path d="M19.4 12h2.2"/>'
        '<path d="m5.4 5.4 1.5 1.5"/><path d="m17.1 17.1 1.5 1.5"/>'
        '<path d="m18.6 5.4-1.5 1.5"/><path d="m6.9 17.1-1.5 1.5"/></g>',
        color,
      ),
    ]);
  }

  // ── Tam giác cảnh báo ──────────────────────────────────────────────────
  static Widget warning(
    double size, {
    required Color triangle,
    required Color mark,
  }) {
    return _icon(size, <_Layer>[
      _Layer('<path d="M12 2.6 22.4 21H1.6L12 2.6Z" fill="#000"/>', triangle),
      _Layer(
        '<path d="M12 9.4v5.1" fill="none" stroke="#000" stroke-width="2.1" '
        'stroke-linecap="round"/>'
        '<circle cx="12" cy="17.6" r="1.15" fill="#000"/>',
        mark,
      ),
    ]);
  }

  // ── Máy ảnh ba tông ────────────────────────────────────────────────────
  static Widget camera(
    double size, {
    required Color body,
    required Color lens,
    Color dot = AgriColors.olive,
  }) {
    return _icon(size, <_Layer>[
      _Layer(
        '<path d="M9.4 3h5.2l2.1 2.6H20a2 2 0 0 1 2 2V18a2 2 0 0 1-2 2H4a2 2 0 0 '
        '1-2-2V7.6a2 2 0 0 1 2-2h3.3L9.4 3Z" fill="#000"/>',
        body,
      ),
      _Layer('<circle cx="12" cy="12.8" r="4.2" fill="#000"/>', lens),
      _Layer('<circle cx="12" cy="12.8" r="2.1" fill="#000"/>', dot),
    ]);
  }

  // ── Lọ thuốc — mục "Thuốc gợi ý" ───────────────────────────────────────
  static Widget bottle(
    double size, {
    Color body = AgriColors.accent,
    Color mark = AgriColors.inkOnAccent,
  }) {
    return _icon(size, <_Layer>[
      _Layer(
        '<path d="M6.6 13.4 13.4 6.6a4.8 4.8 0 0 1 6.8 6.8l-6.8 6.8a4.8 4.8 0 0 '
        '1-6.8-6.8Z" fill="#000"/>',
        body,
      ),
      _Layer(
        '<path d="M9.6 10.4l4 4" fill="none" stroke="#000" stroke-width="2.2" '
        'stroke-linecap="round"/>',
        mark,
      ),
    ]);
  }

  // ── Thông tin — kicker "Vì sao hệ thống kết luận vậy?" ─────────────────
  static Widget info(double size) {
    return _icon(size, <_Layer>[
      const _Layer(
        '<circle cx="12" cy="12" r="10" fill="#000"/>',
        AgriColors.primary,
      ),
      const _Layer(
        '<g fill="none" stroke="#000" stroke-width="2.4" stroke-linecap="round">'
        '<path d="M12 7.4v.2"/><path d="M12 11v5.6"/></g>',
        Color(0xFF0C2418),
      ),
    ]);
  }

  // ── Tick phòng ngừa ────────────────────────────────────────────────────
  static Widget checkCircle(double size) {
    return _icon(size, <_Layer>[
      _Layer(
        '<circle cx="12" cy="12" r="10" fill="#000"/>',
        AgriColors.oliveA(.2),
      ),
      const _Layer(
        '<path d="m7.5 12.4 3 3 6-6.4" fill="none" stroke="#000" '
        'stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>',
        AgriColors.oliveInk,
      ),
    ]);
  }

  // ── Icon nét ───────────────────────────────────────────────────────────
  static Widget arrowRight(double size, Color color) => _stroke(
        size,
        '<path d="M4 12h15"/><path d="m13 6 6 6-6 6"/>',
        color,
      );

  static Widget chevronLeft(double size, Color color) =>
      _stroke(size, '<path d="m15 18-6-6 6-6"/>', color);

  static Widget chevronRight(double size, Color color) =>
      _stroke(size, '<path d="m9 18 6-6-6-6"/>', color);

  static Widget upload(double size, Color color) => _stroke(
        size,
        '<path d="M12 16V4"/><path d="m7 9 5-5 5 5"/>'
        '<path d="M4 16v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2"/>',
        color,
      );

  static Widget share(double size, Color color) => _stroke(
        size,
        '<path d="M12 16V4"/><path d="m8 8 4-4 4 4"/>'
        '<path d="M5 14v5a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-5"/>',
        color,
      );

  static Widget speaker(double size, Color color) => _stroke(
        size,
        '<path d="M11 5 6 9H2v6h4l5 4V5Z"/>'
        '<path d="M15.5 8.5a5 5 0 0 1 0 7"/>'
        '<path d="M18.5 6a9 9 0 0 1 0 12"/>',
        color,
        width: 2.75,
      );

  static Widget stopSquare(double size, Color color) => _icon(size, <_Layer>[
        _Layer(
          '<rect x="6" y="6" width="12" height="12" rx="2" fill="#000"/>',
          color,
        ),
      ]);

  static Widget externalLink(double size, Color color) => _stroke(
        size,
        '<path d="M14 4h6v6"/><path d="M20 4 10 14"/>'
        '<path d="M18 14v4a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4"/>',
        color,
      );

  static Widget search(double size, Color color) => _stroke(
        size,
        '<circle cx="11" cy="11" r="7"/><path d="m20 20-4.5-4.5"/>',
        color,
      );

  static Widget pencil(double size, Color color) => _stroke(
        size,
        '<path d="M4 20h4L20 8l-4-4L4 16v4Z"/>',
        color,
      );

  static Widget logout(double size, Color color) => _stroke(
        size,
        '<path d="M15 12H4"/><path d="m8 8-4 4 4 4"/>'
        '<path d="M10 4h8a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-8"/>',
        color,
      );

  static Widget play(double size, Color color) => _icon(size, <_Layer>[
        _Layer('<path d="M8 5v14l11-7z" fill="#000"/>', color),
      ]);

  // ── Icon thanh tab ─────────────────────────────────────────────────────
  static Widget tabPlots(double size, Color color, Color fill) =>
      _icon(size, <_Layer>[
        _Layer(
          '<path d="M12 21.5V10" fill="none" stroke="#000" stroke-width="2.2" '
          'stroke-linecap="round"/>'
          '<path d="M12 10C12 6 9.4 3.4 5 2.8c-.4 4.6 2.6 7.4 7 7.2Z" fill="#000"/>',
          color,
        ),
        _Layer(
          '<path d="M12 10.4c0-3.2 2.1-5.4 6-5.8.4 3.9-2.2 6-6 5.8Z" fill="#000"/>',
          fill,
        ),
      ]);

  static Widget tabHistory(double size, Color color) => _icon(size, <_Layer>[
        _Layer(
          '<g fill="none" stroke="#000" stroke-width="2.2">'
          '<circle cx="12" cy="12" r="9.4"/>'
          '<path d="M12 7v5.2l3.4 2" stroke-linecap="round"/></g>',
          color,
        ),
      ]);

  static Widget tabCatalog(double size, Color color) => _icon(size, <_Layer>[
        _Layer(
          '<g fill="none" stroke="#000" stroke-width="2.2">'
          '<path d="M4 19.4V4.6A1.6 1.6 0 0 1 5.6 3H19v18H5.6A1.6 1.6 0 0 1 4 '
          '19.4Z" stroke-linejoin="round"/>'
          '<path d="M9 3v18"/></g>',
          color,
        ),
      ]);

  static Widget tabProfile(double size, Color color) => _icon(size, <_Layer>[
        _Layer(
          '<g fill="none" stroke="#000" stroke-width="2.2">'
          '<circle cx="12" cy="8" r="3.9"/>'
          '<path d="M4.4 20.6a7.6 7.6 0 0 1 15.2 0" stroke-linecap="round"/></g>',
          color,
        ),
      ]);
}

/// Bốn góc chữ L của khung ngắm ở màn 03 — vẽ theo viewBox 370×312 và kéo
/// giãn đầy khung như `preserveAspectRatio="none"` trong thiết kế.
class ViewfinderCorners extends StatelessWidget {
  const ViewfinderCorners({super.key});

  @override
  Widget build(BuildContext context) {
    return IgnorePointer(
      child: SvgPicture.string(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 370 312" '
        'preserveAspectRatio="none">'
        '<g fill="none" stroke="#F1F6EF" stroke-width="4" stroke-linecap="round" '
        'opacity=".9">'
        '<path d="M96 84h-24v-24"/><path d="M274 84h24v-24"/>'
        '<path d="M96 228h-24v24"/><path d="M274 228h24v24"/></g></svg>',
        fit: BoxFit.fill,
      ),
    );
  }
}

/// Lớp khoanh vùng Grad-CAM ở màn 05 — hai ellipse vàng nét đứt trên nền
/// radial gradient mờ dần, viewBox 370×272 kéo giãn đầy khung ảnh.
class GradCamOverlay extends StatelessWidget {
  const GradCamOverlay({super.key});

  @override
  Widget build(BuildContext context) {
    return IgnorePointer(
      child: SvgPicture.string(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 370 272" '
        'preserveAspectRatio="none">'
        '<defs><radialGradient id="agri3Glow">'
        '<stop offset="0%" stop-color="#F2A104" stop-opacity=".6"/>'
        '<stop offset="62%" stop-color="#F2A104" stop-opacity=".2"/>'
        '<stop offset="100%" stop-color="#F2A104" stop-opacity="0"/>'
        '</radialGradient></defs>'
        '<ellipse cx="152" cy="122" rx="100" ry="74" fill="url(#agri3Glow)"/>'
        '<ellipse cx="152" cy="122" rx="100" ry="74" fill="none" stroke="#F2A104" '
        'stroke-width="3" stroke-dasharray="11 8"/>'
        '<ellipse cx="276" cy="198" rx="48" ry="34" fill="url(#agri3Glow)"/>'
        '<ellipse cx="276" cy="198" rx="48" ry="34" fill="none" stroke="#F2A104" '
        'stroke-width="2.4" stroke-dasharray="8 7" opacity=".85"/></svg>',
        fit: BoxFit.fill,
      ),
    );
  }
}
