"""Diễn đàn nông dân — bài viết gắn với bệnh, có thể đính kèm một lần chẩn đoán."""

from __future__ import annotations

from app.core.config import settings

API = settings.API_V1_PREFIX


def _files(image: bytes, count: int = 3) -> list[tuple[str, tuple[str, bytes, str]]]:
    return [("files", (f"la{i}.jpg", image, "image/jpeg")) for i in range(count)]


def _make_diagnosis(client, headers, seeded, leaf_image) -> dict:
    response = client.post(
        f"{API}/diagnoses",
        headers=headers,
        files=_files(leaf_image),
        data={"plot_id": str(seeded["plot_id"])},
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_create_post_without_diagnosis(client, farmer_headers):
    response = client.post(
        f"{API}/forum/posts",
        headers=farmer_headers,
        json={"disease_key": "late_blight", "type": "tip", "content": "Kinh nghiệm của tôi"},
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["disease_key"] == "late_blight"
    assert body["disease_name"]
    assert body["diagnosis_id"] is None
    assert body["diagnosis_summary"] is None
    # Không so khớp đúng "Nông dân A" — `test_api.py` chạy trước có thể đã đổi
    # tên người dùng chung này qua `PATCH /auth/me` (fixture `seeded` dùng chung
    # phiên pytest). Chỉ cần xác nhận trường được điền, không rỗng.
    assert body["user_full_name"]
    assert body["likes_count"] == 0


def test_create_post_requires_disease_or_diagnosis(client, farmer_headers):
    response = client.post(
        f"{API}/forum/posts",
        headers=farmer_headers,
        json={"type": "tip", "content": "Không gắn gì cả"},
    )
    assert response.status_code == 400


def test_create_post_with_diagnosis_fills_disease_key_and_summary(
    client, farmer_headers, seeded, leaf_image
):
    diagnosis = _make_diagnosis(client, farmer_headers, seeded, leaf_image)

    response = client.post(
        f"{API}/forum/posts",
        headers=farmer_headers,
        json={
            "diagnosis_id": diagnosis["id"],
            "type": "disagree",
            "content": "Tôi nghĩ đây là bệnh khác",
        },
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["disease_key"] == diagnosis["disease_key"]
    assert body["diagnosis_id"] == diagnosis["id"]
    assert body["diagnosis_summary"] is not None
    assert diagnosis["disease_name"] in body["diagnosis_summary"]


def test_cannot_attach_another_users_diagnosis(
    client, farmer_headers, admin_headers, seeded, leaf_image
):
    diagnosis = _make_diagnosis(client, farmer_headers, seeded, leaf_image)

    response = client.post(
        f"{API}/forum/posts",
        headers=admin_headers,
        json={"diagnosis_id": diagnosis["id"], "type": "agree", "content": "Không phải của tôi"},
    )
    assert response.status_code == 403


def test_list_posts_filters_by_disease_key_and_type(client, farmer_headers):
    client.post(
        f"{API}/forum/posts",
        headers=farmer_headers,
        json={"disease_key": "mosaic_virus", "type": "agree", "content": "Đồng ý"},
    )
    client.post(
        f"{API}/forum/posts",
        headers=farmer_headers,
        json={"disease_key": "mosaic_virus", "type": "tip", "content": "Mẹo khác"},
    )

    response = client.get(
        f"{API}/forum/posts", headers=farmer_headers,
        params={"disease_key": "mosaic_virus", "type": "agree"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["total"] >= 1
    assert all(item["disease_key"] == "mosaic_virus" for item in body["items"])
    assert all(item["type"] == "agree" for item in body["items"])


def test_post_detail_includes_comments(client, farmer_headers):
    created = client.post(
        f"{API}/forum/posts",
        headers=farmer_headers,
        json={"disease_key": "healthy", "type": "tip", "content": "Bài viết gốc"},
    ).json()

    comment = client.post(
        f"{API}/forum/posts/{created['id']}/comments",
        headers=farmer_headers,
        json={"content": "Bình luận đầu tiên"},
    )
    assert comment.status_code == 201, comment.text
    assert comment.json()["user_full_name"]

    detail = client.get(f"{API}/forum/posts/{created['id']}", headers=farmer_headers)
    assert detail.status_code == 200
    body = detail.json()
    assert len(body["comments"]) == 1
    assert body["comments"][0]["content"] == "Bình luận đầu tiên"


def test_like_post_increments_counter(client, farmer_headers):
    created = client.post(
        f"{API}/forum/posts",
        headers=farmer_headers,
        json={"disease_key": "healthy", "type": "agree", "content": "Thích thử"},
    ).json()

    response = client.post(f"{API}/forum/posts/{created['id']}/like", headers=farmer_headers)
    assert response.status_code == 200, response.text
    assert response.json()["likes_count"] == 1

    response2 = client.post(f"{API}/forum/posts/{created['id']}/like", headers=farmer_headers)
    assert response2.json()["likes_count"] == 2


def test_forum_requires_authentication(client):
    response = client.get(f"{API}/forum/posts")
    assert response.status_code == 401
