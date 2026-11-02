"""Sinh hình và báo cáo Word từ kết quả thật của phép so sánh #122."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image

from src.labels import key_to_name_vi

ROOT = Path(__file__).resolve().parents[2]
NAMES = {"gradcam": "Grad-CAM", "lime": "LIME", "kernel_shap": "Kernel SHAP"}
COLORS = {"gradcam": "#2E6F40", "lime": "#D28E22", "kernel_shap": "#5369A7"}
METHODS = tuple(NAMES)


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def number(value, digits=2):
    return f"{value:,.{digits}f}".replace(",", " ").replace(".", ",")


def estimate(entry, scale=1, digits=2):
    return f'{number(entry["mean"] * scale, digits)} [{number(entry["ci95"][0] * scale, digits)}; {number(entry["ci95"][1] * scale, digits)}]'


def make_figures(base: Path, mode="all"):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    quality, cpu = base / "quality", base / "cpu"
    figures = base / "figures"
    figures.mkdir(exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                         "axes.spines.top": False, "axes.spines.right": False})
    if mode not in ("quality", "comparison"):
        summary = read(cpu / "summary.json")["by_dataset"]["all"]
        fig, ax = plt.subplots(figsize=(8.4, 2.5), layout="constrained")
        positions = np.arange(3)
        means = [summary[m]["total_ms"]["mean"] for m in METHODS]
        low = [means[i] - summary[m]["total_ms"]["ci95"][0] for i, m in enumerate(METHODS)]
        high = [summary[m]["total_ms"]["ci95"][1] - means[i] for i, m in enumerate(METHODS)]
        ax.barh(positions, means, color=[COLORS[m] for m in METHODS], height=0.55)
        ax.errorbar(means, positions, xerr=np.array([low, high]), fmt="none", color="black", capsize=3)
        ax.set_yticks(positions, [NAMES[m] for m in METHODS])
        ax.invert_yaxis()
        ax.set_xscale("log")
        ax.set_xlim(left=max(means[0] / 2, 1), right=max(summary[m]["total_ms"]["ci95"][1] for m in METHODS) * 3)
        ax.set_xlabel("Thời gian tạo giải thích trên CPU (ms, trục logarit)")
        for y, method, value in zip(positions, METHODS, means):
            label_x = summary[method]["total_ms"]["ci95"][1] * 1.1
            ax.text(label_x, y + .1, f"{number(value, 1)} ms", fontsize=9)
        fig.savefig(figures / "thoi-gian-cpu.png", dpi=220)
        plt.close(fig)
        if mode == "runtime":
            return figures

    # Chốt trước khi xem kết quả: ảnh đầu tiên của bacterial_spot và late_blight ở mỗi miền.
    chosen = ["pv-bacterial_spot-1", "pv-late_blight-1", "pd-bacterial_spot-1", "pd-late_blight-1"]
    labels = key_to_name_vi()
    fig, axes = plt.subplots(4, 4, figsize=(10.8, 11.2), layout="constrained")
    for row, sample_id in enumerate(chosen):
        image = np.asarray(Image.open(quality / "images" / f"{sample_id}.png"))
        records = {method: read(quality / "records" / f"{sample_id}--{method}--42.json") for method in METHODS}
        original = records["gradcam"]
        for col in range(4):
            axes[row, col].imshow(image)
            axes[row, col].set_xticks([])
            axes[row, col].set_yticks([])
            for spine in axes[row, col].spines.values():
                spine.set_visible(False)
            if col:
                method = METHODS[col - 1]
                heatmap = np.load(quality / "maps" / f"{sample_id}--{method}--42.npz")["heatmap"]
                normalized = heatmap / max(float(heatmap.max()), 1e-12)
                axes[row, col].imshow(normalized, cmap="magma", vmin=0, vmax=1, alpha=normalized * .78)
            if row == 0:
                axes[row, col].set_title("Ảnh đầu vào" if col == 0 else NAMES[METHODS[col - 1]], fontsize=18)
        source = "PlantVillage" if sample_id.startswith("pv") else "PlantDoc"
        axes[row, 0].set_ylabel(source + "\n" + labels[original["label"]], fontsize=13)
        axes[row, 0].set_xlabel("Dự đoán: " + labels[original["predicted"]] +
                                f'\n{number(original["confidence"] * 100, 1)}%', fontsize=13)
    fig.savefig(figures / "doi-chieu-4-anh.png", dpi=220)
    plt.close(fig)
    if mode == "comparison":
        return figures

    # Toàn bộ 56 ảnh đều có output; không chỉ lưu những ảnh được đưa vào báo cáo.
    gallery = base / "gallery"
    gallery.mkdir(exist_ok=True)
    for image_path in sorted((quality / "images").glob("*.png")):
        sample_id = image_path.stem
        image = np.asarray(Image.open(image_path))
        fig, axes = plt.subplots(1, 4, figsize=(10, 2.8), layout="constrained")
        for index, ax in enumerate(axes):
            ax.imshow(image)
            ax.axis("off")
            ax.set_title("Ảnh đầu vào" if not index else NAMES[METHODS[index - 1]], fontsize=10)
            if index:
                heatmap = np.load(quality / "maps" / f"{sample_id}--{METHODS[index - 1]}--42.npz")["heatmap"]
                normalized = heatmap / max(float(heatmap.max()), 1e-12)
                ax.imshow(normalized, cmap="magma", vmin=0, vmax=1, alpha=normalized * .78)
        fig.suptitle(sample_id + " | cùng lớp dự đoán | seed 42", fontsize=10)
        fig.savefig(gallery / f"{sample_id}.png", dpi=140)
        plt.close(fig)
    return figures


def make_docx(base: Path, target: Path, figures: Path):
    from docx import Document
    from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Cm, Pt, RGBColor

    q = read(base / "quality/summary.json")
    c = read(base / "cpu/summary.json")
    protocol = read(base / "quality/protocol.json")
    cpu_protocol = read(base / "cpu/protocol.json")
    qs, cs = q["by_dataset"]["all"], c["by_dataset"]["all"]
    times = {m: cs[m]["total_ms"]["mean"] for m in METHODS}
    ratios = {m: times[m] / times["gradcam"] for m in METHODS[1:]}
    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21), Cm(29.7)
    sec.top_margin, sec.bottom_margin = Cm(1.7), Cm(1.7)
    sec.left_margin, sec.right_margin = Cm(2), Cm(2)
    sec.footer_distance = Cm(1)
    normal = doc.styles["Normal"]
    normal.font.name, normal.font.size = "Times New Roman", Pt(11.5)
    normal.font.bold, normal.font.italic = False, False
    normal.font.color.rgb = RGBColor(0, 0, 0)
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.line_spacing = 1.08
    for name, size in (("Title", 21), ("Heading 1", 15), ("Heading 2", 12.5)):
        style = doc.styles[name]
        style.font.name, style.font.size = "Times New Roman", Pt(size)
        style.font.color.rgb = RGBColor(0, 0, 0)
        style.font.bold = True
        style.font.underline = False
        style.paragraph_format.space_before = Pt(9)
        style.paragraph_format.space_after = Pt(6)
    # Template đi kèm thư viện có thể có đường kẻ xanh dưới Title.
    # Loại đường kẻ kế thừa để tiêu đề chỉ dùng chữ và khoảng trắng.
    for style in doc.styles:
        if style.type == 1:
            props = style.element.find(qn("w:pPr"))
            if props is not None:
                for border in list(props.findall(qn("w:pBdr"))):
                    props.remove(border)
    doc.core_properties.title = "So sánh Grad-CAM LIME và SHAP trong AgriXAI"
    doc.core_properties.subject = "Thực nghiệm lựa chọn phương pháp giải thích mô hình ảnh"
    doc.core_properties.author = "Nhóm 3 - AgriXAI"
    doc.core_properties.created = doc.core_properties.modified = datetime.now(timezone.utc)
    footer = sec.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    footer_style = doc.styles["Footer"]
    footer_style.font.name, footer_style.font.size = "Times New Roman", Pt(9)
    footer_style.font.bold = False
    footer_style.font.color.rgb = RGBColor(0, 0, 0)
    footer.add_run("AgriXAI | ").font.size = Pt(9)
    field = OxmlElement("w:fldSimple")
    field.set(qn("w:instr"), "PAGE")
    footer._p.append(field)

    def p(text, bold=False):
        para = doc.add_paragraph()
        para.paragraph_format.widow_control = True
        para.add_run(text).bold = bold
        return para

    def heading(text, level=1):
        return doc.add_heading(text, level=level)

    def caption(text):
        para = p(text)
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for run in para.runs:
            run.font.size, run.italic = Pt(10), True
        return para

    def table(headers, rows, widths):
        tab = doc.add_table(rows=1, cols=len(headers))
        tab.alignment = WD_TABLE_ALIGNMENT.CENTER
        tab.autofit = False
        for col, width in zip(tab.columns, widths):
            col.width = Cm(width)
        for index, text in enumerate(headers):
            tab.rows[0].cells[index].text = text
        for row in rows:
            for cell, text in zip(tab.add_row().cells, row):
                cell.text = str(text)
        for row_index, row in enumerate(tab.rows):
            props = row._tr.get_or_add_trPr()
            props.append(OxmlElement("w:cantSplit"))
            if row_index == 0:
                props.append(OxmlElement("w:tblHeader"))
            for index, cell in enumerate(row.cells):
                cell.width = Cm(widths[index])
                cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
                tcpr = cell._tc.get_or_add_tcPr()
                shade = OxmlElement("w:shd")
                shade.set(qn("w:fill"), "E5EDE6" if row_index == 0 else ("F5F5F5" if row_index % 2 == 0 else "FFFFFF"))
                tcpr.append(shade)
                for para in cell.paragraphs:
                    para.paragraph_format.space_after = Pt(4)
                    para.paragraph_format.space_before = Pt(4)
                    for run in para.runs:
                        run.font.name, run.font.size = "Times New Roman", Pt(10)
                        run.bold = row_index == 0
        doc.add_paragraph().paragraph_format.space_after = Pt(0)
        return tab

    # Trang 1: khái niệm, phương pháp, không coi XAI là mô hình phân loại mới.
    doc.add_heading("So sánh Grad-CAM LIME và SHAP trong AgriXAI", 0)
    p("Báo cáo thực nghiệm lựa chọn phương pháp giải thích mô hình ảnh | 02/11/2026")
    p(f'Kết quả chính: trên phép đo CPU gồm {c["image_count"]} ảnh và ba seed, Grad-CAM mất trung bình '
      f'{number(times["gradcam"], 1)} ms/ảnh; nhanh hơn LIME {number(ratios["lime"], 1)} lần và Kernel SHAP '
      f'{number(ratios["kernel_shap"], 1)} lần. Lợi thế được xác lập là chi phí tạo giải thích và tính phù hợp '
      'với luồng tương tác; chất lượng định vị được phân tích riêng, không suy từ tốc độ.', bold=True)
    heading("1 Khái niệm và nguyên lý")
    p("XAI là các phương pháp giúp diễn giải hành vi của mô hình. Ba phương pháp trong báo cáo đều tạo giải thích "
      "hậu nghiệm cho cùng một bộ phân loại EfficientNet-B0 đã huấn luyện. Chúng không tạo ba mức accuracy phân loại "
      "khác nhau. Đối tượng so sánh là vùng giải thích, độ ổn định và chi phí tính toán.")
    heading("1.1 Grad-CAM", 2)
    p("Grad-CAM lấy đạo hàm (gradient) của điểm số lớp mục tiêu đối với bản đồ đặc trưng (feature map) tại tầng tích chập. Trung bình gradient "
      "theo không gian tạo trọng số cho mỗi kênh; cộng các feature map có trọng số, áp dụng ReLU rồi nội suy về ảnh "
      "đầu vào [1]. Trong AgriXAI, tầng cuối tạo bản đồ 7 × 7 và giải thích điểm số trước softmax (logit) của lớp dự đoán. Mỗi ảnh cần một "
      "lượt tính xuôi (forward) và một lượt lan truyền ngược (backward). Bản đồ là vùng ảnh ảnh hưởng đến quyết định, không phải mặt nạ vết bệnh.")
    heading("1.2 LIME", 2)
    p("LIME chia ảnh thành các vùng nhỏ đồng nhất (superpixel), tạo nhiều ảnh bằng cách che các tổ hợp vùng, rồi hỏi lại bộ phân loại. "
      "Một mô hình tuyến tính có trọng số khoảng cách được khớp quanh ảnh gốc để xấp xỉ hành vi cục bộ. Hệ số của "
      "mỗi vùng biểu diễn đóng góp hỗ trợ hoặc chống lại lớp đang giải thích [2]. LIME không cần gradient, nhưng "
      "phụ thuộc cách chia vùng, cách che và ngân sách lấy mẫu.")
    p("Có thể hiểu LIME là cách học một lời giải thích đơn giản quanh một ảnh cụ thể. Nếu các tổ hợp giữ lại một vùng "
      "thường hỗ trợ điểm dự đoán, vùng đó có thể nhận hệ số dương. Hệ số được ước lượng từ nhiều tổ hợp, không chỉ từ "
      "một lần che vùng; lời giải thích này không mô tả toàn bộ hành vi của CNN trên mọi ảnh.")
    heading("1.3 SHAP và biến thể được chạy", 2)
    p("SHAP gán giá trị đóng góp dựa trên giá trị Shapley: xét mức thay đổi đầu ra khi một đặc trưng tham gia các "
      "tổ hợp đặc trưng khác nhau [3]. Phép thử sử dụng Kernel SHAP, hồi quy tuyến tính với trọng số Shapley trên "
      "các vùng ảnh, cùng nền che và cùng hàm xác suất với LIME [5]. SHAP còn có các biến thể khác; kết luận ở đây "
      "chỉ áp dụng cấu hình Kernel SHAP đã đo.")
    p("Khác với hồi quy cục bộ của LIME, Kernel SHAP dùng trọng số được xây dựng để ước lượng đóng góp Shapley. "
      "Đóng góp của một vùng được xét trong nhiều tổ hợp với các vùng còn lại. Trong cấu hình identity link, tổng "
      "các đóng góp cộng với giá trị tham chiếu khớp với xác suất lớp đang giải thích; đây không phải xác suất mỗi vùng bị bệnh.")

    doc.add_page_break()
    heading("1.4 So sánh trực tiếp ba phương pháp", 2)
    p("Bảng 1 phân biệt nguồn thông tin, cách tính và ý nghĩa đầu ra. Các phương pháp cùng giải thích một dự đoán, "
      "nhưng không đưa ra cùng một loại đại lượng đóng góp. Grad-CAM tận dụng tín hiệu bên trong CNN; LIME và "
      "Kernel SHAP quan sát phản ứng của mô hình trước các tổ hợp vùng ảnh bị che.")
    caption("Bảng 1 So sánh nguyên lý và yêu cầu triển khai")
    table(["Tiêu chí", "Grad-CAM", "LIME", "Kernel SHAP"], [
        ["Thông tin cần truy cập", "Tầng tích chập và gradient của CNN", "Hàm nhận ảnh và trả dự đoán", "Hàm nhận ảnh và trả dự đoán"],
        ["Cách tạo giải thích", "Kết hợp feature map bằng trọng số gradient", "Khớp mô hình tuyến tính cục bộ trên các ảnh bị che", "Ước lượng đóng góp Shapley qua hồi quy có trọng số"],
        ["Đơn vị trong phép thử", "Feature map 7 × 7, nội suy về ảnh", "Các vùng SLIC được giữ hoặc che", "Cùng các vùng SLIC được giữ hoặc che"],
        ["Ý nghĩa đầu ra", "Vùng ảnh hỗ trợ điểm số lớp mục tiêu", "Hệ số hỗ trợ/chống lại dự đoán của mô hình xấp xỉ", "Đóng góp tăng/giảm đầu ra so với nền tham chiếu"],
        ["Ưu thế phù hợp", "CNN có gradient, cần giải thích theo ảnh với chi phí thấp", "Chỉ truy cập được đầu vào/đầu ra, cần xấp xỉ cục bộ", "Cần phân bổ đóng góp có dấu theo cơ sở Shapley"]
    ], [3.1, 4.6, 4.6, 4.7])
    heading("Ví dụ trong bài toán bệnh lá", 2)
    p("Với cùng ảnh được dự đoán là đốm lá vi khuẩn, Grad-CAM tìm các vị trí đặc trưng hỗ trợ điểm số của lớp này. "
      "LIME tạo nhiều ảnh che vùng rồi học các hệ số giải thích cục bộ. Kernel SHAP cũng khảo sát các tổ hợp vùng, "
      "nhưng phân bổ đóng góp theo cách xấp xỉ giá trị Shapley. Cả ba có thể làm nổi bật vùng trên lá, song một vùng "
      "được làm sáng chưa đủ để gọi là vết bệnh đã được xác nhận.")
    p("Trong AgriXAI, mục tiêu sử dụng là tạo vùng khoanh và câu mô tả cho từng ảnh. Nhóm có toàn quyền truy cập "
      "CNN, nên Grad-CAM đáp ứng được điều kiện kỹ thuật. LIME và Kernel SHAP vẫn có lợi thế khi chỉ được gọi một "
      "mô hình qua API; khả năng đó không phải điều kiện bắt buộc của backend hiện tại.")

    # Trang 2: thiết kế và định nghĩa chỉ số.
    doc.add_page_break()
    heading("2 Thiết kế thực nghiệm")
    p(f'Checkpoint giữ nguyên: {protocol["config"]["model_version"]}. Đầu vào RGB 224 × 224 và chuẩn hóa ImageNet '
      'như pipeline hiện tại. Cùng một lớp dự đoán trên ảnh gốc được giải thích bởi cả ba phương pháp; không huấn luyện lại, '
      'không chỉnh danh mục lớp và không đưa bộ chặn vào phép đo XAI.')
    p(f'Tập chất lượng gồm {q["image_count"]} ảnh đã được chọn cho phép kiểm #17 từ tháng 9: 30 PlantVillage và 26 PlantDoc, '
      f'gồm cả dự đoán đúng và sai; {q["record_count"]} bản giải thích được tạo với seed 42, 123 và 2026. '
      'Ảnh không được chọn lại sau khi xem kết quả. Đây là tập thăm dò nhỏ, không đại diện ngẫu nhiên cho toàn bộ dữ liệu.')
    p('LIME và Kernel SHAP dùng chung SLIC yêu cầu 50 vùng, compactness 10, sigma 1; số vùng thực tế được lưu. '
      'Mỗi phương pháp có ngân sách 1.000 mẫu nhiễu, batch 32 và cùng nền RGB trung bình ảnh. LIME dùng kernel mặc định '
      'và toàn bộ feature; Kernel SHAP dùng identity link, l1_reg = 0. Số forward thực tế được đếm thay vì giả định bằng ngân sách.')
    p(f'Chất lượng chạy trên {protocol["gpu"]}. Phép đo CPU riêng dùng {c["image_count"]} ảnh, lấy ảnh đầu của mỗi lớp ở mỗi miền, '
      'ba seed, Intel Core i5-13400F và 4 luồng PyTorch/BLAS. Hai lượt chạy không chạy đồng thời. Thời gian gồm tạo giải thích và SLIC '
      'khi cần, sau làm nóng; không tính nạp mô hình, đọc/ghi ảnh và số liệu, dự đoán chung hay chấm chất lượng.')
    p('Bảng 2 định nghĩa các chỉ số. Deletion/insertion được điều chỉnh từ phép đánh giá trong RISE [6], dùng vùng SLIC '
      'và cùng nền trung bình. Mỗi ảnh được lấy trung bình qua ba seed trước khi bootstrap theo ảnh 10.000 lần. '
      'KTC 95% là khoảng tin cậy thăm dò của tập đã chọn, không phải bảo đảm cho mọi ảnh ngoài thực tế.')
    caption("Bảng 2 Các chỉ số so sánh")
    table(["Chỉ số", "Cách hiểu"], [
        ["Thời gian và số forward", "Chi phí sinh giải thích; thấp hơn phù hợp hơn với tương tác."],
        ["IoU theo seed", "Độ trùng vùng top 20% giữa ba seed; cao hơn là ít biến thiên lấy mẫu."],
        ["Mức nâng trong lá", "(Khối lượng dương trong lá − diện tích lá)/(1 − diện tích lá). 0 tương đương rải đều."],
        ["Mức nâng vào vết bệnh", "Công thức tương tự; chỉ tính triệu chứng khu trú và dự đoán đúng."],
        ["Deletion / insertion AUC", "Xóa / chèn cùng vùng SLIC theo mức quan trọng; deletion thấp, insertion cao tốt hơn."]
    ], [4.1, 12.9])
    p('Chỉ đóng góp dương được hiển thị để so với Grad-CAM sau ReLU; trọng số âm của LIME/SHAP vẫn được lưu. '
      'Đóng góp vùng được chia cho diện tích khi chuyển sang mật độ pixel. Tham chiếu vùng lá/vết bệnh là lưới 14 × 14 '
      'do AI gán mù trước đó, chưa được thẩm định độc lập; các ảnh có cờ dữ liệu đáng ngờ không được chấm định vị.')

    # Trang 3: tất cả bảng số lấy trực tiếp JSON.
    doc.add_page_break()
    heading("3 Kết quả định lượng")
    p('Bảng 3 và Hình 1 cho thấy chi phí tạo giải thích trên CPU. Thời gian là trung bình theo ảnh, kèm KTC 95%; '
      'cả ba phương pháp sử dụng cùng giới hạn batch.')
    caption("Bảng 3 Thời gian và chi phí trên CPU")
    table(["Phương pháp", "Thời gian ms [KTC 95%]", "Ảnh forward", "Backward"], [
        [NAMES[m], estimate(cs[m]["total_ms"], digits=1), number(cs[m]["forward_images"]["mean"], 0), "1" if m == "gradcam" else "0"]
        for m in METHODS], [3.1, 7.1, 3.4, 3.4])
    doc.add_picture(str(figures / "thoi-gian-cpu.png"), width=Cm(16.6))
    caption("Hình 1 Thời gian CPU với trục logarit và KTC 95%")
    p('Bảng 4 trình bày chất lượng trên toàn bộ tập thăm dò. Hai AUC phản ánh hành vi mô hình khi che ảnh; '
      'chúng không trực tiếp đo tính đúng về bệnh học.')
    caption("Bảng 4 Chất lượng giải thích và độ ổn định")
    quality_rows = []
    for label, metric, dataset in [("IoU theo seed ↑", "seed_iou", "all"),
                                   ("Mức nâng trong lá PV ↑", "leaf_lift", "pv"),
                                   ("Mức nâng trong lá PD ↑", "leaf_lift", "pd"),
                                   ("Mức nâng vết bệnh ↑", "lesion_lift", "all"),
                                   ("Deletion AUC ↓", "deletion_auc", "all"),
                                   ("Insertion AUC ↑", "insertion_auc", "all")]:
        quality_rows.append([label] + [estimate(q["by_dataset"][dataset][m][metric], digits=3) for m in METHODS])
    table(["Chỉ số", "Grad-CAM", "LIME", "Kernel SHAP"], quality_rows, [4.0, 4.3, 4.3, 4.4])
    p(f'PV = PlantVillage, PD = PlantDoc. Số ảnh chấm mức nâng trong lá: {qs["gradcam"]["leaf_lift"]["n_images"]}; mức nâng vết bệnh: '
      f'{qs["gradcam"]["lesion_lift"]["n_images"]}. Các seed không được tính là ảnh độc lập. '
      'IoU của Grad-CAM phản ánh thuật toán xác định trên cùng đầu vào, không chứng minh độ bền trước nhiễu ảnh.')

    # Trang 4: đầu ra thật của cả ba phương pháp.
    doc.add_page_break()
    heading("4 Đầu ra trực quan")
    p('Hình 2 dùng cùng lớp mục tiêu và seed 42. Bốn ảnh được ấn định theo ID trước khi xem kết quả: ảnh đầu '
      'của đốm vi khuẩn và mốc sương muộn trong mỗi miền. Màu sáng biểu diễn mật độ đóng góp dương cao; '
      'mỗi bản đồ được chuẩn hóa riêng để xem hình dạng, không so cường độ tuyệt đối giữa các phương pháp.')
    doc.add_picture(str(figures / "doi-chieu-4-anh.png"), width=Cm(16.7))
    caption("Hình 2 Ảnh đầu vào và giải thích Grad-CAM LIME Kernel SHAP")
    p('Toàn bộ 56 ảnh đều có hình đối chiếu trong thư mục gallery; các bản đồ của cả ba seed và trọng số vùng có dấu '
      'được lưu để kiểm tra lại. Vùng sáng là giải thích của mô hình, không được diễn giải thành mặt nạ bệnh chính xác.')

    # Lý do lựa chọn được trình bày riêng theo yêu cầu triển khai và bằng chứng.
    doc.add_page_break()
    heading("5 Vì sao lựa chọn Grad-CAM")
    p('Lựa chọn Grad-CAM được xác định theo yêu cầu của AgriXAI: mô hình CNN do nhóm kiểm soát, giải thích theo từng ảnh, '
      'hiển thị vùng khoanh dễ hiểu và hạn chế thời gian chờ. Lợi thế tốc độ đã được đo; sự phù hợp với kiến trúc và '
      'giao diện là lập luận triển khai. Các tiêu chí chất lượng được xem xét riêng ở mục 5.5.', bold=True)
    heading("5.1 Phù hợp với kiến trúc CNN hiện có", 2)
    p('AgriXAI sở hữu mã nguồn EfficientNet-B0 và chạy mô hình bằng PyTorch trong backend. Nhóm truy cập được tầng '
      'tích chập, trọng số và gradient, nên có đủ điều kiện dùng Grad-CAM trực tiếp. Đặc trưng đã được mạng tính khi '
      'xử lý ảnh được tận dụng để tạo giải thích. LIME và Kernel SHAP chỉ cần đầu vào/đầu ra, phù hợp khi không '
      'truy cập được bên trong mô hình; AgriXAI hiện không gặp giới hạn truy cập đó.')
    heading("5.2 Chi phí phù hợp với luồng chẩn đoán tương tác", 2)
    p(f'Trong cấu hình thực nghiệm, Grad-CAM tạo giải thích trong {number(times["gradcam"], 1)} ms trên CPU, '
      f'so với {number(times["lime"], 1)} ms của LIME và {number(times["kernel_shap"], 1)} ms của Kernel SHAP. '
      'Chênh lệch có nguyên nhân từ thuật toán: Grad-CAM tận dụng gradient sẵn có của CNN, trong khi hai phương pháp '
      'còn lại phải đánh giá nhiều tổ hợp vùng ảnh. Batch đã được áp dụng cho cả hai phương pháp lấy mẫu, nên kết quả '
      'không dựa vào việc cố ý chạy chúng từng ảnh một.')
    p('Mỗi giải thích Grad-CAM đánh giá một ảnh qua mạng và thực hiện một backward. LIME đánh giá 1.000 ảnh với '
      '32 lượt gọi mạng theo batch; Kernel SHAP đánh giá 1.002 ảnh với 34 lượt gọi. Vì vậy, 1.000 ảnh không có nghĩa '
      'là 1.000 yêu cầu HTTP riêng. Chi phí thấp có giá trị khi người dùng cần xem kết quả ngay sau khi gửi ảnh, '
      'đặc biệt với luồng nhiều ảnh. Các thời gian này chưa phải độ trễ end-to-end của ứng dụng.')
    heading("5.3 Đầu ra phù hợp với vùng khoanh và câu giải thích", 2)
    p('Heatmap Grad-CAM được đưa vào bước xử lý contour và sinh câu mô tả tiếng Việt đang có. Đường xử lý này phù hợp '
      'với mục tiêu chỉ ra vùng ảnh hỗ trợ dự đoán cho người dùng phổ thông. LIME và Kernel SHAP cũng có thể chuyển '
      'thành vùng khoanh, nhưng cấu hình đã thử cần thêm bước chia vùng ảnh làm đặc trưng và hồi quy đóng góp. '
      'Bản đồ Grad-CAM liên tục thuận tiện cho hiển thị; độ mượt của nó không chứng minh định vị vết bệnh chính xác hơn.')
    heading("5.4 Ít biến thiên theo seed lấy mẫu", 2)
    p(f'IoU vùng quan trọng giữa ba seed có trung bình {number(qs["gradcam"]["seed_iou"]["mean"], 3)} với Grad-CAM, '
      f'{number(qs["lime"]["seed_iou"]["mean"], 3)} với LIME và {number(qs["kernel_shap"]["seed_iou"]["mean"], 3)} '
      'với Kernel SHAP. Grad-CAM không lấy mẫu các tổ hợp che ảnh, nên đổi seed trong phép thử không đổi bản đồ. '
      'Điều này hỗ trợ tái tạo cùng một giải thích. LIME/SHAP có thể thay đổi khi đổi tập mẫu; tăng ngân sách có thể '
      'đổi độ ổn định và thời gian. Tính lặp lại không chứng minh tính đúng và chưa đo độ bền trước thay đổi ảnh.')

    doc.add_page_break()
    heading("5.5 Đối chiếu chất lượng và các đánh đổi", 2)
    comparisons = []
    for label, metric, higher in [("mức nâng trong lá", "leaf_lift", True),
                                  ("mức nâng vào vết bệnh", "lesion_lift", True),
                                  ("deletion AUC", "deletion_auc", False),
                                  ("insertion AUC", "insertion_auc", True)]:
        ranking = sorted(METHODS, key=lambda m: qs[m][metric]["mean"], reverse=higher)
        winner = ranking[0]
        comparisons.append(f'{label}: {NAMES[winner]} có trung bình tốt nhất ({number(qs[winner][metric]["mean"], 3)})')
    p('Kết quả trung bình ghi nhận ' + '; '.join(comparisons) + '. Đây là thứ hạng mô tả; xem KTC và số ảnh '
      'trong Bảng 4 trước khi diễn giải. Không dùng một chỉ số duy nhất để tuyên bố phương pháp tốt nhất toàn diện.')
    leaf_difference = q["paired_differences_gradcam_minus_other"]["lime"]["leaf_lift"]
    lesion_difference = q["paired_differences_gradcam_minus_other"]["lime"]["lesion_lift"]
    p('Chênh lệch ghép cặp Grad-CAM trừ LIME về mức nâng trong lá là '
      f'{estimate(leaf_difference, digits=3)}; về vết bệnh là {estimate(lesion_difference, digits=3)}. '
      'Hai KTC đều chứa 0, nên chưa đủ bằng chứng khẳng định Grad-CAM định vị tốt hơn LIME. '
      'Riêng trên PlantDoc, KTC mức nâng trong lá của cả ba phương pháp đều chứa 0.')
    p('Deletion đo diễn biến xác suất khi xóa dần các vùng được xếp quan trọng; AUC thấp hơn cho thấy xác suất '
      'giảm nhanh hơn. Insertion đo khi đưa dần các vùng đó trở lại; AUC cao hơn cho thấy xác suất tăng sớm hơn. '
      'LIME và Kernel SHAP tốt hơn Grad-CAM trên hai phép đo này trong cấu hình đã thử. Kết quả đó cần được giữ '
      'trong so sánh, dù Grad-CAM có ưu thế tốc độ. Hai phép đo phản ánh hành vi khi che ảnh và phụ thuộc nền che, '
      'khác với kiểm chứng vùng bệnh bằng chuyên gia.')
    heading("5.6 Giá trị của LIME và SHAP", 2)
    p('LIME hữu ích khi cần giải thích một bộ phân loại chỉ truy cập qua đầu vào/đầu ra. Kernel SHAP cung cấp '
      'đóng góp có dấu và tính cộng theo nền tham chiếu trong cấu hình đã định nghĩa. Hai phương pháp phù hợp để '
      'đối chiếu, kiểm tra hành vi hoặc phân tích ngoại tuyến; kết quả này không phủ nhận giá trị của chúng.')
    p('Nếu yêu cầu chính là phân tích đóng góp chi tiết ngoại tuyến hoặc giải thích một mô hình chỉ truy cập qua API, '
      'lợi thế của LIME/Kernel SHAP cần được xem xét lại. Với luồng online hiện tại, nhóm ưu tiên chi phí giải thích '
      'thấp, tận dụng CNN sẵn có và khả năng đưa đầu ra vào giao diện đang triển khai. Đây là lựa chọn theo yêu cầu '
      'sử dụng, không phải kết luận mọi phương pháp thuộc họ SHAP đều chậm hơn Grad-CAM.')
    heading("5.7 Cách trình bày lựa chọn khi bảo vệ", 2)
    p('“Nhóm chọn Grad-CAM vì hệ thống sử dụng CNN có thể truy cập gradient và cần trả giải thích nhanh cho từng ảnh. '
      f'Thực nghiệm trên cùng checkpoint cho thấy Grad-CAM mất trung bình {number(times["gradcam"], 1)} ms trên CPU, '
      'trong khi LIME và Kernel SHAP cần khoảng 13 giây với ngân sách 1.000 mẫu. Đầu ra Grad-CAM phù hợp với bước '
      'khoanh vùng và diễn giải tiếng Việt của ứng dụng. Nhóm vẫn ghi nhận những chỉ số LIME và Kernel SHAP tốt hơn, '
      'đồng thời không khẳng định Grad-CAM luôn định vị vết bệnh tốt nhất. Lựa chọn này dựa trên yêu cầu triển khai '
      'cụ thể của AgriXAI và các đánh đổi đã được đo lường.”')

    # Trang 6: giới hạn, tái lập và tài liệu tham khảo.
    doc.add_page_break()
    heading("6 Giới hạn và khả năng tái lập")
    p('Tập 56 ảnh nhỏ và đã được chọn cho một kiểm tra trước đó; chưa có thẩm định vùng bệnh độc lập. '
      'Các mặt nạ lưới chỉ cho phép so sánh thăm dò. PlantDoc khác miền huấn luyện; một giải thích có thể phản ánh '
      'đúng cách mô hình đưa ra một dự đoán sai. Kết quả phân loại trên tập này là '
      f'{q["classification"]["pv"]["correct"]}/30 ảnh PlantVillage và {q["classification"]["pd"]["correct"]}/26 ảnh PlantDoc; '
      'không dùng các tỷ lệ của tập chọn nhỏ này thay cho báo cáo test đầy đủ.')
    p('Thời gian được đo trên máy phát triển và phụ thuộc tải máy, phần cứng, thư viện và ngân sách giải thích; '
      'không phải cam kết độ trễ trên mọi thiết bị hoặc số đo đã chốt cho máy bảo vệ.')
    p('LIME/Kernel SHAP phụ thuộc SLIC, nền che và 1.000 mẫu; tăng ngân sách có thể đổi độ ổn định/chất lượng và '
      'thời gian. Phép thử không bao phủ Deep SHAP, Gradient SHAP hay Partition SHAP. Grad-CAM giải thích logit, '
      'hai phương pháp lấy mẫu giải thích xác suất; đây là so sánh các cấu hình cụ thể, không phải so sánh đại lượng '
      'đóng góp tuyệt đối. Deletion/insertion cũng phụ thuộc ảnh bị che và có thể tạo ảnh ngoài phân phối.')
    p('Bản đồ Grad-CAM cuối chỉ 7 × 7 trước nội suy. Các đốm nhỏ có thể không được phân giải; không được gọi '
      'vùng khoanh là kết quả segmentation hoặc bằng chứng mô hình có hiểu biết nhân quả về bệnh.')
    p('Mã chạy: model/src/evaluation/compare_xai.py. Kết quả nằm tại model/outputs/xai-comparison-122, gồm '
      'protocol.json, records, maps, per-image.csv, summary.json và gallery. Hash checkpoint và ảnh, seed, phiên bản '
      'thư viện và cấu hình máy được lưu trong protocol.json; checkpoint không bị thay đổi. CPU đặt OMP_NUM_THREADS, '
      'OPENBLAS_NUM_THREADS, MKL_NUM_THREADS và NUMEXPR_NUM_THREADS bằng 4; lưu xác nhận trong threadpools.json.')
    versions = protocol["versions"]
    p(f'Phiên bản: Python {protocol["python"]}; torch {versions["torch"]}; LIME {versions["lime"]}; '
      f'SHAP {versions["shap"]}; scikit-image {versions["scikit-image"]}. Lệnh tái lập từ thư mục model:')
    for text in ["python -m src.evaluation.compare_xai --device cuda --out outputs/xai-comparison-122/quality",
                 "python -m src.evaluation.compare_xai --device cpu --timing-only --one-per-class --out outputs/xai-comparison-122/cpu"]:
        para = p(text)
        for run in para.runs:
            run.font.name, run.font.size = "Consolas", Pt(8.5)
    heading("Tài liệu tham khảo")
    refs = [
        '[1] R. R. Selvaraju và cộng sự, “Grad-CAM: Visual Explanations from Deep Networks via Gradient-based Localization,” ICCV, 2017. https://arxiv.org/abs/1610.02391',
        '[2] M. T. Ribeiro, S. Singh và C. Guestrin, “Why Should I Trust You?: Explaining the Predictions of Any Classifier,” KDD, 2016. https://arxiv.org/abs/1602.04938',
        '[3] S. M. Lundberg và S.-I. Lee, “A Unified Approach to Interpreting Model Predictions,” NeurIPS, 2017. https://arxiv.org/abs/1705.07874',
        '[4] Tài liệu LIME Image. https://lime-ml.readthedocs.io/en/latest/lime.html#module-lime.lime_image',
        '[5] Tài liệu SHAP KernelExplainer. https://shap.readthedocs.io/en/latest/generated/shap.KernelExplainer.html',
        '[6] V. Petsiuk, A. Das và K. Saenko, “RISE: Randomized Input Sampling for Explanation of Black-box Models,” BMVC, 2018. https://arxiv.org/abs/1806.07421',
    ]
    for ref in refs:
        para = p(ref)
        for run in para.runs:
            run.font.size = Pt(10)
    target.parent.mkdir(parents=True, exist_ok=True)
    doc.save(target)
    print(target)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, default=ROOT / "outputs/xai-comparison-122")
    parser.add_argument("--out", type=Path, default=ROOT.parent / "docx/bao-cao-so-sanh-gradcam-lime-shap.docx")
    parser.add_argument("--figures-only", action="store_true")
    parser.add_argument("--document-only", action="store_true")
    parser.add_argument("--quality-figures-only", action="store_true")
    parser.add_argument("--runtime-figure-only", action="store_true")
    parser.add_argument("--comparison-figure-only", action="store_true")
    args = parser.parse_args()
    mode = "quality" if args.quality_figures_only else ("runtime" if args.runtime_figure_only else
            ("comparison" if args.comparison_figure_only else "all"))
    figures = args.base / "figures" if args.document_only else make_figures(args.base, mode)
    if not (args.figures_only or args.quality_figures_only or args.runtime_figure_only or args.comparison_figure_only):
        make_docx(args.base, args.out, figures)


if __name__ == "__main__":
    main()
