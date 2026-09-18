"""Augmentation phá "lối tắt phong cách ảnh" cho bộ chặn 2 lớp (issue #92).

Vì sao cần: lớp dương của bộ chặn toàn ảnh PlantVillage (một phiến lá cắt rời,
nền xám đồng nhất, đèn phòng chụp) còn lớp âm toàn ảnh Internet (nền lộn xộn,
ánh sáng tự nhiên). Hai lớp **tách được bằng phong cách ảnh** nên mạng không cần
nhìn cái lá: bản huấn luyện đầu đạt recall 1,0000 trên tập test của chính nó và
0,9993 trên test PlantVillage, nhưng **chặn oan 92,0 % ảnh lá thật của PlantDoc**
— tức lúc chạy thật, ảnh nông dân chụp ngoài vườn sẽ bị từ chối gần như toàn bộ.

Cách chữa ở đây: làm cho **nền không còn mang thông tin về nhãn**. Tách phiến lá
khỏi nền xám rồi dán lên chính những tấm nền của lớp âm, nên cùng một cái nền
xuất hiện ở cả hai lớp — muốn phân biệt thì buộc phải nhìn vật thể. Kèm theo là
nắng gắt/bóng đổ mô phỏng ngoài trời.

⚠️ Chỉ lấy nền từ ảnh âm thuộc split **train**. Dùng nền của val/test là rò rỉ,
và kiểu rò rỉ này không báo lỗi gì — chỉ làm hai con số cuối đẹp lên vô cớ.

Mặt hạn chế phải nhớ khi báo cáo: đây vẫn là lá **cắt rời dán lên nền**, không
phải ảnh chụp cả bụi cây nhiều lá chồng nhau. Nó xoá được manh mối nền nhưng
không tạo ra được cảnh lộn xộn thật.
"""

from __future__ import annotations

import random
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from torch.utils.data import Dataset

from src.data.dataset import TomatoLeafDataset


def load_rgb_fast(path: Path, max_side: int = 640) -> Image.Image:
    """Mở ảnh và giải nén ở độ phân giải vừa đủ.

    Cần vì ảnh PlantDoc là ảnh web nhiều megapixel: giải nén full rồi mới resize
    về 224 làm epoch đầu đội từ ~25 giây lên hơn 25 phút (đo được, 83 s/batch).
    ``draft()`` bảo bộ giải mã JPEG nhả thẳng ở mức thu nhỏ nên nhanh hơn nhiều
    lần. Chỉ dùng cho **tập train của bộ chặn** — không đụng đường nạp ảnh dùng
    chung, vì nó ảnh hưởng số liệu đã báo cáo của mô hình bệnh.
    """
    image = Image.open(path)
    image.draft("RGB", (max_side, max_side))
    return image.convert("RGB")


def leaf_mask(rgb: np.ndarray) -> np.ndarray:
    """Mặt nạ phiến lá trên nền đồng nhất kiểu PlantVillage.

    Chỉ dùng **độ bão hoà màu**: lá xanh hoặc nâu bệnh đều bão hoà rõ, còn nền
    xám thì không — kể cả vùng bóng đổ, vì bóng chỉ làm nền tối đi chứ không làm
    nó có màu. Đo thử 30 ảnh: ngưỡng 40 cho diện tích mặt nạ trung vị 0,45, khớp
    với tỉ lệ phiến lá nhìn bằng mắt.

    ⚠️ Bản đầu còn cộng thêm điều kiện "khác xa màu nền lấy từ viền ảnh"
    (``dist > 60``) — **sai**: chính vùng bóng đổ cũng khác xa màu viền, nên mặt
    nạ nuốt luôn cả nền, diện tích trung vị vọt lên 0,95 và 18/40 ảnh bị bỏ qua
    vì chạm ngưỡng an toàn. Bỏ hẳn điều kiện đó.

    Không cần chính xác tuyệt đối — sai lệch ở đây là nhiễu augmentation, không
    phải số đo (khác hẳn mặt nạ dùng để chấm điểm Grad-CAM ở #17, chỗ đó sai một
    chút là hỏng kết luận).
    """
    sat = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)[..., 1].astype(np.int16)
    mask = (sat > 40).astype(np.uint8)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

    n, labels, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
    if n > 1:
        biggest = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
        mask = (labels == biggest).astype(np.uint8)

    # Co vào một chút: mặt nạ hay ăn theo mép bóng đổ của lá, để nguyên thì ảnh
    # ghép nào cũng có viền tối quanh lá — vừa xoá được manh mối nền lại vừa tạo
    # ra một manh mối mới đúng y như vậy.
    return cv2.erode(mask, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))


def composite_on_background(rgb: np.ndarray, bg_rgb: np.ndarray) -> np.ndarray:
    """Dán phiến lá lên một tấm nền khác, viền được làm mềm cho đỡ lộ."""
    mask = leaf_mask(rgb)
    # Mặt nạ quá nhỏ (tách hỏng) hoặc quá lớn (nền không đồng nhất) thì bỏ qua,
    # trả nguyên ảnh — thà mất một lượt augment còn hơn tạo ảnh rác.
    ratio = mask.mean()
    if ratio < 0.05 or ratio > 0.95:
        return rgb

    h, w = rgb.shape[:2]
    bg = cv2.resize(bg_rgb, (w, h), interpolation=cv2.INTER_AREA)
    alpha = cv2.GaussianBlur(mask.astype(np.float32), (5, 5), 0)[..., None]
    return (rgb * alpha + bg * (1 - alpha)).astype(np.uint8)


