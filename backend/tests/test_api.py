"""Kiểm thử luồng chính từ đầu tới cuối.

Chạy:
    cd backend
    pytest -v

Bộ test này bảo vệ đúng cái quan trọng nhất: luồng "gửi ảnh -> nhận kết quả kèm
giải thích XAI" luôn chạy được, và nông dân không bao giờ nhìn thấy dữ liệu của
nông dân khác.
"""

from __future__ import annotations

from app.core.config import settings

API = settings.API_V1_PREFIX


# ── Hệ thống ──

def test_health(client):
    body = client.get("/health").json()
    assert body["status"] == "ok"
    # Khi test luôn phải là mô hình giả, không được vô tình nạp checkpoint thật
    assert body["using_real_model"] is False


def test_disease_catalog(client):
    diseases = client.get(f"{API}/diseases").json()
    assert len(diseases) == 10, "Phải đủ 10 lớp bệnh cà chua"

    keys = {d["key"] for d in diseases}
    assert "healthy" in keys
    assert "early_blight" in keys

    detail = client.get(f"{API}/diseases/late_blight").json()
    assert detail["name_vi"] == "Mốc sương muộn"
    assert detail["treatments"], "Bệnh nào cũng phải có gợi ý xử lý"


def test_unknown_disease_returns_404(client):
    assert client.get(f"{API}/diseases/khong-co-benh-nay").status_code == 404


def test_disease_without_medicines_has_empty_products(client):
    """Bệnh chưa gán thuốc nào (CSDL test không seed) vẫn trả về mảng rỗng, không lỗi."""
    detail = client.get(f"{API}/diseases/late_blight").json()
    assert detail["products"] == []
    assert detail["video_url"] is None


def test_disease_products_come_from_database(client):
    """Thuốc gợi ý lấy từ CSDL (medicines/disease_medicines), không phải từ JSON."""
    from app.db.session import SessionLocal
    from app.models.medicine import DiseaseGuide, DiseaseMedicine, Medicine

    with SessionLocal() as db:
        medicine = Medicine(name="Thuốc thử nghiệm", group="Nhóm thử",
                            purchase_url="https://example.com/thuoc")
        db.add(medicine)
        db.flush()
        db.add(DiseaseMedicine(disease_key="early_blight", medicine_id=medicine.id,
                               note="Ghi chú thử nghiệm"))
        db.add(DiseaseGuide(disease_key="early_blight", video_url="https://youtube.com/watch?v=test"))
        db.commit()

    detail = client.get(f"{API}/diseases/early_blight").json()
    assert detail["products"] == [{
        "name": "Thuốc thử nghiệm",
        "group": "Nhóm thử",
        "purchase_url": "https://example.com/thuoc",
        "note": "Ghi chú thử nghiệm",
    }]
    assert detail["video_url"] == "https://youtube.com/watch?v=test"


# ── Xác thực ──

def test_login_wrong_password(client, seeded):
    response = client.post(f"{API}/auth/login",
                           json={"username": "nongdan", "password": "sai-mat-khau"})
    assert response.status_code == 401


def test_register_creates_farmer_and_logs_in(client, seeded):
    response = client.post(f"{API}/auth/register", json={
        "username": "nongdan_moi",
        "password": "mkkhachang",
        "full_name": "Nông dân Mới",
        "email": "nongdan.moi@example.com",
    })
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["user"]["role"] == "farmer"  # tự đăng ký không được chọn vai trò
    assert body["user"]["email"] == "nongdan.moi@example.com"
    assert "access_token" in body  # đăng ký xong đăng nhập luôn


