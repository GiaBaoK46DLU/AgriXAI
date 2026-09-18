#!/usr/bin/env bash
# Sao lưu CSDL PostgreSQL + thư mục ảnh backend/storage/ bằng MỘT lệnh (#40/BE-06).
#
# Chạy bằng Git Bash (không phải PowerShell) — dùng cùng shell với phần còn
# lại của repo. Yêu cầu: container `plantdx-db` đang chạy (docker compose up).
#
#   ./scripts/backup.sh
#
# Ghi ra scripts/backups/<ngày giờ>/{database.sql, storage.tar.gz} — thư mục
# này nằm NGOÀI Git (xem .gitignore), tên có ngày giờ nên không đè bản cũ.
set -euo pipefail

cd "$(dirname "$0")/.."  # về gốc repo, để mọi đường dẫn tương đối bên dưới luôn đúng

DB_CONTAINER="plantdx-db"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
OUT_DIR="scripts/backups/$TIMESTAMP"

if ! docker inspect "$DB_CONTAINER" >/dev/null 2>&1; then
  echo "Không thấy container '$DB_CONTAINER' — chạy 'docker compose up -d db' trước." >&2
  exit 1
fi

mkdir -p "$OUT_DIR"

echo "==> Dump PostgreSQL (container $DB_CONTAINER)..."
docker exec "$DB_CONTAINER" pg_dump -U plantdx plantdx > "$OUT_DIR/database.sql"

echo "==> Nén backend/storage/ (ảnh gốc + ảnh khoanh vùng)..."
tar -czf "$OUT_DIR/storage.tar.gz" -C backend storage

echo "==> Xong: $OUT_DIR"
du -h "$OUT_DIR"/database.sql "$OUT_DIR"/storage.tar.gz 2>/dev/null || true
echo
echo "Khôi phục bằng: ./scripts/restore.sh $OUT_DIR"