def harsh_outdoor_light(rgb: np.ndarray, rng: random.Random) -> np.ndarray:
    """Nắng gắt hoặc bóng đổ — thứ ảnh phòng chụp không bao giờ có."""
    out = rgb.astype(np.float32)
    gamma = rng.uniform(0.6, 1.6)
    out = 255.0 * np.power(out / 255.0, gamma)

    h, w = rgb.shape[:2]
    overlay = np.zeros((h, w), np.float32)
    cx, cy = rng.randint(0, w), rng.randint(0, h)
    radius = rng.randint(w // 4, w)
    cv2.circle(overlay, (cx, cy), radius, 1.0, -1)
    overlay = cv2.GaussianBlur(overlay, (0, 0), radius / 3.0)

    strength = rng.uniform(0.15, 0.45)
    if rng.random() < 0.5:                       # vệt nắng
        out = out + overlay[..., None] * 255.0 * strength
    else:                                        # bóng đổ
        out = out * (1.0 - overlay[..., None] * strength)

    return np.clip(out, 0, 255).astype(np.uint8)


def background_pool(gate_manifest: Path, split: str = "train") -> list[Path]:
    """Ảnh âm dùng làm nền — chỉ lấy từ split train, xem cảnh báo rò rỉ ở đầu file."""
    import csv

    with Path(gate_manifest).open(encoding="utf-8") as f:
        return [Path(r["path"]) for r in csv.DictReader(f)
                if r["label"] == "not_tomato_leaf" and r["split"] == split]


class DomainShortcutBreaker:
    """Áp cho ảnh **lớp dương** trước khi vào pipeline augment thường."""

    def __init__(self, background_paths: list[Path], p_background: float = 0.7,
                 p_light: float = 0.5, seed: int = 42) -> None:
        self.background_paths = background_paths
        self.p_background = p_background
        self.p_light = p_light
        self._seed = seed

    def __call__(self, image: Image.Image) -> Image.Image:
        # Seed theo từng lần gọi để mỗi worker của DataLoader không lặp lại
        # cùng một chuỗi ngẫu nhiên.
        rng = random.Random(random.getrandbits(32))
        rgb = np.asarray(image.convert("RGB"))

        if self.background_paths and rng.random() < self.p_background:
            bg_path = rng.choice(self.background_paths)
            bg = np.asarray(load_rgb_fast(bg_path, max_side=512))
            # Cắt ngẫu nhiên một mảng nền thay vì luôn dùng cả tấm, để cùng một
            # ảnh nền cho ra nhiều nền khác nhau.
            bh, bw = bg.shape[:2]
            side = rng.randint(min(bh, bw) // 2, min(bh, bw))
            y = rng.randint(0, bh - side)
            x = rng.randint(0, bw - side)
            rgb = composite_on_background(rgb, bg[y:y + side, x:x + side])

        if rng.random() < self.p_light:
            rgb = harsh_outdoor_light(rgb, rng)

        return Image.fromarray(rgb)


class GateTrainDataset(Dataset):
    """Như ``TomatoLeafDataset`` nhưng augment **theo nguồn ảnh**.

    Phải là dataset riêng chứ không phải một transform cắm vào pipeline chung,
    vì phép ghép nền chỉ có nghĩa với **ảnh dương của PlantVillage**:

    - Ảnh âm vốn đã có nền lộn xộn thật, ghép thêm nền nữa chỉ làm hỏng ảnh.
    - Ảnh dương **PlantDoc** cũng vậy, và còn tệ hơn: ``leaf_mask`` giả định nền
      xám đồng nhất kiểu phòng chụp, đem áp lên ảnh đồng ruộng thì mặt nạ ra
      rác. Chính chúng là ảnh mang nền thật vào cho bộ chặn học — ghép đè lên là
      xoá mất thứ ta vừa mất công thêm vào.
    """

    def __init__(self, manifest: str | Path, split: str, transform,
                 keys: list[str], breaker: DomainShortcutBreaker) -> None:
        self.inner = TomatoLeafDataset(manifest, split, transform=None, keys=keys)
        self.transform = transform
        self.breaker = breaker
        self.positive_idx = keys.index("tomato_leaf")

    def __len__(self) -> int:
        return len(self.inner)

    def __getitem__(self, idx: int):
        path, label = self.inner.samples[idx]
        image = load_rgb_fast(path)
        # "data/field/" = ảnh đồng ruộng (PlantDoc) -> giữ nguyên nền thật.
        is_lab_positive = label == self.positive_idx and "field" not in path.parts
        if is_lab_positive:
            image = self.breaker(image)
        return self.transform(image), label

    @property
    def keys(self) -> list[str]:
        return self.inner.keys

    @property
    def class_counts(self) -> list[int]:
        return self.inner.class_counts
