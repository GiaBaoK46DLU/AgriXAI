# Thực nghiệm Grad-CAM++ (#98)

Đọc [báo cáo](../../../docx/bao-cao-gradcam-plus-plus.md) để xem công thức, thiết kế,
bảng kết quả, giới hạn và lệnh chạy lại. Mặc định server đã đổi sang Grad-CAM++
ngày 02/11/2026 theo quyết định triển khai; contour ở ngưỡng 0,62 chưa tốt hơn trên
PlantDoc, được giữ nguyên trong báo cáo như một hạn chế.

- `protocol.json`: cấu hình, nguồn mã, checkpoint và 56 ảnh cố định của #17.
- `per-image.json`: kết quả của 2 phương pháp trên mỗi ảnh (112 bản ghi).
- `summary.json`: thống kê theo bộ dữ liệu và chênh lệch có cặp, bootstrap 10.000 lần.
- `maps/*.npz`: hai bản đồ thô và hai bản đồ chuẩn hoá cho từng ảnh.
- `figures/*.png`: ảnh gốc, tham chiếu AI, hai heatmap và hai contour sản phẩm.
- `verification.json`: kết quả đối chiếu tệp đầu ra với mã nguồn, đầu vào và số đo.

Đứng trong `model/`, cài các dependency mô hình và `requirements-xai-validation.txt`,
sau đó kiểm bản đã lưu:

```powershell
$env:DEBUG = 'false'
$env:DATABASE_URL = 'sqlite:///:memory:'
python -m src.evaluation.verify_gradcam_plusplus
```

Chạy mới phải dùng `--out` khác để không ghi đè kết quả đã có.
