"""Thuốc gợi ý, gán thuốc theo bệnh, và video hướng dẫn — chỉ quản trị ghi được."""

from __future__ import annotations

from app.core.config import settings

API = settings.API_V1_PREFIX


def _create_medicine(client, admin_headers, name="Thuốc gốc đồng") -> dict:
    response = client.post(
        f"{API}/medicines",
        headers=admin_headers,
        json={"name": name, "group": "Copper", "purchase_url": "https://example.vn/thuoc"},
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_farmer_cannot_manage_medicines(client, farmer_headers):
    assert client.get(f"{API}/medicines", headers=farmer_headers).status_code == 403
    assert client.post(
        f"{API}/medicines", headers=farmer_headers, json={"name": "X"}
    ).status_code == 403


def test_create_update_delete_medicine(client, admin_headers):
    medicine = _create_medicine(client, admin_headers, "Thuốc test CRUD")
    medicine_id = medicine["id"]

    listed = client.get(f"{API}/medicines", headers=admin_headers).json()
    assert any(m["id"] == medicine_id for m in listed)

    updated = client.patch(
        f"{API}/medicines/{medicine_id}", headers=admin_headers, json={"group": "Mancozeb"}
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["group"] == "Mancozeb"
    assert updated.json()["name"] == "Thuốc test CRUD"  # field không gửi thì giữ nguyên

    deleted = client.delete(f"{API}/medicines/{medicine_id}", headers=admin_headers)
    assert deleted.status_code == 204

    assert client.patch(
        f"{API}/medicines/{medicine_id}", headers=admin_headers, json={"group": "X"}
    ).status_code == 404


def test_assign_medicine_to_disease_and_list_by_disease(client, admin_headers):
    medicine = _create_medicine(client, admin_headers, "Thuốc gán bệnh")

    created = client.post(
        f"{API}/medicines/assignments",
        headers=admin_headers,
        json={
            "disease_key": "late_blight",
            "medicine_id": medicine["id"],
            "note": "Phun 2 lần/tuần",
        },
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["medicine_name"] == "Thuốc gán bệnh"

    listed = client.get(
        f"{API}/medicines/assignments", headers=admin_headers,
        params={"disease_key": "late_blight"},
    )
    assert listed.status_code == 200
    assert any(a["id"] == body["id"] for a in listed.json())

    # Đã gán thật thì bệnh phải trả về thuốc này ở endpoint công khai
    public = client.get(f"{API}/diseases/late_blight").json()
    assert any(p["name"] == "Thuốc gán bệnh" for p in public["products"])

    removed = client.delete(f"{API}/medicines/assignments/{body['id']}", headers=admin_headers)
    assert removed.status_code == 204


def test_assign_medicine_rejects_unknown_disease_key(client, admin_headers):
    medicine = _create_medicine(client, admin_headers, "Thuốc bệnh lạ")
    response = client.post(
        f"{API}/medicines/assignments",
        headers=admin_headers,
        json={"disease_key": "khong_ton_tai", "medicine_id": medicine["id"]},
    )
    assert response.status_code == 404


def test_upsert_and_delete_disease_guide(client, admin_headers):
    empty = client.get(f"{API}/medicines/guides/healthy", headers=admin_headers)
    assert empty.status_code == 200
    assert empty.json() is None

    saved = client.put(
        f"{API}/medicines/guides/healthy",
        headers=admin_headers,
        json={"video_url": "https://www.youtube.com/watch?v=demo123"},
    )
    assert saved.status_code == 200, saved.text
    assert saved.json()["video_url"] == "https://www.youtube.com/watch?v=demo123"

    # Đặt lại là ghi đè, không tạo bản ghi mới
    overwritten = client.put(
        f"{API}/medicines/guides/healthy",
        headers=admin_headers,
        json={"video_url": "https://www.youtube.com/watch?v=demo456"},
    )
    assert overwritten.status_code == 200
    assert overwritten.json()["video_url"] == "https://www.youtube.com/watch?v=demo456"

    public = client.get(f"{API}/diseases/healthy").json()
    assert public["video_url"] == "https://www.youtube.com/watch?v=demo456"

    deleted = client.delete(f"{API}/medicines/guides/healthy", headers=admin_headers)
    assert deleted.status_code == 204
    assert client.delete(f"{API}/medicines/guides/healthy", headers=admin_headers).status_code == 404
