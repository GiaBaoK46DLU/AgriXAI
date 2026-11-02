"""Tạo báo cáo Word ngắn từ số đo và bản đồ đã lưu của #98."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
import numpy as np
from PIL import Image
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.evaluation.compare_xai import dump, sha256
from src.evaluation.compare_gradcam_plusplus import text_sha256
from src.predictor import DiseasePredictor

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "outputs/gradcam-plus-plus-98"
OUTPUT = ROOT.parent / "docx/bao-cao-nang-cap-gradcam-plus-plus.docx"


def number(value, digits=3, percent=False):
    return f"{value * (100 if percent else 1):.{digits}f}".replace(".", ",") + ("%" if percent else "")


def make_figures(records):
    sys.path.insert(0, str(ROOT.parent / "backend"))
    from app.services.xai.overlay import draw_regions

    figures = BASE / "report-figures"
    figures.mkdir(exist_ok=True)
    samples = json.loads((BASE / "protocol.json").read_text(encoding="utf-8"))["samples"]
    paths = {r["sample_id"]: ROOT / r["path"] for r in samples}
    for sample_id in ("pv-septoria_leaf_spot-2", "pd-septoria_leaf_spot-2"):
        image = Image.open(paths[sample_id]).convert("RGB")
        maps = np.load(BASE / "maps" / f"{sample_id}.npz")
        for kind in ("heatmap", "contour"):
            fig, axes = plt.subplots(1, 3, figsize=(10, 3.55))
            axes[0].imshow(image.resize((224, 224)))
            axes[0].set_title("Ảnh gốc", fontsize=12)
            for axis, method, title in zip(axes[1:], ("gradcam", "gradcam_plusplus"), ("Grad-CAM", "Grad-CAM++")):
                if kind == "heatmap":
                    base = np.asarray(image.resize((224, 224)), dtype=np.float32) / 255
                    panel = np.clip(.55 * base + .45 * plt.get_cmap("jet")(maps[method])[..., :3], 0, 1)
                else:
                    full = DiseasePredictor._resize_heatmap(maps[method], *image.size)
                    panel = draw_regions(image, full, .62).resize((224, 224))
                axis.imshow(panel)
                axis.set_title(title, fontsize=12)
            for axis in axes:
                axis.axis("off")
            fig.tight_layout(rect=(0, 0, 1, .93), pad=.8)
            fig.savefig(figures / f"{sample_id}-{kind}.png", dpi=170, facecolor="white",
                        bbox_inches="tight", pad_inches=.12)
            plt.close(fig)
        maps.close()
    return figures


def build():
    summary = json.loads((BASE / "summary.json").read_text(encoding="utf-8"))
    records = json.loads((BASE / "per-image.json").read_text(encoding="utf-8"))
    figures = make_figures(records)
    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21), Cm(29.7)
    sec.top_margin, sec.bottom_margin = Cm(1.7), Cm(1.7)
    sec.left_margin, sec.right_margin = Cm(2), Cm(2)
    for name in ("Normal", "Caption", "Heading 1", "Heading 2", "Title"):
        style = doc.styles[name]
        style.font.name = "Times New Roman"
        style.element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), "Times New Roman")
        style.font.color.rgb = RGBColor.from_string("000000")
    normal = doc.styles["Normal"]
    normal.font.size = Pt(11.5)
    normal.paragraph_format.line_spacing = 1.08
    normal.paragraph_format.space_after = Pt(5)
    for name in ("Heading 1", "Heading 2"):
        doc.styles[name].font.size = Pt(13)
        doc.styles[name].paragraph_format.space_before = Pt(7)
        doc.styles[name].paragraph_format.space_after = Pt(5)
    doc.styles["Caption"].font.size = Pt(10)
    doc.styles["Caption"].font.italic = True
    doc.core_properties.title = "Nâng cấp Grad-CAM++ trong AgriXAI"
    doc.core_properties.author = "Nhóm 3 - AgriXAI"
    doc.core_properties.subject = "Thực nghiệm XAI và triển khai mặc định - task #98"

    footer = sec.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = footer.add_run("AgriXAI | ")
    run.font.size = Pt(9)
    field = OxmlElement("w:fldSimple")
    field.set(qn("w:instr"), "PAGE")
    footer._p.append(field)

    def p(text, bold=False, style=None):
        paragraph = doc.add_paragraph(style=style)
        paragraph.add_run(text).bold = bold
        return paragraph

    def heading(text):
        doc.add_heading(text, level=1)

    def caption(text, keep_next=False):
        paragraph = p(text, style="Caption")
        paragraph.paragraph_format.keep_with_next = keep_next

    def table(headers, rows, widths):
        obj = doc.add_table(rows=1, cols=len(headers))
        obj.style = "Table Grid"
        obj.alignment = WD_TABLE_ALIGNMENT.CENTER
        obj.autofit = False
        for i, width in enumerate(widths):
            obj.columns[i].width = Cm(width)
        for values, row in [(headers, obj.rows[0])] + [(values, obj.add_row()) for values in rows]:
            no_split = OxmlElement("w:cantSplit")
            row._tr.get_or_add_trPr().append(no_split)
            for i, value in enumerate(values):
                cell = row.cells[i]
                cell.width = Cm(widths[i])
                cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
                paragraph = cell.paragraphs[0]
                paragraph.paragraph_format.space_after = Pt(3)
                paragraph.paragraph_format.space_before = Pt(3)
                run = paragraph.add_run(str(value))
                run.font.size = Pt(10)
                if row is obj.rows[0]:
                    run.bold = True
        # python-docx trả wrapper hàng mới mỗi lần: đánh dấu header theo XML.
        header = obj.rows[0]
        flag = OxmlElement("w:tblHeader")
        header._tr.get_or_add_trPr().append(flag)
        for cell in header.cells:
            shade = OxmlElement("w:shd")
            shade.set(qn("w:fill"), "E8F1EA")
            cell._tc.get_or_add_tcPr().append(shade)
            for run in cell.paragraphs[0].runs:
                run.bold = True
        p("")

    def picture(path, title):
        paragraph = doc.add_paragraph()
        paragraph.paragraph_format.space_after = Pt(2)
        paragraph.paragraph_format.keep_with_next = True
        shape = paragraph.add_run().add_picture(str(path), width=Cm(17))
        shape._inline.docPr.set("descr", title)
        caption(title)

    title = p("BÁO CÁO NÂNG CẤP GRAD-CAM++", bold=True)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.runs[0].font.size = Pt(17)
    subtitle = p("Ứng dụng AgriXAI - Task #98 - Ngày 02/11/2026")
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    heading("1. Mục tiêu và kết quả nổi bật")
    p("Nâng cấp phương pháp giải thích từ Grad-CAM lên Grad-CAM++ nhằm cải thiện cách mô hình "
      "tập trung vào vùng lá và dấu hiệu bệnh. Mô hình phân loại EfficientNet-B0 và checkpoint "
      "được giữ nguyên; nâng cấp này tác động tới bản đồ giải thích, không phải huấn luyện lại bộ nhận diện.")
    p("Kết quả gộp cho thấy cải thiện về tập trung chú ý: trên 52 ảnh có tham chiếu hợp lệ, "
      "khối lượng heatmap nằm trong lá tăng từ 71,69% lên 78,11%; trên 20 ảnh dự đoán đúng có "
      "triệu chứng khu trú, mức nâng vào vết bệnh tăng từ 0,128 lên 0,160.", bold=True)
    heading("2. Grad-CAM++ khác Grad-CAM ở đâu?")
    p("Bảng 1 đối chiếu trực tiếp hai phương pháp trên cùng mô hình và cùng tầng đặc trưng.")
    caption("Bảng 1. So sánh nguyên lý và đặc điểm triển khai", True)
    table(["Tiêu chí", "Grad-CAM", "Grad-CAM++"], [
        ["Trọng số từng kênh", "Trung bình gradient theo không gian.", "Tổng gradient dương với hệ số alpha theo từng vị trí."],
        ["Cơ chế chú ý", "Một trọng số chung cho mỗi kênh.", "Xét đóng góp theo vị trí trước khi tổng hợp trọng số kênh."],
        ["Ưu thế kỳ vọng", "Đơn giản, làm mốc đối chứng.", "Hỗ trợ giải thích nhiều vùng cùng lớp; phải kiểm chứng trên dữ liệu đích."],
        ["Chi phí thuật toán", "Một lượt forward và gradient cho lớp mục tiêu.", "Một lượt forward và gradient, thêm phép tính trọng số alpha."],
        ["Độ phân giải trong đề tài", "Lưới đặc trưng 7×7, nội suy về ảnh gốc.", "Vẫn là 7×7; không tự tạo phân vùng vết bệnh chi tiết."],
        ["Checkpoint phân loại", "EfficientNet-B0 hiện có.", "Dùng cùng checkpoint, giữ nguyên xác suất phân loại."],
    ], [4, 6.5, 6.5])
    heading("3. Căn cứ lựa chọn Grad-CAM++")
    p("Thứ nhất, có cải thiện định lượng về tập trung chú ý trên tập ảnh đánh giá gộp, thay vì chỉ "
      "nhận xét hình đẹp hơn. Thứ hai, giữ đầu ra heatmap theo không gian ảnh để tiếp tục tạo "
      "contour và câu giải thích tiếng Việt. Thứ ba, không cần dữ liệu huấn luyện mới hay thay "
      "hợp đồng Prediction giữa mô hình và backend.")
    p("Nhóm tự cài công thức và đối chiếu với pytorch-grad-cam 1.5.5 trên cả 56 ảnh: sai số bản đồ "
      "lớn nhất 1,49 × 10⁻⁶; IoU hai mặt nạ ngưỡng 0,62 bằng 1,0000. Đây là bằng chứng kiểm "
      "chứng triển khai, không phải độ chính xác phân vùng bệnh.")

    doc.add_page_break()
    heading("4. Thiết kế và kết quả thực nghiệm")
    p("Dùng 56 ảnh cố định từ phép kiểm #17, có nguồn PlantVillage và PlantDoc; báo cáo tính gộp "
      "theo từng ảnh, không chia bảng theo nguồn. Hai phương pháp dùng cùng ảnh đầu vào, lớp "
      "mục tiêu và checkpoint. Contour được tạo bằng đúng hàm backend, ngưỡng 0,62.")
    p("Tham chiếu là lưới 14×14 do AI khoanh mù, chưa được chuyên gia xác nhận. Loại 4 ảnh "
      "có cờ dữ liệu đáng ngờ khỏi chỉ số không gian (còn 52 ảnh); nâng chuẩn hóa vào lá dùng "
      "48 ảnh do 4 ảnh lá phủ kín khung không có mẫu số hợp lệ. Vết bệnh chỉ đo trên 20 ảnh "
      "dự đoán đúng, triệu chứng khu trú. Kết quả gộp chưa đại diện cho mọi điều kiện chụp.")
    def mean(dataset, method, metric):
        return summary["by_dataset"][dataset][method][metric]["mean"]
    positive_specs = [
        ("Khối lượng heatmap trong lá (52 ảnh) ↑", "all", "leaf_mass", 2, True),
        ("Tập trung vào lá so với rải đều (52 ảnh) ↑", "all", "leaf_concentration", 3, False),
        ("Nâng chuẩn hóa vào lá (48 ảnh) ↑", "all", "leaf_lift", 3, False),
        ("Khối lượng heatmap trong vết bệnh (20 ảnh) ↑", "all", "lesion_mass", 2, True),
        ("Nâng vào vết bệnh, ảnh đúng/khu trú (20 ảnh) ↑", "all", "lesion_lift", 3, False),
        ("IoU contour/vết bệnh, ảnh đúng/khu trú (20 ảnh) ↑", "all", "overlay_lesion_iou", 3, False),
        ("Thời gian tạo CAM của cài đặt hiện tại (ms) ↓", "all", "explain_ms", 2, False),
    ]
    rows = [[label] + [number(mean(dataset, method, metric), digits, percent) for method in ("gradcam", "gradcam_plusplus")]
            for label, dataset, metric, digits, percent in positive_specs]
    caption("Bảng 2. So sánh định lượng trên tập đánh giá gộp", True)
    table(["Chỉ số và phạm vi đo", "Grad-CAM", "Grad-CAM++"], rows, [10, 3.5, 3.5])
    p("↑ tốt hơn khi tăng, ↓ tốt hơn khi giảm. Nâng chuẩn hóa bằng 0 tương ứng "
      "rải đều, bằng 1 tương ứng toàn bộ khối lượng chú ý nằm trong vùng tham chiếu. IoU đo độ "
      "chồng lấp vùng khoanh và tham chiếu; không đồng nghĩa với accuracy phân loại.")
    specs = [("Điểm nóng lưới nằm trong lá (52 ảnh) ↑", "peak_in_leaf", 2, True),
             ("Contour hiển thị nằm ngoài lá (52 ảnh) ↓", "overlay_outside_leaf", 2, True)]
    rows = [[label] + [number(mean("all", method, metric), digits, percent) for method in ("gradcam", "gradcam_plusplus")]
            for label, metric, digits, percent in specs]
    caption("Bảng 3. Kiểm tra bổ sung về vị trí điểm nóng và vùng khoanh", True)
    table(["Chỉ số và phạm vi đo", "Grad-CAM", "Grad-CAM++"], rows, [10, 3.5, 3.5])
    p("Khối lượng chú ý trong lá tăng 6,43 điểm phần trăm (KTC 95%: 3,68–9,36 điểm). Nâng vào "
      "vết bệnh tăng 0,032 (KTC: 0,012–0,055). Phần contour ngoài lá tăng 4,98 điểm phần trăm "
      "(KTC: 1,19–9,11 điểm). IoU vết bệnh gộp tăng 0,012 nhưng "
      "KTC −0,008–0,034 còn chứa 0, nên chưa chứng minh contour tốt hơn tổng thể.")
    p("Thời gian đo trên CPU i5-13400F, 4 luồng, 3 lần/ảnh sau khởi động; không gồm mạng, vẽ "
      "contour hoặc giao diện. Bản ++ dùng autograd.grad tới activation, bản cũ dùng backward "
      "toàn đồ thị: khác biệt tốc độ còn do tối ưu cài đặt, không chứng minh ++ vốn nhanh hơn.")

    doc.add_page_break()
    heading("5. Hình ảnh minh họa cải thiện")
    p("Hình 1 và Hình 2 dùng cùng ảnh minh họa A, cùng lớp mục tiêu. Bản ++ tăng "
      "tập trung vào phần giữa lá và bổ sung contour ở vùng này; vùng sát mép phía trên vẫn còn. "
      "Đây là ca minh họa, còn bảng thống kê dùng toàn bộ tập cố định.")
    picture(figures / "pv-septoria_leaf_spot-2-heatmap.png",
            "Hình 1. So sánh bản đồ nhiệt Grad-CAM và Grad-CAM++ trên lá bị đốm Septoria (mẫu A).")
    picture(figures / "pv-septoria_leaf_spot-2-contour.png",
            "Hình 2. Vùng khoanh đầu ra trên cùng ảnh: bản ++ bổ sung vùng giữa lá; chưa loại hết vùng sát nền.")
    sample = {r["method"]: r for r in records if r["sample_id"] == "pv-septoria_leaf_spot-2"}
    leaf_delta = 100 * (sample["gradcam_plusplus"]["leaf_mass"] - sample["gradcam"]["leaf_mass"])
    iou_delta = sample["gradcam_plusplus"]["overlay_lesion_iou"] - sample["gradcam"]["overlay_lesion_iou"]
    p(f"Trên ảnh minh họa, mức tăng khối lượng heatmap trong lá khoảng {number(leaf_delta, 2)} điểm phần trăm "
      f"và IoU contour/vết bệnh tăng khoảng {number(iou_delta)}. Sự thay đổi này thể hiện hiệu quả về phân bố "
      "chú ý trong trường hợp cụ thể, không bảo đảm mọi đốm bệnh đều được khoanh đúng.")

    doc.add_page_break()
    heading("6. Ca khó và triển khai mặc định")
    p("Hình 3 và Hình 4 dùng ảnh minh họa B. Cả hai phương pháp cùng giải thích "
      "dự đoán sai của mô hình phân loại; bản ++ vẫn có vùng khoanh ngoài lá. Kết quả này minh "
      "họa vì sao cần tách chất lượng giải thích khỏi độ chính xác chẩn đoán.")
    picture(figures / "pd-septoria_leaf_spot-2-heatmap.png",
            "Hình 3. So sánh bản đồ nhiệt trên ca khó (mẫu B): nâng cấp XAI chưa sửa được dự đoán sai.")
    picture(figures / "pd-septoria_leaf_spot-2-contour.png",
            "Hình 4. Contour của hai phương pháp trên mẫu B; giữ nguyên ngưỡng 0,62 để so công bằng.")
    p("Dự án đã đặt xai.method = gradcam_plusplus làm mặc định cho server PyTorch theo quyết "
      "định triển khai ngày 02/11/2026. Lựa chọn dựa trên cải thiện ở nhóm ảnh đã đo, đầu ra "
      "phù hợp luồng XAI và cài đặt đã được kiểm chứng; chấp nhận các hạn chế ở Bảng 3. Có thể "
      "quay lại gradcam bằng cấu hình, không đổi checkpoint.", bold=True)
    p("Nhánh ngoại tuyến trên điện thoại giữ CAM cổ điển nên vùng khoanh có thể khác server. "
      "Đã chạy 23 test và kiểm tra cấu hình mặc định, ảnh không vuông, bộ chặn ảnh âm; cần "
      "khởi động lại backend đang chạy để nạp lựa chọn mới.")
    p("Nguồn: Chattopadhyay và cộng sự, Grad-CAM++, arXiv:1710.11063v3, công thức (7), (19); "
      "pytorch-grad-cam 1.5.5. Số đo và 56 hình gốc: model/outputs/gradcam-plus-plus-98/. "
      "Chi tiết phương pháp, khoảng tin cậy và lệnh chạy lại: docx/bao-cao-gradcam-plus-plus.md.")
    OUTPUT.parent.mkdir(exist_ok=True)
    doc.save(OUTPUT)
    dump(BASE / "report-manifest.json", {"document": OUTPUT.relative_to(ROOT.parent).as_posix(),
         "document_sha256": sha256(OUTPUT), "generator_sha256": text_sha256(Path(__file__)),
         "summary_sha256": text_sha256(BASE / "summary.json"),
         "text_hash_mode": "sha256, CRLF normalized to LF",
         "figures": {p.name: sha256(p) for p in sorted(figures.glob("*.png"))},
         "tables": 3, "figures_count": 4, "aggregation": "pooled by image",
         "illustrations": {"A": "pv-septoria_leaf_spot-2", "B": "pd-septoria_leaf_spot-2"}})
    print(OUTPUT)


if __name__ == "__main__":
    build()
