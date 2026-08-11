"""Thiết lập môi trường kiểm thử.

Kiểm thử chạy trên SQLite tạm và thư mục lưu trữ tạm, không đụng tới CSDL
PostgreSQL hay ảnh thật của môi trường phát triển.

QUAN TRỌNG: phải đặt biến môi trường TRƯỚC khi import bất cứ thứ gì trong
``app``, vì cấu hình và engine được khởi tạo ngay lúc import.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

_TMP = Path(tempfile.mkdtemp(prefix="plantdx-test-"))

os.environ["DATABASE_URL"] = f"sqlite:///{(_TMP / 'test.db').as_posix()}"
os.environ["STORAGE_DIR"] = str(_TMP / "storage")
os.environ["MODEL_CHECKPOINT"] = ""          # luôn dùng DummyPredictor khi test
os.environ["SECRET_KEY"] = "khoa-chi-dung-cho-kiem-thu"
os.environ["DEBUG"] = "false"

from fastapi.testclient import TestClient  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.db.session import Base, engine  # noqa: E402
from app.main import app  # noqa: E402
from app import models  # noqa: F401,E402


@pytest.fixture(scope="session", autouse=True)
def _database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="session")
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(scope="session")
def seeded(_database):
    """Tạo sẵn một quản trị và một nông dân kèm lô đất."""
    from app.core.security import hash_password
    from app.db.session import SessionLocal
    from app.models.plot import Plot
    from app.models.user import User, UserRole

    with SessionLocal() as db:
        admin = User(username="admin", full_name="Quản trị", role=UserRole.ADMIN,
                     hashed_password=hash_password("admin123"))
        farmer = User(username="nongdan", full_name="Nông dân A", role=UserRole.FARMER,
                      hashed_password=hash_password("nongdan123"))
        db.add_all([admin, farmer])
        db.commit()
        db.refresh(farmer)

        plot = Plot(puc="PUC-TEST-0001", name="Lô thử nghiệm", owner_id=farmer.id,
                    region="Đà Lạt", area_m2=1000)
        db.add(plot)
        db.commit()

        return {"admin_id": admin.id, "farmer_id": farmer.id, "plot_id": plot.id}


def _token(client: TestClient, username: str, password: str) -> str:
    response = client.post(f"{settings.API_V1_PREFIX}/auth/login",
                           json={"username": username, "password": password})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


@pytest.fixture(scope="session")
def farmer_headers(client, seeded) -> dict[str, str]:
    return {"Authorization": f"Bearer {_token(client, 'nongdan', 'nongdan123')}"}


@pytest.fixture(scope="session")
def admin_headers(client, seeded) -> dict[str, str]:
    return {"Authorization": f"Bearer {_token(client, 'admin', 'admin123')}"}


@pytest.fixture
def leaf_image() -> bytes:
    """Ảnh giả để gửi lên endpoint chẩn đoán."""
    import io

    from PIL import Image

    image = Image.new("RGB", (400, 400), (40, 120, 50))
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    return buffer.getvalue()
