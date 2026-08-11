"""Tạo bảng trong cơ sở dữ liệu.

Chạy:
    cd backend
    python -m app.db.init_db

Dùng ``create_all`` cho nhanh trong giai đoạn phát triển. Khi cấu trúc bảng đã
ổn định và cần giữ dữ liệu qua các lần thay đổi, chuyển sang Alembic:

    alembic revision --autogenerate -m "mo ta thay doi"
    alembic upgrade head
"""

from __future__ import annotations

import logging

from app.db.session import Base, engine

# Import để Base.metadata biết đủ các bảng — không được bỏ dòng này
from app import models  # noqa: F401

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def init_db(drop_first: bool = False) -> None:
    if drop_first:
        logger.warning("Đang XOÁ toàn bộ bảng hiện có...")
        Base.metadata.drop_all(bind=engine)

    Base.metadata.create_all(bind=engine)
    logger.info("Đã tạo xong các bảng: %s", ", ".join(sorted(Base.metadata.tables)))


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Tạo bảng cho cơ sở dữ liệu")
    ap.add_argument("--drop", action="store_true",
                    help="XOÁ hết bảng cũ trước khi tạo lại (mất toàn bộ dữ liệu)")
    args = ap.parse_args()

    if args.drop:
        answer = input("Thao tác này xoá TOÀN BỘ dữ liệu. Gõ 'xoa' để xác nhận: ")
        if answer.strip().lower() != "xoa":
            raise SystemExit("Đã huỷ.")

    init_db(drop_first=args.drop)
