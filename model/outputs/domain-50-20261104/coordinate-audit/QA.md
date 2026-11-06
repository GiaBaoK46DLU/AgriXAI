# Kiểm tra bằng mắt ánh xạ toạ độ — 04/11/2026

Đã mở và xem đủ 12 ảnh `pv-01`…`pv-06`, `pd-01`…`pd-06` trong phiên thực hiện.
Khung cắt, ảnh đưa vào mô hình và CAM đặt lại có cùng vị trí; vùng ngoài khung
cắt bằng 0. Không phát hiện lỗi kéo CAM của ảnh cắt phủ toàn ảnh gốc.

Đây là kiểm tra toạ độ, **không phải xác nhận phân vùng lá đúng**. Có hạn chế thật:

- `pd-01`, `pd-03`…`pd-05` vẫn có thể giữ cả nhánh/nhiều lá nối nhau.
- `pd-02` bỏ sót một phần mép lá khô ít bão hoà màu.
- Mặt nạ màu không phải ground truth vết bệnh và không được dùng để báo IoU
  phân vùng bệnh như thể đã có chuyên gia gán nhãn.

Vì vậy phải quyết định bật/tắt bằng phép đo validation/test, đồng thời giữ chế độ
quay về ảnh đầy đủ khi không tách được vùng đủ rõ. Không kết luận chất lượng
phân loại tăng chỉ từ 12 ảnh minh hoạ này.