def test_login_response_serializes_stored_email(client):
    """Hồi quy đúng sự cố thật đã gặp: seed ban đầu gán email `@agrixai.local`
    trực tiếp bằng SQLAlchemy (bỏ qua validate của `RegisterRequest`, y hệt
    cách `app/seed.py` tạo user) — `.local` là tên miền dành riêng (RFC 6762),
    `EmailStr` từ chối. Khi đó `UserOut.email` còn dùng `EmailStr` nên MỌI
    lần đọc lại user này (`/auth/login`, `/auth/me`...) đều sập
    `ResponseValidationError` (500), dù giá trị đã nằm sẵn trong CSDL từ
    trước, không phải input mới. Fixture `seeded` không gán email nên không
    tự bắt được lỗi này — phải seed trực tiếp như dưới đây mới tái hiện đúng.
    Nếu `UserOut.email` bị đổi ngược lại thành `EmailStr`, test này sẽ đỏ."""
    from app.core.security import hash_password
    from app.db.session import SessionLocal
    from app.models.user import User, UserRole

    with SessionLocal() as db:
        db.add(User(username="co_san_email", full_name="Có Sẵn Email",
                    role=UserRole.FARMER, email="legacy@agrixai.local",
                    hashed_password=hash_password("mkkhachang")))
        db.commit()

    response = client.post(f"{API}/auth/login",
                           json={"username": "co_san_email", "password": "mkkhachang"})
    assert response.status_code == 200, response.text
    assert response.json()["user"]["email"] == "legacy@agrixai.local"


def test_register_rejects_duplicate_username(client, seeded):
    response = client.post(f"{API}/auth/register", json={
        "username": "nongdan",  # đã tồn tại từ fixture seeded
        "password": "mkkhachang",
        "full_name": "Trùng tên",
        "email": "trung.ten@example.com",
    })
    assert response.status_code == 409


def test_register_rejects_duplicate_email(client, seeded):
    client.post(f"{API}/auth/register", json={
        "username": "co_email_truoc",
        "password": "mkkhachang",
        "full_name": "Có Email Trước",
        "email": "email.trung@example.com",
    })
    response = client.post(f"{API}/auth/register", json={
        "username": "co_email_sau",
        "password": "mkkhachang",
        "full_name": "Có Email Sau",
        "email": "email.trung@example.com",
    })
    assert response.status_code == 409


def test_me(client, farmer_headers):
    body = client.get(f"{API}/auth/me", headers=farmer_headers).json()
    assert body["username"] == "nongdan"
    assert body["role"] == "farmer"


def test_endpoint_requires_auth(client):
    assert client.get(f"{API}/plots").status_code == 401


def test_update_me_changes_name_and_phone(client, farmer_headers):
    response = client.patch(f"{API}/auth/me", headers=farmer_headers,
                            json={"full_name": "Nông dân Đã Sửa", "phone": "0909123456"})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["full_name"] == "Nông dân Đã Sửa"
    assert body["phone"] == "0909123456"

    again = client.get(f"{API}/auth/me", headers=farmer_headers).json()
    assert again["full_name"] == "Nông dân Đã Sửa"


def test_update_me_ignores_password_field(client, farmer_headers):
    """Đổi mật khẩu phải qua `/auth/change-password` — `PATCH /auth/me` bỏ qua
    trường `password` dù `UserUpdate` (dùng chung với admin) vẫn khai báo nó."""
    client.patch(f"{API}/auth/me", headers=farmer_headers,
                json={"password": "mat-khau-moi-123"})
    response = client.post(f"{API}/auth/login",
                           json={"username": "nongdan", "password": "nongdan123"})
    assert response.status_code == 200, "Mật khẩu cũ vẫn phải còn dùng được"


def test_change_password_requires_correct_current_password(client, farmer_headers):
    response = client.post(f"{API}/auth/change-password", headers=farmer_headers,
                           json={"current_password": "sai-mat-khau", "new_password": "mkkhachang"})
    assert response.status_code == 401


def test_change_password_succeeds_then_old_password_stops_working(client, farmer_headers):
    response = client.post(f"{API}/auth/change-password", headers=farmer_headers,
                           json={"current_password": "nongdan123", "new_password": "mkkhachang"})
    assert response.status_code == 200, response.text

    old = client.post(f"{API}/auth/login",
                      json={"username": "nongdan", "password": "nongdan123"})
    assert old.status_code == 401

    new = client.post(f"{API}/auth/login",
                      json={"username": "nongdan", "password": "mkkhachang"})
    assert new.status_code == 200


# ── Lô đất ──
#
# Chốt 30/09/2026: chỉ quản trị tạo/xoá lô đất, gán thẳng cho một nông dân.
# Nông dân chỉ nhận lô (tự xuất hiện trong danh sách) và sửa cây trồng/trạng
# thái/ghi chú — không tự tạo, không xoá, không sửa tên/PUC/khu vực/diện tích.

