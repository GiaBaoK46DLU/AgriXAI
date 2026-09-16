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
from sqlalchemy import func, select

from app.core.security import hash_password
from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.models.medicine import DiseaseGuide, DiseaseMedicine, Medicine
from app.models.plot import Plot, PlotStatus
from app.models.forum import ForumPost, ForumComment, ForumPostType
from app.models.user import User, UserRole
from app.services import diagnosis_service

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

USERS = [
    # ".local" là tên miền dành riêng theo RFC 6762 (mDNS) — email-validator
    # (pydantic EmailStr) từ chối thẳng, gãy cả /auth/login vì UserOut validate
    # lại khi serialize response. Dùng ".vn" cho thật, tránh mọi TLD đặc biệt
    # (arpa/example/invalid/localhost/local/onion/test).
    {"username": "admin", "password": "admin123", "full_name": "Quản trị hệ thống",
     "role": UserRole.ADMIN, "phone": "0900000001", "email": "admin@agrixai.vn"},
    {"username": "nongdan", "password": "nongdan123", "full_name": "Nguyễn Văn Ba",
     "role": UserRole.FARMER, "phone": "0900000002", "email": "nongdan@agrixai.vn"},
    {"username": "nongdan2", "password": "nongdan123", "full_name": "Trần Thị Bốn",
     "role": UserRole.FARMER, "phone": "0900000003", "email": "nongdan2@agrixai.vn"},
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

# ── Thuốc gợi ý theo bệnh + video hướng dẫn ─────────────────────────────
# Nội dung lấy nguyên từ bản thiết kế mobile (mobile/lib/data/demo_data.dart)
# để không sinh ra khuyến cáo mới — chỉ chuyển từ mock sang CSDL thật.
# Link mua/link tham khảo hoạt chất và video YouTube là link thật, tìm bằng
# tay ngày 07/09/2026 — không đảm bảo còn hiệu lực mãi, kiểm tra lại định kỳ.

MEDICINES = {
    "Metalaxyl + Mancozeb": {
        "group": "Trừ nấm lưu dẫn kết hợp tiếp xúc",
        "purchase_url": "https://th-agricare.com.vn/cam-nang-nong-nghiep/goc-thuoc/metalaxyl/",
    },
    "Cymoxanil": {
        "group": "Trừ nấm lưu dẫn — đặc hiệu nấm trứng",
        "purchase_url": "https://vietnong.vn/hoat-chat-cymoxanil/",
    },
    "Dimethomorph": {
        "group": "Trừ nấm lưu dẫn",
        "purchase_url": "https://phunthuoctudong.com/hoat-chat-dimethomorph-chuyen-tri-nam-phytophthora",
    },
    "Mancozeb": {
        "group": "Trừ nấm tiếp xúc phổ rộng",
        "purchase_url": "https://th-agricare.com.vn/huong-dan-su-dung/tac-dung-hoat-chat-mancozeb/",
    },
    "Chlorothalonil": {
        "group": "Trừ nấm tiếp xúc",
        "purchase_url": "https://nongnghieplamdong.com/hoat-chat-chlorothalonil.html",
    },
    "Azoxystrobin": {
        "group": "Trừ nấm lưu dẫn nhóm strobilurin",
        "purchase_url": "https://www.nongviet.com/hoat-chat-azoxystrobin/",
    },
    "Difenoconazole": {
        "group": "Trừ nấm lưu dẫn nhóm triazole",
        "purchase_url": "https://vietthanghanoi.vn/hoat-chat-difenoconazole/",
    },
    "Copper hydroxide": {
        "group": "Thuốc gốc đồng — kháng khuẩn",
        "purchase_url": "https://www.anbio.vn/blogs/kien-thuc/hoat-chat-thuoc-bao-ve-thuc-vat-goc-dong-phong-tru-benh-hai-cay-trong",
    },
    "Copper oxychloride": {
        "group": "Thuốc gốc đồng — kháng khuẩn",
        "purchase_url": "https://www.anbio.vn/blogs/kien-thuc/hoat-chat-thuoc-bao-ve-thuc-vat-goc-dong-phong-tru-benh-hai-cay-trong",
    },
    "Abamectin": {
        "group": "Trừ nhện — nguồn gốc sinh học",
        "purchase_url": "https://vietnong.vn/hoat-chat-abamectin/",
    },
    "Spiromesifen": {
        "group": "Trừ nhện, diệt cả trứng",
        "purchase_url": None,
    },
    "Dầu khoáng": {
        "group": "Bịt lỗ thở — an toàn cho thiên địch",
        "purchase_url": None,
    },
    "Pymetrozine": {
        "group": "Trừ bọ phấn — chặn môi giới truyền virus",
        "purchase_url": "https://ducthanhagri.com/hoat-chat-pymetrozine/",
    },
    "Dinotefuran": {
        "group": "Trừ bọ phấn lưu dẫn",
        "purchase_url": "https://www.kingelong.com.vn/blogs/tin-chuyen-nganh/hoat-chat-dinotefuran",
    },
}

# disease_key -> [(tên thuốc, ghi chú riêng cho cặp này | None), ...]
DISEASE_MEDICINES: dict[str, list[tuple[str, str | None]]] = {
    "late_blight": [
        ("Metalaxyl + Mancozeb", None),
        ("Cymoxanil", None),
        ("Dimethomorph", None),
    ],
    "early_blight": [
        ("Mancozeb", None),
        ("Chlorothalonil", None),
        ("Azoxystrobin", None),
        ("Difenoconazole", None),
    ],
    "bacterial_spot": [
        ("Copper hydroxide", None),
        ("Copper oxychloride", None),
        ("Mancozeb", "Phối hợp với thuốc gốc đồng để tăng hiệu quả"),
    ],
    "septoria_leaf_spot": [
        ("Chlorothalonil", None),
        ("Mancozeb", None),
        ("Azoxystrobin", None),
    ],
    "leaf_mold": [
        ("Chlorothalonil", None),
        ("Mancozeb", None),
        ("Difenoconazole", None),
    ],
    "target_spot": [
        ("Azoxystrobin", None),
        ("Difenoconazole", None),
        ("Mancozeb", None),
    ],
    "spider_mites": [
        ("Abamectin", None),
        ("Spiromesifen", None),
        ("Dầu khoáng", None),
    ],
    "yellow_leaf_curl_virus": [
        ("Pymetrozine", "Trị bọ phấn trắng — môi giới truyền bệnh, không phải trị virus"),
        ("Dinotefuran", "Trị bọ phấn trắng — môi giới truyền bệnh, không phải trị virus"),
        ("Dầu khoáng", "Xua và bịt lỗ thở bọ phấn, không phải trị virus"),
    ],
    # mosaic_virus, healthy: cố tình không có thuốc — virus không chữa được
    # bằng thuốc, lá khoẻ thì không cần thuốc. Mobile hiện `noProductText`.
}

# disease_key -> link YouTube hướng dẫn xử lý (tìm tay 07/09/2026, tiếng Việt)
DISEASE_GUIDES = {
    "late_blight": "https://www.youtube.com/watch?v=aHN9bwgL3qo",
    "early_blight": "https://www.youtube.com/watch?v=X-qsSbxv288",
    "bacterial_spot": "https://www.youtube.com/watch?v=w8V3EVL48H8",
    "septoria_leaf_spot": "https://www.youtube.com/watch?v=Q0UGegDx-bQ",
    "leaf_mold": "https://www.youtube.com/watch?v=GwAlAz8io3Y",
    "target_spot": "https://www.youtube.com/watch?v=GwAlAz8io3Y",
    "spider_mites": "https://www.youtube.com/watch?v=Q0UGegDx-bQ",
    "yellow_leaf_curl_virus": "https://www.youtube.com/watch?v=9P6A0I8Sf80",
    "mosaic_virus": "https://www.youtube.com/watch?v=gL8Ja3gWLBQ",
}


def seed_users(db) -> dict[str, User]:
    result: dict[str, User] = {}
    for spec in USERS:
        user = db.scalar(select(User).where(User.username == spec["username"]))
        if user is None:
            user = User(
                username=spec["username"],
                full_name=spec["full_name"],
                email=spec["email"],
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


def seed_medicines(db) -> None:
    """Tạo thuốc gợi ý theo bệnh + video hướng dẫn. Chạy lại được nhiều lần."""
    medicine_ids: dict[str, int] = {}
    for name, spec in MEDICINES.items():
        medicine = db.scalar(select(Medicine).where(Medicine.name == name))
        if medicine is None:
            medicine = Medicine(name=name, group=spec["group"], purchase_url=spec["purchase_url"])
            db.add(medicine)
            db.flush()
            logger.info("  + thuốc %s", name)
        medicine_ids[name] = medicine.id

    for disease_key, entries in DISEASE_MEDICINES.items():
        for medicine_name, note in entries:
            exists = db.scalar(
                select(DiseaseMedicine).where(
                    DiseaseMedicine.disease_key == disease_key,
                    DiseaseMedicine.medicine_id == medicine_ids[medicine_name],
                )
            )
            if exists is None:
                db.add(DiseaseMedicine(
                    disease_key=disease_key,
                    medicine_id=medicine_ids[medicine_name],
                    note=note,
                ))
                logger.info("  + %s -> %s", disease_key, medicine_name)

    for disease_key, video_url in DISEASE_GUIDES.items():
        guide = db.get(DiseaseGuide, disease_key)
        if guide is None:
            db.add(DiseaseGuide(disease_key=disease_key, video_url=video_url))
            logger.info("  + video hướng dẫn %s", disease_key)
        else:
            guide.video_url = video_url

    db.commit()


def seed_forum(db, users: dict[str, User]) -> None:
    logger.info("  Đang tạo dữ liệu diễn đàn...")
    existing_count = db.scalar(select(func.count(ForumPost.id))) or 0
    if existing_count >= 15:
        logger.info("  · Đã có đủ dữ liệu diễn đàn (%d bài), bỏ qua.", existing_count)
        return

    admin = users["admin"]
    nongdan = users["nongdan"]
    nongdan2 = users["nongdan2"]
    now = datetime.now(timezone.utc)

    # ── 15 bài viết trải đều các loại bệnh và loại phản hồi ──────────────────
    post_specs = [
        # --- Mốc sương (late_blight) ---
        dict(
            user=nongdan, disease_key="late_blight", type=ForumPostType.TIP,
            content=(
                "Mọi người ơi, vườn cà chua 500m² nhà mình bị mốc sương nặng sau đợt mưa kéo dài 3 ngày. "
                "Mình đã dùng Metalaxyl kết hợp Mancozeb phun 2 lần cách nhau 5 ngày, thấy lá mới ra sạch hơn nhiều. "
                "Quan trọng là phun đều cả mặt dưới lá và phun lúc trời mát sáng sớm nhé."
            ),
            likes_count=18, days_ago=2,
        ),
        dict(
            user=nongdan2, disease_key="late_blight", type=ForumPostType.DISAGREE,
            content=(
                "Hệ thống chẩn đoán bảo cây mình bị mốc sương nhưng mình thấy đốm trên lá khác lắm — "
                "đốm vàng lan rộng không có viền nước như mốc sương thật. Hay là bệnh héo vàng? "
                "Có ai từng gặp triệu chứng tương tự không ạ?"
            ),
            likes_count=7, days_ago=5,
        ),
        dict(
            user=admin, disease_key="late_blight", type=ForumPostType.TIP,
            content=(
                "Phòng mốc sương hiệu quả nhất là quản lý độ ẩm: tưới nhỏ giọt thay vì tưới phun, "
                "dọn lá bệnh ngay khi phát hiện, và dùng lưới che mưa nếu có điều kiện. "
                "Thuốc chỉ là biện pháp hỗ trợ, không thể thay thế quản lý tốt."
            ),
            likes_count=24, days_ago=8,
        ),
        # --- Nhện đỏ (spider_mites) ---
        dict(
            user=nongdan2, disease_key="spider_mites", type=ForumPostType.MEDICINE_ISSUE,
            content=(
                "Hôm trước hệ thống gợi ý dùng Dầu khoáng cho nhện đỏ, nhưng mình xịt 3 lần không thấy bớt nhiều, "
                "nhện vẫn bò đầy mặt dưới lá. Nhà mình trồng trong nhà kính nên nhiệt độ cao, "
                "có phải vì vậy dầu khoáng kém hiệu quả hơn không? Có nên đổi sang Abamectin không ạ?"
            ),
            likes_count=12, days_ago=3,
        ),
        dict(
            user=admin, disease_key="spider_mites", type=ForumPostType.AGREE,
            content=(
                "Chào bạn! Dầu khoáng đúng là kém hiệu quả hơn khi nhiệt độ trên 35°C vì bay hơi nhanh. "
                "Trong nhà kính bạn nên dùng Abamectin hoặc Bifenazate. Nhớ luân phiên thuốc vì nhện đỏ "
                "kháng thuốc rất nhanh — cùng một hoạt chất dùng quá 3 lần liên tiếp là giảm hiệu lực rõ rệt."
            ),
            likes_count=31, days_ago=3,
        ),
        dict(
            user=nongdan, disease_key="spider_mites", type=ForumPostType.TIP,
            content=(
                "Mình trị nhện đỏ bằng cách phun nước áp lực cao mặt dưới lá mỗi sáng trước khi trời nóng, "
                "kết hợp thả bọ rùa thiên địch. Chi phí thấp, an toàn, nhưng cần kiên nhẫn 2-3 tuần. "
                "Vườn mình giảm 80% nhện đỏ mà không dùng thuốc hóa học."
            ),
            likes_count=15, days_ago=10,
        ),
        # --- Sâu đục quả (fruit_borer) ---
        dict(
            user=nongdan, disease_key="fruit_borer", type=ForumPostType.TIP,
            content=(
                "Vụ này sâu đục quả phá nặng lắm, cứ 2-3 quả lại có 1 quả bị đục. "
                "Mình đặt bẫy pheromone 10 bẫy/1000m², cộng với phun Spinosad lúc bướm đẻ trứng nhiều nhất "
                "(chiều tối). Sau 2 tuần tỉ lệ quả bị hại giảm từ 30% xuống còn khoảng 8%."
            ),
            likes_count=9, days_ago=1,
        ),
        dict(
            user=nongdan2, disease_key="fruit_borer", type=ForumPostType.AGREE,
            content=(
                "Bẫy pheromone thật sự rất hiệu quả! Mình dùng từ 2 vụ nay rồi. "
                "Lưu ý là phải thay mồi 4-6 tuần/lần và đặt bẫy trước khi cây ra hoa để bắt bướm sớm. "
                "Kết hợp với bao quả thì gần như không cần phun thuốc."
            ),
            likes_count=6, days_ago=1,
        ),
        # --- Héo fusarium (fusarium_wilt) ---
        dict(
            user=admin, disease_key="fusarium_wilt", type=ForumPostType.TIP,
            content=(
                "Fusarium không có thuốc trị dứt điểm — phòng bệnh quan trọng hơn trị. "
                "Ba việc quan trọng nhất: (1) dùng giống kháng bệnh, (2) khử trùng đất trước khi trồng "
                "bằng Trichoderma hoặc phơi nắng, (3) tưới nước đúng lượng, không để đất quá ẩm."
            ),
            likes_count=42, days_ago=15,
        ),
        dict(
            user=nongdan, disease_key="fusarium_wilt", type=ForumPostType.MEDICINE_ISSUE,
            content=(
                "App gợi ý dùng Carbendazim cho cây héo fusarium nhà mình. Mình đã tưới vào gốc 3 lần "
                "nhưng cây vẫn héo dần rồi chết. Nghe nói nấm này đã kháng Carbendazim nhiều nơi rồi. "
                "Hiện có thuốc nào hiệu quả hơn không ạ?"
            ),
            likes_count=5, days_ago=6,
        ),
        # --- Đốm vòng (early_blight) ---
        dict(
            user=nongdan2, disease_key="early_blight", type=ForumPostType.TIP,
            content=(
                "Đốm vòng thường xuất hiện ở lá già trước, từ dưới lên trên. "
                "Bí quyết của mình: tỉa bỏ tất cả lá già, lá sát mặt đất, kể cả lá chưa bệnh "
                "để thông thoáng gốc. Kết hợp phun Chlorothalonil 2 tuần/lần. Hiệu quả và rẻ hơn nhiều "
                "so với để bệnh nặng rồi mới xử lý."
            ),
            likes_count=20, days_ago=4,
        ),
        dict(
            user=nongdan, disease_key="early_blight", type=ForumPostType.AGREE,
            content=(
                "Đúng vậy! Tỉa lá là bước quan trọng nhất. Mình thêm một bước nữa là bón Canxi "
                "và Kali đều đặn — cây khỏe thì đề kháng tốt hơn nhiều. "
                "Vụ trước dùng cách này, cây mình gần như không bị đốm vòng dù vườn xung quanh bị nặng."
            ),
            likes_count=13, days_ago=4,
        ),
        # --- Virus xoăn lá (leaf_curl_virus) ---
        dict(
            user=admin, disease_key="leaf_curl_virus", type=ForumPostType.TIP,
            content=(
                "Virus xoăn vàng lá cà chua (TYLCV) lây qua bọ phấn — không có thuốc trị virus, "
                "chỉ có thể diệt vector. Mình dùng lưới 50 mesh bao kín nhà lưới + vàng bẫy bọ phấn "
                "+ phun Imidacloprid. Quan trọng: nhổ ngay cây bệnh, bao túi nilon trước khi mang ra "
                "khỏi vườn để không lây lan."
            ),
            likes_count=35, days_ago=12,
        ),
        # --- Xì mủ thân (bacterial_canker) ---
        dict(
            user=nongdan2, disease_key="bacterial_canker", type=ForumPostType.DISAGREE,
            content=(
                "Hệ thống chẩn đoán cây mình bị xì mủ thân do vi khuẩn nhưng mình thấy vết thương "
                "trên thân khô và nứt nẻ chứ không có mủ chảy. Sau mưa lớn cây bị tương tự — "
                "hay là do vết thương cơ học khi buộc dây? Mình không chắc lắm."
            ),
            likes_count=3, days_ago=7,
        ),
        dict(
            user=nongdan, disease_key="bacterial_canker", type=ForumPostType.MEDICINE_ISSUE,
            content=(
                "Mình dùng Copper Oxychloride phun lên vết bệnh theo hướng dẫn app nhưng thấy lá "
                "bị cháy viền sau khi phun. Có phải do pha nồng độ sai không? "
                "Hay là do phun lúc trời nắng gắt 12 giờ trưa? Mọi người có kinh nghiệm không?"
            ),
            likes_count=8, days_ago=9,
        ),
    ]

    posts = []
    for i, spec in enumerate(post_specs):
        days_ago = spec.get("days_ago", 0)
        post = ForumPost(
            user_id=spec["user"].id,
            disease_key=spec["disease_key"],
            type=spec["type"],
            content=spec["content"],
            likes_count=spec.get("likes_count", 0),
        )
        db.add(post)
        posts.append((post, days_ago))

    db.commit()

    # Rải ngược thời gian
    for post, days_ago in posts:
        db.refresh(post)
        post.created_at = now - timedelta(days=days_ago, hours=random.randint(0, 8))
    db.commit()

    # ── Bình luận phong phú ────────────────────────────────────────────────────
    post_objs = [p for p, _ in posts]
    comments_data = [
        # Bài 0 - late_blight TIP
        (post_objs[0], nongdan2, "Tuyệt vời, mình sẽ thử ngay vụ này! Tỷ lệ pha Metalaxyl : Mancozeb là bao nhiêu vậy bạn?", 2),
        (post_objs[0], admin, "Bạn nhớ chú ý PHI (Pre-Harvest Interval) trên bao bì nhé, đặc biệt khi quả sắp chín.", 2),
        (post_objs[0], nongdan2, "À, mình hiểu rồi. Vậy trước thu hoạch 14 ngày thì ngưng phun đúng không?", 1),

        # Bài 1 - late_blight DISAGREE
        (post_objs[1], admin, "Triệu chứng bạn mô tả — đốm vàng lan rộng không có viền nước — có thể là bệnh héo vàng (Fusarium) hoặc thiếu Magiê. Bạn thử kiểm tra rễ xem có thâm đen không?", 5),
        (post_objs[1], nongdan, "Mình cũng từng nhầm lẫn tương tự. Mốc sương thật sự có mảng trắng xám ở mặt dưới lá khi trời ẩm — bạn kiểm tra xem có không.", 4),

        # Bài 3 - spider_mites MEDICINE_ISSUE
        (post_objs[3], admin, "Nhiệt độ cao làm dầu khoáng kém hiệu quả đúng rồi. Trong nhà kính trên 32°C, bạn dùng Abamectin hoặc Spirodiclofen sẽ tốt hơn nhiều.", 3),
        (post_objs[3], nongdan, "Mình cũng gặp tình trạng tương tự trong nhà kính. Abamectin 3 lần cách nhau 7 ngày giải quyết được vấn đề.", 2),
        (post_objs[3], nongdan2, "Cảm ơn mọi người nhiều! Mình sẽ đổi sang Abamectin thử.", 1),

        # Bài 4 - spider_mites AGREE (admin)
        (post_objs[4], nongdan2, "Cảm ơn anh/chị admin! Vậy mình nên luân phiên Abamectin → Bifenazate → Spiromesifen phải không?", 2),
        (post_objs[4], admin, "Đúng vậy! Luân phiên 3 hoạt chất khác nhau là tốt nhất. Mỗi đợt chỉ dùng cùng hoạt chất tối đa 2 lần.", 2),

        # Bài 5 - spider_mites TIP (thiên địch)
        (post_objs[5], nongdan2, "Hay quá! Bọ rùa mua ở đâu vậy bạn? Tìm trên mạng hay có đại lý riêng?", 9),
        (post_objs[5], nongdan, "Mình mua qua hợp tác xã bảo vệ thực vật địa phương. Giá khoảng 150k/túi 500 con.", 9),

        # Bài 6 - fruit_borer TIP
        (post_objs[6], nongdan2, "Bẫy pheromone loại nào hiệu quả? Bạn dùng của hãng nào?", 1),
        (post_objs[6], nongdan, "Mình dùng của Hợp Trí, giá ổn và mồi bền. Đặt bẫy ở độ cao ngang đầu người là tốt nhất.", 0),

        # Bài 8 - fusarium TIP (admin)
        (post_objs[8], nongdan, "Mình đã dùng Trichoderma trộn vào đất trước khi trồng 2 vụ nay. Tỉ lệ cây bị héo giảm rõ rệt. Cần bao nhiêu lượng Trichoderma cho 1000m² ạ?", 14),
        (post_objs[8], admin, "Khoảng 2-3 kg chế phẩm Trichoderma (10^8 CFU/g) trộn đều vào đất 2-3 tuần trước khi trồng. Đất ẩm vừa phải để nấm phát triển tốt.", 14),
        (post_objs[8], nongdan2, "Ngoài Trichoderma, bón phân hữu cơ hoai mục cũng giúp ích rất nhiều — vi sinh vật có lợi trong phân cạnh tranh với Fusarium.", 12),

        # Bài 9 - fusarium MEDICINE_ISSUE
        (post_objs[9], admin, "Bạn nói đúng, Carbendazim đã bị kháng nhiều nơi. Hiện tại Fludioxonil + Metalaxyl M hoặc Thiophanate-methyl + Tebuconazole hiệu quả hơn. Nhưng quan trọng nhất vẫn là nhổ cây bệnh sớm.", 5),

        # Bài 10 - early_blight TIP
        (post_objs[10], admin, "Bổ sung thêm: nên phun Chlorothalonil buổi chiều mát, không phun lúc trời nắng gắt. Và đừng quên phun cả mặt dưới lá — đó là nơi bào tử phát triển nhiều nhất.", 3),
        (post_objs[10], nongdan, "Mình thêm một bước: sau khi tỉa lá, rắc vôi bột xung quanh gốc để sát khuẩn đất. Đơn giản mà hiệu quả.", 3),

        # Bài 11 - early_blight AGREE
        (post_objs[11], nongdan2, "Canxi qua lá hay qua gốc bạn? Mình nghe nói Canxi qua lá hiệu quả hơn cho cà chua.", 3),
        (post_objs[11], nongdan, "Mình dùng cả hai: Canxi + Boron qua lá mỗi 10 ngày, kết hợp bón phân NPK + CaO vào đất mỗi vụ.", 3),

        # Bài 12 - virus TIP
        (post_objs[12], nongdan, "Lưới 50 mesh có làm giảm thông gió nhiều không ạ? Mình lo cây bị ngột ngạt trong nhà kính.", 10),
        (post_objs[12], admin, "Có giảm thông gió chút nhưng không đáng kể nếu thiết kế nhà kính đúng. Ưu tiên cửa thông gió 2 đầu hồi rộng và mái có khe thoáng.", 10),

        # Bài 14 - bacterial_canker MEDICINE_ISSUE
        (post_objs[14], admin, "Copper Oxychloride bị phytotoxic (cháy lá) khi phun lúc trời nắng trên 30°C hoặc pha quá đặc. Nên phun sáng sớm hoặc chiều mát, nồng độ 0.25-0.3% (pha đúng theo bao bì).", 8),
        (post_objs[14], nongdan2, "Mình cũng bị vậy một lần. Sau đó học được bài: không bao giờ phun thuốc đồng lúc 11 giờ-15 giờ.", 7),
    ]

    for (post, user, content, days_ago_c) in comments_data:
        comment = ForumComment(post_id=post.id, user_id=user.id, content=content)
        db.add(comment)
        db.flush()
        comment.created_at = now - timedelta(days=days_ago_c, hours=random.randint(0, 5))

    db.commit()
    logger.info(
        "  + Đã thêm %d bài viết diễn đàn và %d bình luận.",
        len(post_objs), len(comments_data),
    )


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
            images=[_fake_leaf_image(rng) for _ in range(3)],
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

        logger.info("\nThuốc gợi ý + video hướng dẫn:")
        seed_medicines(db)

        logger.info("\nDiễn đàn:")
        seed_forum(db, users)

        if args.diagnoses:
            logger.info("\nLịch sử chẩn đoán:")
            seed_diagnoses(db, users, plots, args.count)

    logger.info("\nXong. Đăng nhập thử với:")
    for spec in USERS:
        logger.info("  %-10s / %-12s (%s)", spec["username"], spec["password"], spec["role"])


if __name__ == "__main__":
    main()
