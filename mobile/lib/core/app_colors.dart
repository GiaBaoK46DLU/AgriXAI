import 'package:flutter/painting.dart';

/// Bảng màu chốt của bản thiết kế **AgriXAI Farmer v4**.
///
/// Mọi giá trị lấy nguyên từ file thiết kế, không tự đặt thêm màu mới.
/// Hàm nhận `opacity` tương ứng với `rgba(...)` trong CSS — giữ đúng bộ ba
/// R,G,B của thiết kế thay vì pha sẵn ra hex, để so lại với file gốc cho dễ.
class AgriColors {
  const AgriColors._();

  // ── Nền app ────────────────────────────────────────────────────────────
  // linear-gradient(168deg,#C9DCC0 0%,#B0CBA4 52%,#96BC87 100%)
  static const Color bgTop = Color(0xFFC9DCC0);
  static const Color bgMid = Color(0xFFB0CBA4);
  static const Color bgBottom = Color(0xFF96BC87);

  /// Lớp phủ sáng trên ảnh hero — rgba(190,212,178,·)
  static Color heroVeil(double o) => Color.fromRGBO(190, 212, 178, o);

  // ── Chữ ────────────────────────────────────────────────────────────────
  static const Color ink = Color(0xFF12301D); // chữ chính trong app
  static const Color inkDeep = Color(0xFF122E1D); // chữ trên trang trình bày
  static const Color inkOnAccent = Color(0xFF12240F); // chữ trên nền vàng

  static Color inkA(double o) => Color.fromRGBO(18, 48, 29, o); // #12301D
  static Color inkSoftA(double o) => Color.fromRGBO(23, 58, 36, o); // #173A24
  static Color inkOnAccentA(double o) => Color.fromRGBO(18, 36, 15, o);

  // ── Xanh chủ đạo ───────────────────────────────────────────────────────
  static const Color primary = Color(0xFF2E6F40);
  static const Color primaryLight = Color(0xFF54A96A);
  static Color primaryLightA(double o) => Color.fromRGBO(84, 169, 106, o);
  static Color primaryA(double o) => Color.fromRGBO(46, 111, 64, o);
  static Color mintA(double o) => Color.fromRGBO(143, 220, 163, o);

  // ── Ô liu ──────────────────────────────────────────────────────────────
  static const Color olive = Color(0xFFC3D24A);
  static const Color oliveInk = Color(0xFF4A5810);
  static Color oliveA(double o) => Color.fromRGBO(195, 210, 74, o);

  // ── Vàng cảnh báo ──────────────────────────────────────────────────────
  static const Color accent = Color(0xFFF2A104);
  static const Color accentInk = Color(0xFF7A4F00);
  static const Color accentInkDeep = Color(0xFF5C3A00);
  static const Color accentInkDarkest = Color(0xFF3D2400);
  static Color accentA(double o) => Color.fromRGBO(242, 161, 4, o);

  // ── Mức độ "Nặng" ──────────────────────────────────────────────────────
  static const Color severeBg = Color(0xFFC24A12);
  static const Color severeFg = Color(0xFFFFF3E8);
  static const Color severeDot = Color(0xFFE4661F);
  static Color severeDotA(double o) => Color.fromRGBO(228, 102, 31, o);

  // ── Màu lẻ dùng đúng một chỗ ───────────────────────────────────────────
  static const Color cream = Color(0xFFF1F6EF); // nút tròn trong nút chính
  static const Color viewfinderVoid = Color(0xFF081711); // nền khung ngắm
  static const Color top3Ink = Color(0xFF2E2B25); // chữ hàng "3 khả năng"
  static const Color paleLime = Color(0xFFF0FAE1); // viền thẻ số ở hồ sơ
  static const Color forecastBorder = Color(0xFFE5AC3D);
  static const Color alertCardBg = Color(0xFFDBEDBE);
  static Color alertCardBorder() => const Color(0x56F2A104);
  static Color alertButtonBg() => const Color(0xCFFFB925);
  static Color weatherStripBg() => const Color(0x72F2A104);
  static const Color diseaseTagBorder = Color(0x81D67F48);

  // ── Đổ bóng — rgba(26,60,38,·) và rgba(24,86,45,·) ─────────────────────
  static Color shadowA(double o) => Color.fromRGBO(26, 60, 38, o);
  static Color primaryShadowA(double o) => Color.fromRGBO(24, 86, 45, o);
  static Color fabShadowA(double o) => Color.fromRGBO(16, 70, 36, o);
  static Color amberShadowA(double o) => Color.fromRGBO(122, 79, 0, o);

  static Color whiteA(double o) => Color.fromRGBO(255, 255, 255, o);
}
