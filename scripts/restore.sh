#!/usr/bin/env bash
# Khôi phục một bản sao lưu do backup.sh tạo ra (#40/BE-06).
#
# Chạy bằng Git Bash.
#
#   ./scripts/restore.sh scripts/backups/<ngày giờ>
#
# ⚠️ GHI ĐÈ TOÀN BỘ: xoá sạch schema `public` hiện có trong CSDL rồi nạp lại
# từ bản dump, và xoá backend/storage/ hiện có trước khi giải nén bản cũ vào.
# Chỉ dùng khi thật sự muốn quay về đúng trạng thái của bản sao lưu.
set -euo pipefail

cd "$(dirname "$0")/.."  # về gốc repo

DB_CONTAINER="plantdx-db"
BACKUP_DIR="${1:-}"

if [ -z "$BACKUP_DIR" ]; then
  echo "Dùng: $0 <đường-dẫn-thư-mục-backup>" >&2
  echo "Ví dụ: $0 scripts/backups/20260918-220000" >&2
  exit 1
fi

if [ ! -f "$BACKUP_DIR/database.sql" ] || [ ! -f "$BACKUP_DIR/storage.tar.gz" ]; then
  echo "Không thấy database.sql hoặc storage.tar.gz trong '$BACKUP_DIR' — đúng thư mục backup.sh sinh ra chưa?" >&2
  exit 1
fi

if ! docker inspect "$DB_CONTAINER" >/dev/null 2>&1; then
  echo "Không thấy container '$DB_CONTAINER' — chạy 'docker compose up -d db' trước." >&2
  exit 1
fi

read -r -p "Sẽ XOÁ SẠCH dữ liệu hiện tại trong CSDL + backend/storage/ rồi nạp lại từ '$BACKUP_DIR'. Gõ 'yes' để tiếp tục: " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
  echo "Huỷ."
  exit 1
fi

echo "==> Xoá schema public hiện có, tạo lại rỗng..."
docker exec -i "$DB_CONTAINER" psql -U plantdx -d plantdx -v ON_ERROR_STOP=1 \
  -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

echo "==> Nạp lại từ database.sql..."
docker exec -i "$DB_CONTAINER" psql -U plantdx -d plantdx -v ON_ERROR_STOP=1 < "$BACKUP_DIR/database.sql"

echo "==> Khôi phục backend/storage/..."
rm -rf backend/storage
tar -xzf "$BACKUP_DIR/storage.tar.gz" -C backend

echo "==> Xong. Khởi động lại backend nếu đang chạy (docker compose restart backend)."
