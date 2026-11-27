import 'package:agrixai_farmer/services/offline_aggregation.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('trung bình cộng theo từng bệnh trên các ảnh được cho qua', () {
    final List<double> average = averageProbabilities(<List<double>>[
      <double>[0.9, 0.1, 0.0],
      <double>[0.2, 0.5, 0.3],
      <double>[0.1, 0.6, 0.3],
    ]);
    expect(average[0], closeTo(0.4, 1e-9));
    expect(average[1], closeTo(0.4, 1e-9));
    expect(average[2], closeTo(0.2, 1e-9));
  });

  test('bệnh thắng theo trung bình có thể khác bệnh được nhiều ảnh chọn nhất', () {
    final List<double> average = averageProbabilities(<List<double>>[
      <double>[0.98, 0.02],
      <double>[0.40, 0.60],
      <double>[0.40, 0.60],
    ]);
    expect(argmax(average), 0);
  });

  test('ảnh đại diện ưu tiên ảnh cũng chọn bệnh thắng cuộc', () {
    final int index = representativeIndex(<List<double>>[
      <double>[0.45, 0.55, 0.00], // xác suất lớp 0 cao hơn nhưng chọn lớp 1
      <double>[0.40, 0.30, 0.30], // chọn lớp 0
    ], 0);
    expect(index, 1);
  });

  test('trong các ảnh cùng chọn bệnh thắng cuộc, lấy ảnh có xác suất cao nhất', () {
    final int index = representativeIndex(<List<double>>[
      <double>[0.6, 0.4],
      <double>[0.9, 0.1],
      <double>[0.7, 0.3],
    ], 0);
    expect(index, 1);
  });

  test('không ảnh nào chọn bệnh thắng cuộc thì lấy xác suất cao nhất', () {
    final int index = representativeIndex(<List<double>>[
      <double>[0.55, 0.40, 0.05],
      <double>[0.00, 0.45, 0.55],
    ], 1);
    expect(index, 1);
  });

  test('không lấy trung bình trên danh sách rỗng', () {
    expect(() => averageProbabilities(<List<double>>[]), throwsArgumentError);
  });
}
