"""Tạo dữ liệu mẫu để chạy thử và demo.

Chạy:
    cd backend
    python -m app.seed              # tạo tài khoản + lô đất mẫu
    python -m app.seed --diagnoses  # tạo thêm lịch sử chẩn đoán giả để dashboard có số liệu

Script chạy lại được nhiều lần: tài khoản và lô đất đã tồn tại sẽ được bỏ qua
chứ không tạo trùng.
"""

from __future__ import annotations

import io
import logging
import random
from datetime import datetime, timedelta, timezone

from PIL import Image
from sqlalchemy import select

from app.core.security import hash_password
from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.models.plot import Plot, PlotStatus
from app.models.user import User, UserRole
from app.services import diagnosis_service

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

USERS = [
    {"username": "admin", "password": "admin123", "full_name": "Quản trị hệ thống",
     "role": UserRole.ADMIN, "phone": "0900000001"},
    {"username": "nongdan", "password": "nongdan123", "full_name": "Nguyễn Văn Ba",
     "role": UserRole.FARMER, "phone": "0900000002"},
    {"username": "nongdan2", "password": "nongdan123", "full_name": "Trần Thị Bốn",
     "role": UserRole.FARMER, "phone": "0900000003"},
]

PLOTS = [
    {"puc": "PUC-2608-A001", "name": "Vườn cà chua sau nhà", "owner": "nongdan",
     "region": "Đà Lạt, Lâm Đồng", "area_m2": 1200, "status": PlotStatus.ACTIVE},
    {"puc": "PUC-2608-A002", "name": "Nhà kính số 1", "owner": "nongdan",
     "region": "Đà Lạt, Lâm Đồng", "area_m2": 800, "status": PlotStatus.ACTIVE},
    {"puc": "PUC-2608-A003", "name": "Ruộng dưới chân đồi", "owner": "nongdan",
     "region": "Đơn Dương, Lâm Đồng", "area_m2": 2500, "status": PlotStatus.FALLOW},
    {"puc": "PUC-2608-B001", "name": "Vườn nhà bà Bốn", "owner": "nongdan2",
     "region": "Đức Trọng, Lâm Đồng", "area_m2": 1500, "status": PlotStatus.ACTIVE},
]


def seed_users(db) -> dict[str, User]:
    result: dict[str, User] = {}
    for spec in USERS:
        user = db.scalar(select(User).where(User.username == spec["username"]))
        if user is None:
            user = User(
                username=spec["username"],
                full_name=spec["full_name"],
                phone=spec["phone"],
                role=spec["role"],
                hashed_password=hash_password(spec["password"]),
            )
            db.add(user)
            logger.info("  + tài khoản %s / %s", spec["username"], spec["password"])
        else:
            logger.info("  · tài khoản %s đã có, bỏ qua", spec["username"])
        result[spec["username"]] = user
    db.commit()
    for user in result.values():
        db.refresh(user)
    return result


def seed_plots(db, users: dict[str, User]) -> list[Plot]:
    plots = []
    for spec in PLOTS:
        plot = db.scalar(select(Plot).where(Plot.puc == spec["puc"]))
        if plot is None:
            plot = Plot(
                puc=spec["puc"],
                name=spec["name"],
                owner_id=users[spec["owner"]].id,
                region=spec["region"],
                area_m2=spec["area_m2"],
                status=spec["status"],
                crop="tomato",
            )
            db.add(plot)
            logger.info("  + lô đất %s — %s", spec["puc"], spec["name"])
        else:
            logger.info("  · lô đất %s đã có, bỏ qua", spec["puc"])
        plots.append(plot)
    db.commit()
    for plot in plots:
        db.refresh(plot)
    return plots


def _fake_leaf_image(rng: random.Random) -> bytes:
    """Ảnh lá giả — vài mảng màu xanh có đốm nâu, đủ để chạy hết luồng."""
    size = 512
    image = Image.new("RGB", (size, size), (34 + rng.randint(0, 30), 110 + rng.randint(0, 50), 40))
    pixels = image.load()
    for _ in range(rng.randint(3, 8)):
        cx, cy = rng.randint(80, size - 80), rng.randint(80, size - 80)
        radius = rng.randint(20, 60)
        for x in range(max(0, cx - radius), min(size, cx + radius)):
            for y in range(max(0, cy - radius), min(size, cy + radius)):
                if (x - cx) ** 2 + (y - cy) ** 2 <= radius ** 2:
                    pixels[x, y] = (110 + rng.randint(0, 40), 70 + rng.randint(0, 30), 30)

    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    return buffer.getvalue()


def seed_diagnoses(db, users: dict[str, User], plots: list[Plot], count: int = 40) -> None:
    """Tạo lịch sử chẩn đoán giả, rải đều trong 30 ngày gần nhất.

    Mục đích: dashboard và màn hình lịch sử có số liệu để hiển thị ngay từ đầu,
    không phải chụp tay 40 tấm ảnh mới thấy biểu đồ trông ra sao.
    """
    rng = random.Random(42)
    now = datetime.now(timezone.utc)
    active = [p for p in plots if p.status != PlotStatus.ARCHIVED]

    logger.info("  Đang tạo %d bản chẩn đoán mẫu (mỗi bản chạy qua mô hình thật/giả)...", count)
    for i in range(count):
        plot = rng.choice(active)
        record = diagnosis_service.run_diagnosis(
            db,
            user_id=plot.owner_id,
            plot_id=plot.id,
            image_bytes=_fake_leaf_image(rng),
            note=None,
        )
        # Rải ngược thời gian để biểu đồ theo ngày có hình dạng
        record.created_at = now - timedelta(
            days=rng.randint(0, 29), hours=rng.randint(0, 23)
        )
        db.commit()

        if (i + 1) % 10 == 0:
            logger.info("    ... %d/%d", i + 1, count)


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser(description="Tạo dữ liệu mẫu")
    ap.add_argument("--diagnoses", action="store_true",
                    help="Tạo thêm lịch sử chẩn đoán giả")
    ap.add_argument("--count", type=int, default=40)
    args = ap.parse_args()

    logger.info("Tạo bảng nếu chưa có...")
    init_db()

    with SessionLocal() as db:
        logger.info("\nTài khoản:")
        users = seed_users(db)

        logger.info("\nLô đất:")
        plots = seed_plots(db, users)

        if args.diagnoses:
            logger.info("\nLịch sử chẩn đoán:")
            seed_diagnoses(db, users, plots, args.count)

    logger.info("\nXong. Đăng nhập thử với:")
    for spec in USERS:
        logger.info("  %-10s / %-12s (%s)", spec["username"], spec["password"], spec["role"])


if __name__ == "__main__":
    main()
