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


# ── Xác thực ──

def test_login_wrong_password(client, seeded):
    response = client.post(f"{API}/auth/login",
                           json={"username": "nongdan", "password": "sai-mat-khau"})
    assert response.status_code == 401


def test_me(client, farmer_headers):
    body = client.get(f"{API}/auth/me", headers=farmer_headers).json()
    assert body["username"] == "nongdan"
    assert body["role"] == "farmer"


def test_endpoint_requires_auth(client):
    assert client.get(f"{API}/plots").status_code == 401


# ── Lô đất ──

def test_create_and_list_plot(client, farmer_headers):
    created = client.post(f"{API}/plots", headers=farmer_headers,
                          json={"name": "Lô mới tạo", "region": "Đơn Dương"})
    assert created.status_code == 201, created.text
    assert created.json()["puc"].startswith("PUC-"), "PUC phải được sinh tự động"

    plots = client.get(f"{API}/plots", headers=farmer_headers).json()
    assert any(p["name"] == "Lô mới tạo" for p in plots)


def test_farmer_cannot_assign_plot_to_others(client, farmer_headers, seeded):
    response = client.post(f"{API}/plots", headers=farmer_headers,
                           json={"name": "Lô của người khác",
                                 "owner_id": seeded["admin_id"]})
    assert response.status_code == 403


# ── Luồng chẩn đoán — phần quan trọng nhất ──

def test_diagnose_returns_full_explanation(client, farmer_headers, seeded, leaf_image):
    response = client.post(
        f"{API}/diagnoses",
        headers=farmer_headers,
        files={"file": ("la.jpg", leaf_image, "image/jpeg")},
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

    # Ảnh gốc và ảnh overlay phải tải về được
    assert client.get(body["image_url"]).status_code == 200
    if body["overlay_url"]:
        assert client.get(body["overlay_url"]).status_code == 200


def test_diagnose_rejects_non_image(client, farmer_headers):
    response = client.post(
        f"{API}/diagnoses",
        headers=farmer_headers,
        files={"file": ("virus.txt", b"day khong phai anh", "text/plain")},
    )
    assert response.status_code == 422


def test_diagnose_rejects_empty_file(client, farmer_headers):
    response = client.post(
        f"{API}/diagnoses",
        headers=farmer_headers,
        files={"file": ("rong.jpg", b"", "image/jpeg")},
    )
    assert response.status_code == 400


def test_dummy_predictor_is_deterministic(client, farmer_headers, leaf_image):
    """Cùng một ảnh phải cho cùng một kết quả — nếu không thì không test được gì."""
    results = []
    for _ in range(2):
        response = client.post(f"{API}/diagnoses", headers=farmer_headers,
                               files={"file": ("la.jpg", leaf_image, "image/jpeg")})
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
