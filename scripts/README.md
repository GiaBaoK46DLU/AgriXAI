# `scripts/` — Tiện ích vận hành

Các script chạy tay, không thuộc về `model/` hay `backend/` — thường là việc làm một lần hoặc thỉnh thoảng.

**Hiện đang trống.** Thư mục dựng sẵn cho những thứ dự kiến sẽ cần:

| Sẽ cần | Việc |
|---|---|
| Tải dữ liệu | Tải PlantVillage từ Kaggle, lọc riêng 10 thư mục cà chua, xếp vào `model/data/raw/` |
| Sao lưu | Dump PostgreSQL + nén thư mục `backend/storage/` trước khi demo |
| Chuẩn bị demo | Dựng sẵn dữ liệu đẹp cho buổi bảo vệ (tài khoản, lô đất, vài ca bệnh tiêu biểu) |
| Đổi tên ảnh thực địa | Chuẩn hoá tên và gán nhãn ảnh tự chụp trước khi đưa vào `model/data/field/` |

Những việc đã có chỗ riêng thì **không** đưa vào đây:

- Chia tập dữ liệu → `model/src/data/prepare.py`
- Tạo bảng CSDL → `backend/app/db/init_db.py`
- Dữ liệu mẫu → `backend/app/seed.py`
