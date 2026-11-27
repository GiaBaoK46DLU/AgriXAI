/// Gộp kết quả của 3–5 ảnh khi chẩn đoán ngoại tuyến.
///
/// Cùng quy tắc với `backend/app/services/diagnosis_service.py`: lấy trung bình
/// cộng xác suất theo từng bệnh trên các ảnh được bộ lọc cho qua, rồi chọn
/// bệnh có trung bình cao nhất. Đây là bản chép tay (khác ngôn ngữ) — sửa một
/// bên phải soát lại bên kia.
library;

/// Chỉ số của phần tử lớn nhất; hoà thì lấy phần tử đứng trước.
int argmax(List<double> values) {
  int best = 0;
  for (int i = 1; i < values.length; i++) {
    if (values[i] > values[best]) best = i;
  }
  return best;
}

/// Trung bình cộng theo từng lớp. [perImage] không được rỗng.
List<double> averageProbabilities(List<List<double>> perImage) {
  if (perImage.isEmpty) {
    throw ArgumentError('Cần ít nhất một ảnh để lấy trung bình');
  }
  final List<double> sum = List<double>.filled(perImage.first.length, 0);
  for (final List<double> probs in perImage) {
    for (int k = 0; k < sum.length; k++) {
      sum[k] += probs[k];
    }
  }
  return <double>[for (final double s in sum) s / perImage.length];
}

/// Ảnh đại diện cho bệnh [target]: ưu tiên những ảnh mà bản thân chúng cũng
/// xếp [target] đứng đầu, trong đó chọn ảnh có xác suất [target] cao nhất.
/// Không có ảnh nào như vậy thì chọn ảnh có xác suất [target] cao nhất.
int representativeIndex(List<List<double>> perImage, int target) {
  int best = 0;
  bool bestAgrees = argmax(perImage[0]) == target;
  for (int i = 1; i < perImage.length; i++) {
    final bool agrees = argmax(perImage[i]) == target;
    final bool better = agrees != bestAgrees
        ? agrees
        : perImage[i][target] > perImage[best][target];
    if (better) {
      best = i;
      bestAgrees = agrees;
    }
  }
  return best;
}
