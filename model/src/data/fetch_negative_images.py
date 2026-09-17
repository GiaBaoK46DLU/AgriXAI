"""Tải bộ ảnh "không phải lá cà chua" cho issue #91, từ Wikimedia Commons.

Vì sao Wikimedia Commons chứ không phải tìm ảnh Google/Bing tuỳ ý: mọi file trên
Commons đều có giấy phép tái sử dụng rõ ràng (ghi trong ``extmetadata`` của chính
ảnh, script này lưu lại trong manifest) và có API tra cứu ổn định — không cần đoán
URL ảnh, chỉ cần gọi ``action=query`` rồi lấy URL thật trả về.

⚠️ **Đây là lệch hướng có chủ đích so với chính ticket #91**, mục "Gợi ý triển khai"
của ticket viết thẳng: "Không lấy ảnh từ Internet cho bộ này" — vì ảnh mạng đã qua
nén/chỉnh màu, phân phối khác ảnh điện thoại chụp thật, và bộ phân loại 2 lớp (#92)
có nguy cơ học nhầm "ảnh nén web" so với "ảnh điện thoại" thay vì "không phải lá cà
chua" so với "lá cà chua". Dùng script này vì nhóm xác nhận không tự chụp được ảnh
lúc này (quyết định 17/09/2026, xem CLAUDE.md) — **rủi ro đó vẫn còn**, không bị gỡ
bỏ chỉ vì đổi nguồn ảnh. Khi báo cáo #91/#92 phải nói rõ bộ âm dựng từ ảnh Internet.

Nhóm "ảnh mờ/tối/rung" (``blur_dark_shake``) **không** tìm bằng từ khoá như 5 nhóm
kia. Đã thử ("blurry photograph", "motion blur photo"...) và kiểm bằng mắt: Commons
gần như không có kho ảnh chụp hỏng thật — kết quả trả về toàn ảnh nét cố tình dùng
"blur" làm hiệu ứng nghệ thuật (bokeh hậu cảnh, ảnh kiến trúc sắc nét gắn nhầm từ
khoá...). Thay vào đó, nhóm này **tổng hợp** bằng cách lấy ngẫu nhiên ảnh thật đã
tải từ 5 nhóm kia rồi làm méo bằng PIL/numpy (mờ nét, mờ chuyển động, thiếu sáng) —
mô phỏng đúng ba lỗi chụp ("mờ / tối / rung") thay vì đoán mò từ khoá tìm kiếm.

Chạy:
    cd model
    .venv/Scripts/python -m src.data.fetch_negative_images --target-per-group 50

Ghi vào ``model/data/negative/<group>/`` + ``model/data/negative/manifest.csv``.
An toàn khi chạy lại nhiều lần: bỏ qua ảnh đã có (theo sha256 đọc từ manifest cũ).
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import random
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

API_URL = "https://commons.wikimedia.org/w/api.php"
# Commons yêu cầu User-Agent định danh rõ ràng, không phải trình duyệt giả.
USER_AGENT = (
    "AgriXAI-ThesisDataCollection/1.0 "
    "(dlgb260704@gmail.com; do an tot nghiep DHDL, thu thap anh am cho issue #91, phi thuong mai)"
)
THUMB_WIDTH = 1024
MIN_SIDE = 400
REQUEST_DELAY_S = 0.3
BLUR_GROUP = "blur_dark_shake"
MANIFEST_FIELDS = [
    "path", "group", "title", "page_url", "license_short_name",
    "width", "height", "sha256",
]

# Thử batch đầu (target=5/nhóm) lộ ra: tìm theo từ khoá trên Commons trúng rất
# nhiều trang scan sách/tạp chí cũ (Internet Archive Book Images, Biodiversity
# Heritage Library) vì caption OCR khớp từ khoá dù ảnh thật là trang giấy scan,
# không phải ảnh chụp vật thể/lá cây thật. Loại theo category, không theo tên
# file (số ID Flickr đuôi tên không phân biệt được scan với ảnh thật).
EXCLUDED_CATEGORY_MARKERS = (
    "internet archive book images",
    "biodiversity heritage library",
    "book illustrations",
    "book scans",
)
# Vòng soát thứ hai (sau khi tải xong batch 60/nhóm) lộ thêm một loại lẫn khác:
# minh hoạ y khoa/tôn giáo cổ (khắc đồng, thạch bản, ảnh trang atlas giải phẫu,
# chữ cái trang trí trong bản thảo Phúc Âm thời trung cổ) — toàn bộ nhóm
# ``hand_face_clothing``, khớp từ khoá "hand"/"face" nhưng là tranh vẽ/scan trang
# sách, không phải ảnh chụp. Category không đủ đặc trưng để lọc tự động ổn định
# (nhiều ảnh Wellcome/Walters thật KHÔNG gắn category rõ ràng), nên lọc trực tiếp
# theo TIÊU ĐỀ — coi là an toàn vì các minh hoạ này luôn ghi rõ nguồn trong tên file.
EXCLUDED_TITLE_MARKERS = (
    "wellcome",
    "walters manuscript",
    "historiated initial",
    "gospel book",
    "engraving",
    "lithograph",
    "woodcut",
    "stereoscopic atlas",
)

# 5 nhóm tải thật từ Commons. Nhóm thứ 6 (blur_dark_shake) tổng hợp riêng — xem
# docstring ở đầu file.
GROUPS: dict[str, list[str]] = {
    "indoor_objects": [
        "wooden table indoor photo",
        "chair furniture photo",
        "interior wall plain photo",
        "floor tile indoor photo",
        "coffee mug on table photo",
        "book stack photo",
        "smartphone on table photo",
    ],
    "hand_face_clothing": [
        "human hand palm photo",
        "human face portrait photo",
        "person wearing shirt clothing photo",
        "blue jeans clothing photo",
        "human hands closeup photo",
    ],
    "other_plant_leaves": [
        "potato plant leaves photo",
        "chili pepper plant leaf photo",
        "eggplant plant leaves photo",
        "basil plant leaves photo",
        "rose bush leaves photo",
        "green leaves closeup photo",
    ],
    "soil_ground": [
        "bare soil ground photo",
        "gravel stones ground photo",
        "concrete pavement texture photo",
        "green grass lawn photo",
        "garden bed soil photo",
    ],
    "screenshot_document": [
        "computer desktop screenshot",
        "smartphone app screenshot",
        "printed document page photo",
        "scanned document page",
    ],
}


def _api_get(params: dict) -> dict:
    query = dict(params, format="json")
    url = f"{API_URL}?{urllib.parse.urlencode(query)}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def search_titles(query: str, limit: int = 30) -> list[str]:
    data = _api_get(
        {
            "action": "query",
            "list": "search",
            "srnamespace": 6,  # namespace File:
            "srsearch": query,
            "srlimit": limit,
        }
    )
    return [item["title"] for item in data.get("query", {}).get("search", [])]


def fetch_imageinfo(titles: list[str]) -> dict:
    if not titles:
        return {}
    data = _api_get(
        {
            "action": "query",
            "titles": "|".join(titles),
            "prop": "imageinfo|categories",
            "iiprop": "url|size|mime|extmetadata",
            "iiurlwidth": THUMB_WIDTH,
            # 500 = mức tối đa cho tài khoản thường (không phải bot). Từng đặt 50 —
            # SAI: cllimit tính chung cho cả batch nhiều title trong một lần gọi,
            # không phải mỗi trang, nên các trang xếp sau trong batch 30 title bị
            # cắt category rỗng và lọt qua is_archival_scan() một cách âm thầm
            # (kiểm bằng tay thấy "Hand-book of physiology (1892)" vẫn lọt được dù
            # rõ ràng thuộc category bị loại).
            "cllimit": 500,
        }
    )
    return data.get("query", {}).get("pages", {})


def is_archival_scan(page: dict) -> bool:
    cats = " ".join(c.get("title", "") for c in page.get("categories", [])).lower()
    if any(marker in cats for marker in EXCLUDED_CATEGORY_MARKERS):
        return True
    title = page.get("title", "").lower()
    return any(marker in title for marker in EXCLUDED_TITLE_MARKERS)


def load_existing_hashes(manifest_path: Path) -> set[str]:
    if not manifest_path.exists():
        return set()
    with manifest_path.open("r", encoding="utf-8") as f:
        return {row["sha256"] for row in csv.DictReader(f)}


def download(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read()


def fetch_real_groups(out_dir: Path, target_per_group: int, min_side: int, writer, mf, seen_hashes: set[str]) -> dict[str, int]:
    summary: dict[str, int] = {}

    for group, queries in GROUPS.items():
        group_dir = out_dir / group
        group_dir.mkdir(exist_ok=True)
        # Bug đã gặp: đếm mỗi *.jpg bỏ sót ảnh .png đã tải (nhóm screenshot_document
        # có nhiều .png) → "kept" khởi điểm thấp hơn thật, khiến vòng lặp tưởng
        # chưa đủ target và tải dư hẳn một loạt ảnh không liên quan (từ khoá cuối
        # cùng trong danh sách truy vấn thường kém liên quan nhất).
        existing_count = sum(1 for _ in group_dir.glob("*.jpg")) + sum(1 for _ in group_dir.glob("*.png"))
        kept = existing_count
        seen_titles: set[str] = set()

        for query in queries:
            if kept >= target_per_group:
                break
            try:
                titles = search_titles(query, limit=30)
            except (urllib.error.URLError, TimeoutError) as e:
                print(f"[{group}] lỗi tìm kiếm '{query}': {e}")
                continue
            time.sleep(REQUEST_DELAY_S)

            new_titles = [t for t in titles if t not in seen_titles]
            seen_titles.update(new_titles)
            if not new_titles:
                continue

            try:
                pages = fetch_imageinfo(new_titles)
            except (urllib.error.URLError, TimeoutError) as e:
                print(f"[{group}] lỗi lấy imageinfo cho '{query}': {e}")
                continue
            time.sleep(REQUEST_DELAY_S)

            for page in pages.values():
                if kept >= target_per_group:
                    break
                infos = page.get("imageinfo")
                if not infos:
                    continue
                if is_archival_scan(page):
                    continue
                info = infos[0]
                mime = info.get("mime", "")
                if mime not in ("image/jpeg", "image/png"):
                    continue
                width, height = info.get("width", 0), info.get("height", 0)
                if min(width, height) < min_side:
                    continue
                src_url = info.get("thumburl") or info.get("url")
                if not src_url:
                    continue

                try:
                    raw = download(src_url)
                except (urllib.error.URLError, TimeoutError) as e:
                    print(f"[{group}] lỗi tải {src_url}: {e}")
                    continue
                time.sleep(REQUEST_DELAY_S)

                digest = hashlib.sha256(raw).hexdigest()
                if digest in seen_hashes:
                    continue
                seen_hashes.add(digest)

                kept += 1
                ext = ".png" if mime == "image/png" else ".jpg"
                filename = f"{kept:04d}_{digest[:10]}{ext}"
                dest = group_dir / filename
                dest.write_bytes(raw)

                extmeta = info.get("extmetadata", {})
                license_name = extmeta.get("LicenseShortName", {}).get("value", "unknown")

                writer.writerow(
                    {
                        "path": str(dest.relative_to(out_dir.parent.parent)),
                        "group": group,
                        "title": page.get("title", ""),
                        "page_url": info.get("descriptionurl", ""),
                        "license_short_name": license_name,
                        "width": width,
                        "height": height,
                        "sha256": digest,
                    }
                )
                mf.flush()

        summary[group] = kept

    return summary


def _motion_blur(img: Image.Image, length: int, angle_deg: float) -> Image.Image:
    arr = np.asarray(img).astype(np.float32)
    theta = math.radians(angle_deg)
    dx, dy = math.cos(theta), math.sin(theta)
    acc = np.zeros_like(arr)
    steps = max(length, 1)
    for i in range(steps):
        offset = i - steps // 2
        acc += np.roll(arr, shift=(int(round(offset * dy)), int(round(offset * dx))), axis=(0, 1))
    acc /= steps
    return Image.fromarray(np.clip(acc, 0, 255).astype(np.uint8))


def _darken(img: Image.Image, factor: float) -> Image.Image:
    arr = np.asarray(img).astype(np.float32) * factor
    noise = np.random.default_rng().normal(0, 4, arr.shape)
    return Image.fromarray(np.clip(arr + noise, 0, 255).astype(np.uint8))


def degrade_image(img: Image.Image, rng: random.Random) -> tuple[Image.Image, str]:
    kind = rng.choice(["out_of_focus", "motion_blur", "underexposed", "blur_and_dark"])
    if kind == "out_of_focus":
        out = img.filter(ImageFilter.GaussianBlur(rng.uniform(4, 10)))
    elif kind == "motion_blur":
        out = _motion_blur(img, length=rng.randint(10, 22), angle_deg=rng.uniform(0, 360))
    elif kind == "underexposed":
        out = _darken(img, factor=rng.uniform(0.2, 0.45))
    else:
        blurred = img.filter(ImageFilter.GaussianBlur(rng.uniform(3, 7)))
        out = _darken(blurred, factor=rng.uniform(0.3, 0.55))
    return out, kind


def synthesize_blur_group(out_dir: Path, source_groups: list[str], target_count: int, min_side: int, writer, mf, seen_hashes: set[str]) -> int:
    group_dir = out_dir / BLUR_GROUP
    group_dir.mkdir(exist_ok=True)
    kept = sum(1 for _ in group_dir.glob("*.jpg"))
    if kept >= target_count:
        return kept

    pool: list[Path] = []
    for g in source_groups:
        pool.extend((out_dir / g).glob("*.jpg"))
        pool.extend((out_dir / g).glob("*.png"))
    if not pool:
        print(f"[{BLUR_GROUP}] không có ảnh nguồn để tổng hợp — chạy các nhóm khác trước")
        return kept

    rng = random.Random(42)
    rng.shuffle(pool)
    idx = 0
    attempts = 0
    max_attempts = target_count * 6
    while kept < target_count and attempts < max_attempts:
        attempts += 1
        src_path = pool[idx % len(pool)]
        idx += 1
        try:
            with Image.open(src_path) as im:
                im = im.convert("RGB")
                if min(im.size) < min_side:
                    continue
                degraded, kind = degrade_image(im, rng)
        except (OSError, ValueError) as e:
            print(f"[{BLUR_GROUP}] lỗi đọc {src_path}: {e}")
            continue

        buf = io.BytesIO()
        degraded.save(buf, format="JPEG", quality=88)
        raw = buf.getvalue()
        digest = hashlib.sha256(raw).hexdigest()
        if digest in seen_hashes:
            continue
        seen_hashes.add(digest)

        kept += 1
        dest = group_dir / f"{kept:04d}_{digest[:10]}.jpg"
        dest.write_bytes(raw)

        writer.writerow(
            {
                "path": str(dest.relative_to(out_dir.parent.parent)),
                "group": BLUR_GROUP,
                "title": f"tong hop ({kind}) tu {src_path.relative_to(out_dir.parent.parent)}",
                "page_url": "",
                "license_short_name": "derived (xem license ảnh gốc trong hàng manifest tương ứng)",
                "width": degraded.width,
                "height": degraded.height,
                "sha256": digest,
            }
        )
        mf.flush()

    return kept


def run(out_dir: Path, target_per_group: int, min_side: int) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_dir / "manifest.csv"
    seen_hashes = load_existing_hashes(manifest_path)
    write_header = not manifest_path.exists()

    with manifest_path.open("a", encoding="utf-8", newline="") as mf:
        writer = csv.DictWriter(mf, fieldnames=MANIFEST_FIELDS)
        if write_header:
            writer.writeheader()

        summary = fetch_real_groups(out_dir, target_per_group, min_side, writer, mf, seen_hashes)
        summary[BLUR_GROUP] = synthesize_blur_group(
            out_dir, list(GROUPS.keys()), target_per_group, min_side, writer, mf, seen_hashes
        )

    print("\nTổng kết số ảnh mỗi nhóm (đã tải trước + tải lần này):")
    total = 0
    for group, count in summary.items():
        print(f"  {group}: {count}")
        total += count
    print(f"  Tổng: {total}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=Path("data/negative"))
    parser.add_argument("--target-per-group", type=int, default=50)
    parser.add_argument("--min-side", type=int, default=MIN_SIDE)
    args = parser.parse_args()
    run(args.out_dir, args.target_per_group, args.min_side)
