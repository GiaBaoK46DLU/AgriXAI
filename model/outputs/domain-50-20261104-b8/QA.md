# Rà soát kết quả

- Đã xem đủ 12 gallery `evaluation/pv-test-{1..6}.png` và
  `evaluation/pd-test-{1..6}.png`. Cột phải dùng hàm vẽ thật của backend.
- Đã làm rõ nhãn **khung lá ước lượng**: cắt đang tắt, khung đỏ không phải
  khung đầu vào thực tế. `rendering-qa.json` ghi hash trước/sau, xác nhận các
  JSON số liệu không đổi, dự đoán và quyết định chốt khớp khi dựng lại hình.
- Có trường hợp CAM nhìn bằng mắt tập trung trong lá nhưng vẫn bị ẩn vì mask
  màu không rõ (`pd-test-2`, `pd-test-3`, `pd-test-5`), hoặc mặt nạ hụt phần lá
  vàng/nâu (`pd-test-6`). Chốt khá bảo thủ; không kết luận nó dự báo đúng/sai
  của phân loại, và không dùng nó làm mask vết bệnh.
- Đã kiểm 12 ảnh cắt thật trên validation trong
  `../domain-50-20261104/coordinate-audit/`. CAM được đặt lại đúng khung gốc;
  hạn chế tách màu được ghi riêng trong QA của bộ đó.
- Uvicorn HTTP thật trên CPU đã kiểm đăng ký cấp token, loader/default thật,
  lưu/đọc chẩn đoán, tải overlay, trường hợp ẩn vùng và ảnh âm trả 422.
  Chỉ dùng SQLite/storage tạm. Xem `api-http.json` và `api-http-server.log`.
- Docker Engine không chạy trong phiên kiểm tra. Cấu hình Compose đã parse
  bằng `docker compose config --quiet`; không coi đây là kiểm chạy container.

Checkpoint server đóng gói: `model/checkpoints/leaf_disease_domain_adapted.pt`.
Bản gốc vẫn giữ riêng. Sau khi thay checkpoint/YAML cần khởi động lại backend
vì predictor được cache lúc khởi động.
