import 'dart:typed_data';

import 'package:agrixai_farmer/services/image_resize.dart';
import 'package:flutter_test/flutter_test.dart';

/// Giá trị kỳ vọng sinh bằng Pillow 12.3.0:
/// `Image.fromarray(src).resize((w, h), Image.BILINEAR)` — đúng phép resize
/// máy chủ dùng (`build_infer_transform`), nên bản Dart phải trùng từng byte.
Uint8List _pattern(int width, int height) => Uint8List.fromList(<int>[
      for (int i = 0; i < width * height * 3; i++) (i * 37 + 11) % 256,
    ]);

void main() {
  test('trùng Pillow khi thu nhỏ cả hai chiều (13×9 → 5×4)', () {
    expect(
      resizeRgbBilinear(_pattern(13, 9), 13, 9, 5, 4),
      <int>[
        115, 122, 139, 146, 130, 120, 127, 144, 119, 119, 125, 127, 124, 122,
        121, 132, 132, 117, 124, 134, 138, 137, 124, 131, 136, 111, 121, 122,
        131, 108, 116, 119, 138, 132, 118, 127, 130, 140, 124, 125, 129, 140,
        145, 126, 134, 130, 108, 125, 123, 128, 119, 118, 126, 127, 133, 126,
        126, 133, 132, 140,
      ],
    );
  });

  test('trùng Pillow khi phóng to cả hai chiều (3×2 → 6×5)', () {
    expect(
      resizeRgbBilinear(_pattern(3, 2), 3, 2, 6, 5),
      <int>[
        11, 48, 85, 39, 76, 113, 94, 131, 168, 150, 123, 160, 205, 50,
        87, 233, 14, 51, 19, 56, 93, 47, 84, 114, 102, 139, 157, 151,
        131, 149, 194, 58, 88, 215, 22, 59, 50, 87, 124, 78, 115, 120,
        133, 170, 111, 157, 162, 103, 148, 89, 94, 144, 53, 90, 80, 117,
        154, 108, 145, 125, 163, 200, 64, 162, 192, 56, 101, 119, 99, 72,
        83, 120, 88, 125, 162, 116, 153, 126, 171, 208, 53, 163, 200, 45,
        90, 127, 100, 54, 91, 128,
      ],
    );
  });

  test('trùng Pillow khi chỉ thu chiều ngang (40×6 → 7×6)', () {
    expect(
      resizeRgbBilinear(_pattern(40, 6), 40, 6, 7, 6),
      <int>[
        127, 116, 116, 132, 131, 134, 135, 138, 140, 128, 145, 108, 120, 113,
        116, 123, 124, 127, 128, 125, 135, 130, 148, 146, 141, 106, 113, 115,
        117, 119, 122, 125, 127, 130, 132, 134, 141, 143, 136, 149, 101, 138,
        114, 124, 121, 122, 125, 126, 133, 136, 129, 141, 137, 139, 109, 123,
        141, 115, 118, 117, 133, 133, 122, 135, 124, 124, 140, 139, 135, 116,
        134, 109, 118, 120, 116, 128, 121, 124, 131, 132, 135, 136, 133, 143,
        119, 156, 108, 121, 114, 116, 123, 125, 127, 130, 133, 135, 138, 140,
        142, 144, 107, 116, 111, 109, 127, 122, 132, 129, 130, 133, 134, 137,
        144, 137, 108, 112, 130, 117, 119, 122, 123, 126, 125, 141, 141, 130,
      ],
    );
  });

  test('giữ nguyên ảnh khi kích thước không đổi và không dùng chung bộ nhớ', () {
    final Uint8List src = _pattern(4, 3);
    final Uint8List out = resizeRgbBilinear(src, 4, 3, 4, 3);
    expect(out, src);
    expect(identical(out, src), isFalse);
  });

  test('báo lỗi khi mảng điểm ảnh không khớp kích thước', () {
    expect(() => resizeRgbBilinear(Uint8List(10), 4, 3, 2, 2), throwsArgumentError);
  });
}