def test_admin_creates_and_assigns_plot(client, admin_headers, farmer_headers, seeded):
    created = client.post(f"{API}/plots", headers=admin_headers,
                          json={"name": "Lô mới tạo", "region": "Đơn Dương",
                                "owner_id": seeded["farmer_id"]})
    assert created.status_code == 201, created.text
    assert created.json()["puc"].startswith("PUC-"), "PUC phải được sinh tự động"

    plots = client.get(f"{API}/plots", headers=farmer_headers).json()
    assert any(p["name"] == "Lô mới tạo" for p in plots)


def test_admin_create_plot_requires_owner(client, admin_headers):
    response = client.post(f"{API}/plots", headers=admin_headers,
                           json={"name": "Lô chưa gán ai"})
    assert response.status_code == 422


def test_farmer_cannot_create_plot(client, farmer_headers, seeded):
    response = client.post(f"{API}/plots", headers=farmer_headers,
                           json={"name": "Lô tự tạo", "owner_id": seeded["farmer_id"]})
    assert response.status_code == 403


def test_farmer_cannot_delete_plot(client, farmer_headers, seeded):
    response = client.delete(f"{API}/plots/{seeded['plot_id']}", headers=farmer_headers)
    assert response.status_code == 403


def test_farmer_can_update_crop_but_not_name(client, farmer_headers, seeded):
    ok = client.patch(f"{API}/plots/{seeded['plot_id']}", headers=farmer_headers,
                      json={"crop": "Cà chua bi", "status": "fallow", "note": "Nghỉ vụ"})
    assert ok.status_code == 200, ok.text
    assert ok.json()["crop"] == "Cà chua bi"

    blocked = client.patch(f"{API}/plots/{seeded['plot_id']}", headers=farmer_headers,
                           json={"name": "Đổi tên lô"})
    assert blocked.status_code == 403


# ── Luồng chẩn đoán — phần quan trọng nhất ──

def _files(image: bytes, count: int = 3) -> list[tuple[str, tuple[str, bytes, str]]]:
    """Danh sách `files` dạng httpx cho `count` bản sao của cùng một ảnh —
    đủ để test luồng đa ảnh mà không cần sinh nhiều ảnh giả khác nhau."""
    return [("files", (f"la{i}.jpg", image, "image/jpeg")) for i in range(count)]


def test_diagnose_returns_full_explanation(client, farmer_headers, seeded, leaf_image):
    response = client.post(
        f"{API}/diagnoses",
        headers=farmer_headers,
        files=_files(leaf_image),
        data={"plot_id": str(seeded["plot_id"]), "note": "Chụp sáng nay"},
    )
    assert response.status_code == 201, response.text
    body = response.json()

    # Kết quả phân loại
    assert body["disease_key"]
    assert 0.0 <= body["confidence"] <= 1.0
    assert body["disease_name"]

    # Phần XAI — lý do đề tài tồn tại
    assert body["explanation"], "Phải luôn có câu giải thích bằng tiếng Việt"
    assert body["severity"] in {"none", "mild", "moderate", "severe"}
    assert 0.0 <= body["affected_ratio"] <= 1.0

    # Ảnh
    assert body["image_url"].startswith("/storage/uploads/")

    # Thông tin tra cứu kèm theo
    assert body["disease"] is not None
    assert body["top_predictions"], "Phải có top-3 để người dùng thấy mô hình phân vân gì"
    assert body["disclaimer"], "Phải luôn kèm khuyến cáo"

    # Kết quả riêng từng ảnh — dùng vẽ carousel khoanh vùng ở mobile
    assert len(body["images"]) == 3
    for image in body["images"]:
        assert image["disease_key"]
        assert image["image_url"].startswith("/storage/uploads/")

    # Ảnh gốc và ảnh overlay phải tải về được
    assert client.get(body["image_url"]).status_code == 200
    if body["overlay_url"]:
        assert client.get(body["overlay_url"]).status_code == 200


