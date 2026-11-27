import 'dart:math' as math;
import 'dart:typed_data';

/// Thu phóng ảnh RGB bằng bilinear CÓ khử răng cưa, chép từng bước từ thuật
/// toán resample của Pillow (số học dấu phẩy tĩnh 22 bit, quét ngang trước,
/// dọc sau). Kết quả trùng từng byte với `Image.resize(..., Image.BILINEAR)`.
///
/// Vì sao không dùng `img.copyResize(..., Interpolation.linear)`: máy chủ tiền
/// xử lý ảnh bằng `build_infer_transform` (torchvision `Resize` trên ảnh PIL,
/// tức bilinear của Pillow). Nội suy linear của gói `image` chỉ lấy 4 điểm ảnh
/// lân cận, nên khi thu ảnh 1280 px về 224 px sẽ bị răng cưa và tensor đầu vào
/// lệch so với máy chủ. Đo trên 68 ảnh PlantDoc, bộ lọc ảnh đầu vào đổi quyết
/// định ở 3 ảnh khi dùng cách cũ, và 0 ảnh khi dùng cách này.
///
/// [src] là mảng điểm ảnh RGB liền nhau (3 byte mỗi điểm, theo từng hàng).
Uint8List resizeRgbBilinear(
  Uint8List src,
  int srcWidth,
  int srcHeight,
  int dstWidth,
  int dstHeight,
) {
  if (src.length != srcWidth * srcHeight * 3) {
    throw ArgumentError('Mảng điểm ảnh không khớp kích thước $srcWidth×$srcHeight');
  }
  Uint8List current = src;
  if (dstWidth != srcWidth) {
    current = _horizontalPass(current, srcWidth, srcHeight, dstWidth);
  }
  if (dstHeight != srcHeight) {
    current = _verticalPass(current, dstWidth, srcHeight, dstHeight);
  }
  return identical(current, src) ? Uint8List.fromList(src) : current;
}

const int _precisionBits = 32 - 8 - 2;
const int _half = 1 << (_precisionBits - 1);

/// Trọng số của một trục: điểm ảnh đích thứ `i` là tổng có trọng số của
/// `count[i]` điểm ảnh nguồn liên tiếp bắt đầu từ `first[i]`.
class _AxisWeights {
  _AxisWeights(this.first, this.count, this.weights, this.kernelSize);

  final Int32List first;
  final Int32List count;
  final Int32List weights;
  final int kernelSize;
}

_AxisWeights _axisWeights(int inSize, int outSize) {
  final double scale = inSize / outSize;
  // Khi thu nhỏ, cửa sổ lọc nở theo tỉ lệ — đây chính là phần khử răng cưa.
  final double filterScale = math.max(scale, 1.0);
  final double support = filterScale; // bán kính của bộ lọc bilinear là 1.0
  final int kernelSize = support.ceil() * 2 + 1;

  final Int32List first = Int32List(outSize);
  final Int32List count = Int32List(outSize);
  final Int32List weights = Int32List(outSize * kernelSize);
  final Float64List raw = Float64List(kernelSize);
  final double inverse = 1.0 / filterScale;

  for (int o = 0; o < outSize; o++) {
    final double center = (o + 0.5) * scale;
    final int start = math.max((center - support + 0.5).toInt(), 0);
    final int n = math.min((center + support + 0.5).toInt(), inSize) - start;
    double total = 0;
    for (int i = 0; i < n; i++) {
      final double distance = ((i + start - center + 0.5) * inverse).abs();
      final double w = distance < 1.0 ? 1.0 - distance : 0.0;
      raw[i] = w;
      total += w;
    }
    for (int i = 0; i < n; i++) {
      final double normalized = total != 0 ? raw[i] / total : 0.0;
      weights[o * kernelSize + i] = (0.5 + normalized * (1 << _precisionBits)).toInt();
    }
    first[o] = start;
    count[o] = n;
  }
  return _AxisWeights(first, count, weights, kernelSize);
}

int _clip8(int value) {
  final int v = value >> _precisionBits;
  return v < 0 ? 0 : (v > 255 ? 255 : v);
}

Uint8List _horizontalPass(Uint8List src, int width, int height, int outWidth) {
  final _AxisWeights axis = _axisWeights(width, outWidth);
  final Uint8List out = Uint8List(outWidth * height * 3);
  for (int y = 0; y < height; y++) {
    for (int x = 0; x < outWidth; x++) {
      final int start = axis.first[x];
      final int n = axis.count[x];
      final int offset = x * axis.kernelSize;
      int r = _half, g = _half, b = _half;
      int p = (y * width + start) * 3;
      for (int i = 0; i < n; i++) {
        final int w = axis.weights[offset + i];
        r += src[p] * w;
        g += src[p + 1] * w;
        b += src[p + 2] * w;
        p += 3;
      }
      final int q = (y * outWidth + x) * 3;
      out[q] = _clip8(r);
      out[q + 1] = _clip8(g);
      out[q + 2] = _clip8(b);
    }
  }
  return out;
}

Uint8List _verticalPass(Uint8List src, int width, int height, int outHeight) {
  final _AxisWeights axis = _axisWeights(height, outHeight);
  final Uint8List out = Uint8List(width * outHeight * 3);
  final int stride = width * 3;
  for (int y = 0; y < outHeight; y++) {
    final int start = axis.first[y];
    final int n = axis.count[y];
    final int offset = y * axis.kernelSize;
    for (int x = 0; x < width; x++) {
      int r = _half, g = _half, b = _half;
      int p = start * stride + x * 3;
      for (int i = 0; i < n; i++) {
        final int w = axis.weights[offset + i];
        r += src[p] * w;
        g += src[p + 1] * w;
        b += src[p + 2] * w;
        p += stride;
      }
      final int q = y * stride + x * 3;
      out[q] = _clip8(r);
      out[q + 1] = _clip8(g);
      out[q + 2] = _clip8(b);
    }
  }
  return out;
}
