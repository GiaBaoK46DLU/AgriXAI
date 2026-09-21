# `scripts/` — Tiện ích vận hành

Các script chạy tay, không thuộc về `model/` hay `backend/` — thường là việc làm một lần hoặc thỉnh thoảng.

## Sao lưu / khôi phục (`backup.sh` / `restore.sh`, #40/BE-06)

Chạy bằng **Git Bash** (không phải PowerShell — dùng cùng shell với phần còn lại của repo).
Yêu cầu container `plantdx-db` đang chạy (`docker compose up -d db`).

```bash
./scripts/backup.sh                              # sao lưu
./scripts/restore.sh scripts/backups/<ngày giờ>  # khôi phục (hỏi xác nhận trước khi ghi đè)
```

Mỗi lần sao lưu ra một thư mục `scripts/backups/<YYYYMMDD-HHMMSS>/` gồm:

- `database.sql` — `pg_dump` toàn bộ CSDL từ container `plantdx-db`
- `storage.tar.gz` — nén `backend/storage/` (ảnh gốc + ảnh khoanh vùng)

`scripts/backups/` nằm **ngoài Git** (chứa dữ liệu người dùng thật) — xem `.gitignore`.

`restore.sh` **xoá sạch** schema `public` hiện có và `backend/storage/` hiện có trước khi
nạp lại từ bản sao lưu — hỏi gõ `yes` để xác nhận trước khi làm, vì đây là thao tác không
thể hoàn tác. Sau khi khôi phục, khởi động lại backend (`docker compose restart backend`)
để SQLAlchemy không giữ kết nối/cache cũ.

Đã thử khôi phục thật một lần (18/09/2026) trên dữ liệu dev đang chạy: sao lưu → xoá →
khôi phục → xác nhận `GET /diagnoses` trả về đúng số bản ghi như trước khi xoá (21/21).

**Hiện đang trống phần còn lại.** Thư mục dựng sẵn cho những thứ dự kiến sẽ cần:

| Sẽ cần | Việc |
|---|---|
| Tải dữ liệu | Tải PlantVillage từ Kaggle, lọc riêng 10 thư mục cà chua, xếp vào `model/data/raw/` |
| Chuẩn bị demo | Dựng sẵn dữ liệu đẹp cho buổi bảo vệ (tài khoản, lô đất, vài ca bệnh tiêu biểu) |
| Đổi tên ảnh thực địa | Chuẩn hoá tên và gán nhãn ảnh tự chụp trước khi đưa vào `model/data/field/` |

Những việc đã có chỗ riêng thì **không** đưa vào đây:

- Chia tập dữ liệu → `model/src/data/prepare.py`
- Tạo bảng CSDL → `backend/app/db/init_db.py`
- Dữ liệu mẫu → `backend/app/seed.py`