def test_diagnose_without_save_does_not_persist(client, farmer_headers, seeded, leaf_image):
    """`save=false` (nút chụp ảnh chung, không qua lô đất cụ thể) phải trả về
    kết quả đầy đủ như bình thường nhưng KHÔNG ghi gì vào CSDL — xem CLAUDE.md
    mục quản lý lô đất."""
    before = client.get(f"{API}/diagnoses", headers=farmer_headers).json()["total"]

    response = client.post(
        f"{API}/diagnoses",
        headers=farmer_headers,
        files=_files(leaf_image),
        data={"plot_id": str(seeded["plot_id"]), "save": "false"},
    )
    assert response.status_code == 201, response.text
    body = response.json()

    assert body["disease_key"]
    assert body["explanation"]
    # Không lưu nên không thể/không nên gắn lô đất, dù có lỡ gửi plot_id lên.
    assert body["plot_id"] is None

    after = client.get(f"{API}/diagnoses", headers=farmer_headers).json()["total"]
    assert after == before, "save=false không được tạo bản ghi CSDL nào"


def test_diagnose_rejects_too_few_images(client, farmer_headers, leaf_image):
    response = client.post(
        f"{API}/diagnoses", headers=farmer_headers, files=_files(leaf_image, count=2),
    )
    assert response.status_code == 400


def test_diagnose_rejects_too_many_images(client, farmer_headers, leaf_image):
    response = client.post(
        f"{API}/diagnoses", headers=farmer_headers, files=_files(leaf_image, count=6),
    )
    assert response.status_code == 400


def test_diagnose_rejects_non_image(client, farmer_headers):
    response = client.post(
        f"{API}/diagnoses",
        headers=farmer_headers,
        files=[
            ("files", ("virus1.txt", b"day khong phai anh", "text/plain")),
            ("files", ("virus2.txt", b"day khong phai anh", "text/plain")),
            ("files", ("virus3.txt", b"day khong phai anh", "text/plain")),
        ],
    )
    assert response.status_code == 422


def test_diagnose_rejects_empty_file(client, farmer_headers, leaf_image):
    response = client.post(
        f"{API}/diagnoses",
        headers=farmer_headers,
        files=[
            ("files", ("la1.jpg", leaf_image, "image/jpeg")),
            ("files", ("la2.jpg", leaf_image, "image/jpeg")),
            ("files", ("rong.jpg", b"", "image/jpeg")),
        ],
    )
    assert response.status_code == 400


def test_dummy_predictor_is_deterministic(client, farmer_headers, leaf_image):
    """Cùng một lô ảnh phải cho cùng một kết quả — nếu không thì không test được gì."""
    results = []
    for _ in range(2):
        response = client.post(f"{API}/diagnoses", headers=farmer_headers, files=_files(leaf_image))
        results.append(response.json()["disease_key"])
    assert results[0] == results[1]


def test_history_is_paginated(client, farmer_headers):
    body = client.get(f"{API}/diagnoses?page=1&page_size=5", headers=farmer_headers).json()
    assert body["page"] == 1
    assert body["page_size"] == 5
    assert body["total"] >= 1
    assert len(body["items"]) <= 5


# ── Phân quyền ──

def test_farmer_cannot_open_admin_dashboard(client, farmer_headers):
    assert client.get(f"{API}/stats/dashboard", headers=farmer_headers).status_code == 403


def test_admin_dashboard(client, admin_headers):
    body = client.get(f"{API}/stats/dashboard", headers=admin_headers).json()
    assert body["overview"]["total_diagnoses"] >= 1
    assert body["using_real_model"] is False
    assert isinstance(body["timeseries"], list)


def test_farmer_cannot_manage_users(client, farmer_headers):
    assert client.get(f"{API}/users", headers=farmer_headers).status_code == 403


def test_admin_sees_all_diagnoses(client, admin_headers, farmer_headers):
    """Quản trị thấy được cả bản ghi của nông dân, nông dân thì không thấy ngược lại."""
    admin_total = client.get(f"{API}/diagnoses", headers=admin_headers).json()["total"]
    farmer_total = client.get(f"{API}/diagnoses", headers=farmer_headers).json()["total"]
    assert admin_total >= farmer_total
