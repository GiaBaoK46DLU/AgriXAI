"""Tổng hợp báo cáo #93/#90/#50 từ số liệu máy, không nhập tay kết quả."""

import argparse
import json
from pathlib import Path


def percent(value):
    return f"{value * 100:.2f}%"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True)
    parser.add_argument("--out", default="../docx/bao-cao-cat-la-domain-adaptation.md")
    args = parser.parse_args()
    root = Path(args.run)

    def read(name):
        return json.loads((root / name).read_text(encoding="utf-8"))

    selection = read("selection.json")
    manifest = read("evaluation/manifest.json")
    classification = read("evaluation/classification.json")
    cpu_classification = read("evaluation/classification-cpu.json")
    cpu_paired = read("evaluation/paired-comparison-cpu.json")
    paired = read("evaluation/paired-comparison.json")
    guards = read("evaluation/guard-summary.json")
    system = read("evaluation/system-summary.json")
    latency = read("evaluation/cpu-latency.json")
    smoke = read("api-smoke.json")
    baseline = classification["baseline-full"]
    chosen = classification[manifest["selected_run"]]
    thresholds = selection["config"]["xai"]["reliability"]
    crop_validation = read("crop-selection-validation.json")
    full_validation = read("candidate-validation-cpu.json")[selection["selected"]]
    text = [
        "# Cắt vùng lá, chốt hiển thị XAI và cải thiện domain gap",
        "",
        "Thực hiện [#93](https://github.com/GiaBaoK46DLU/AgriXAI/issues/93), "
        "[#90](https://github.com/GiaBaoK46DLU/AgriXAI/issues/90), "
        "[#50](https://github.com/GiaBaoK46DLU/AgriXAI/issues/50). "
        "Các số liệu dưới đây được sinh từ file dự đoán từng ảnh, không chỉnh tay.",
        "",
        f"Checkpoint được chọn bằng validation: **{selection['selected']}**. "
        f"Cắt lá trong cấu hình được chọn: **{'bật' if selection['crop_enabled'] else 'tắt'}**. "
        "Mặc định XAI vẫn là Grad-CAM++; bộ chặn lá chạy trước bước cắt, trên ảnh đầy đủ. "
        "Sau các lượt học, checkpoint và bước cắt được chốt bằng validation CPU (batch 1 như backend), trước khi mở test.",
        "Chính sách chọn: giữ accuracy PV validation ít nhất 98,5%; trong các bản đạt điều kiện này, "
        "chọn macro-F1 PlantDoc validation cao nhất. Nhờ vậy mức đánh đổi trên dữ liệu nguồn được kiểm soát.",
        "",
        "## 1. Thiết kế và dữ liệu",
        "",
        "- Checkpoint cha EfficientNet-B0 giữ nguyên; không đổi thứ tự 10 lớp trong danh mục dùng chung.",
        "- PlantDoc chỉ dùng thư mục train để học: bỏ `tomato_V8.jpg`, còn 674 ảnh; "
        "chia phân tầng seed 42 thành 539 ảnh học và 135 ảnh validation. Không dùng test để chọn epoch/cấu hình.",
        "- Phép đo đích giữ đúng **66 ảnh test PlantDoc** đã lọc ba bản trùng byte từ bộ gốc. "
        "Đây là ảnh công khai từ Internet, không phải ảnh tự chụp ở Đà Lạt.",
        "- Audit SHA-256 phát hiện thêm 5 bản sao trong train/val PlantVillage trùng test; "
        "đã bỏ khỏi dữ liệu học mới. Ba ảnh test từng có bản sao trong train của checkpoint cha "
        "được báo riêng qua cột PV sạch (2716 ảnh). Tập lịch sử 2719 ảnh vẫn giữ để so lại số cũ.",
        "- Augmentation: ghép nền chỉ cho PlantVillage, nền chỉ từ split train của bộ ảnh âm; "
        "mô phỏng gamma, vùng nắng/bóng đổ, kèm jitter/blur hiện có. PlantDoc giữ nền thật, chỉ thay ánh sáng.",
        "- Hai lần học đều bắt đầu từ checkpoint cha: augmentation trên PV; adaptation dùng "
        "539 ảnh PlantDoc lặp 5 lần và 250 ảnh/lớp PV để giữ đủ 10 lớp. Batch 8, tích luỹ gradient 4 bước; "
        "AMP, AdamW, seed 42. Lượt batch 32 đầu bị dừng vì áp lực VRAM, chưa có checkpoint hoàn tất epoch.",
        "- Sau fine-tune, thử hiệu chỉnh thống kê BatchNorm bằng ảnh train chưa augment: "
        "một biến thể dùng PV, một biến thể trộn PV/PlantDoc. Giữ nguyên mọi tham số đã học, "
        "chỉ cập nhật running mean/variance; dropout/stochastic depth tắt. Chỉ chọn biến thể "
        "bằng validation, trước khi mở test. Inventory hiệu chỉnh được kiểm tra không trùng validation/test.",
        "",
        "## 2. Kết quả phân loại",
        "",
        "**Bảng 1. Các hướng đã thử, cùng phép đo và không dùng test để chọn mô hình.**",
        "",
        "| Phương án | PV 10 lớp | PV sạch | PV 8 lớp | PlantDoc 8 lớp | Macro-F1 PlantDoc |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    names = {
        "baseline-full": "Checkpoint cha, toàn ảnh",
        "baseline-crop": "Checkpoint cha, cắt lá",
        "augmentation": "Học thêm augmentation, toàn ảnh",
        "adaptation": "Fine-tune PlantDoc + PV, toàn ảnh",
        "adaptation-bn-pv": "Fine-tune + hiệu chỉnh BN bằng PV train",
        "adaptation-bn-mixed": "Fine-tune + hiệu chỉnh BN bằng PV/PlantDoc train",
        "rehearsal": "Fine-tune + nhắc lại PV và chưng cất từ checkpoint cha",
        "selected-crop": "Checkpoint được chọn, có cắt lá",
    }
    for variant, metrics in classification.items():
        text.append(
            f"| {names.get(variant, variant)} | {percent(metrics['pv10']['accuracy'])} | "
            f"{percent(metrics['pv10-clean']['accuracy'])} | {percent(metrics['pv8']['accuracy'])} | "
            f"{percent(metrics['pd8']['accuracy'])} | {metrics['pd8']['macro_f1_present']:.4f} |"
        )
    lo, hi = paired["pd8"]["paired_bootstrap_ci95"]
    text += [
        "",
        "Các hàng ở Bảng 1 được đo trên GPU. Backend cấu hình CPU nên được đo thêm riêng:",
        "",
        f"- PlantDoc test CPU: {percent(cpu_classification['baseline']['pd8']['accuracy'])} → "
        f"**{percent(cpu_classification['selected']['pd8']['accuracy'])}**; macro-F1 8 lớp "
        f"{cpu_classification['selected']['pd8']['macro_f1_present']:.4f}.",
        f"- PlantVillage test CPU: {percent(cpu_classification['baseline']['pv10']['accuracy'])} → "
        f"{percent(cpu_classification['selected']['pv10']['accuracy'])}.",
        f"- Mức thay đổi accuracy trên PlantDoc CPU: {cpu_paired['pd8']['accuracy_delta'] * 100:+.2f} điểm; "
        f"KTC ghép cặp 95% [{cpu_paired['pd8']['paired_bootstrap_ci95'][0] * 100:+.2f}; "
        f"{cpu_paired['pd8']['paired_bootstrap_ci95'][1] * 100:+.2f}] điểm.",
        "",
        "Không trộn số CPU với số GPU khi tính mức cải thiện. Các dự đoán khác nhau giữa "
        "hai thiết bị được ghi trong `cpu-gpu-disagreement.json`.",
    ]
    if (root / "rehearsal.pt").exists():
        text += [
            "",
            "Có chạy thêm 3 epoch nhắc lại dữ liệu nguồn: 200 ảnh/lớp PV train và toàn bộ "
            "539 ảnh PlantDoc train. Teacher là checkpoint cha; KL chưng cất (T=2, trọng số 0,5) "
            "chỉ áp trên PV, PlantDoc vẫn học nhãn thật. Tắt augmentation thay nền ở lượt này "
            "để giữ phong cách ảnh nguồn; vẫn giữ transform cơ bản. Inventory kiểm tra độc lập "
            "không trùng validation/test. Lịch sử, cả các epoch không được chọn, lưu trong `rehearsal-history.json`.",
        ]
    text += [
        "",
        f"Trên 66 ảnh đích, thay đổi accuracy so với checkpoint cha: "
        f"**{paired['pd8']['accuracy_delta'] * 100:+.2f} điểm phần trăm**; "
        f"KTC bootstrap ghép cặp 95% [{lo * 100:+.2f}; {hi * 100:+.2f}] điểm; "
        f"McNemar exact p = {paired['pd8']['mcnemar_exact_p']:.6f}. "
        f"Có {paired['pd8']['wrong_to_correct']} ảnh từ sai thành đúng và "
        f"{paired['pd8']['correct_to_wrong']} ảnh từ đúng thành sai.",
        "",
        "66 ảnh là ít: kết luận chỉ trong bộ test này; không suy thành accuracy ngoài vườn. "
        "Đọc macro-F1 trên 8 lớp có mặt; mô hình vẫn trả đủ 10 lớp, hai lớp không có trong PlantDoc "
        "được kiểm lại trên PlantVillage. Không dùng con số gộp cả PlantDoc train+test của #49 "
        "để đánh giá checkpoint đã fine-tune.",
        "",
        "**Bảng 2. Độ nhạy từng lớp trên PlantDoc test (đủ cả các lớp khó).**",
        "",
        "| Lớp | Số ảnh | Recall trước | Recall sau | F1 sau |",
        "|---|---:|---:|---:|---:|",
    ]
    for key in chosen["pd8"]["classes_present"]:
        a, b = baseline["pd8"]["per_class"][key], chosen["pd8"]["per_class"][key]
        text.append(
            f"| `{key}` | {int(b['support'])} | {percent(a['recall'])} | {percent(b['recall'])} | {b['f1-score']:.4f} |"
        )
    text += [
        "",
        "**Bảng 3. Kết quả toàn hệ thống khi có bộ chặn lá.**",
        "",
        "| Checkpoint | Tổng ảnh | Gate từ chối | Accuracy trên toàn bộ | Accuracy trong phần được nhận |",
        "|---|---:|---:|---:|---:|",
    ]
    for tag, values in system.items():
        text.append(
            f"| {tag} | {values['n']} | {values['rejected']} | {percent(values['overall_accuracy'])} | {percent(values['accepted_accuracy'])} |"
        )
    text += [
        "",
        "## 3. Cắt lá và độ tin cậy của vùng khoanh",
        "",
        "Tách vùng bằng HSV/Otsu và thành phần nổi bật, lấp lỗ trong lá, thêm lề 8%. "
        "Không tách được vùng đủ rõ thì giữ ảnh đầy đủ. CAM của ảnh cắt được resize về khung cắt "
        "rồi đặt vào ảnh gốc; vùng ngoài khung bằng 0. Có kiểm thử ảnh không vuông/lá lệch tâm "
        "và đã xem bằng mắt 12 ảnh thật trong `coordinate-audit/`.",
        "",
        "Cách tách màu còn giữ cả nhánh cây ở vài ảnh và bỏ sót mép lá khô ít bão hoà. "
        "Đây là heuristic cho tiền xử lý, chưa phải mô hình phân vùng lá hoặc phân vùng bệnh. "
        "Kết quả bật/tắt cuối cùng lấy từ validation; Bảng 1 ghi cả hai chế độ để đối chiếu.",
        f"Với checkpoint được chọn, accuracy PlantDoc validation CPU khi không cắt là "
        f"{percent(full_validation['pd']['accuracy'])}, khi bật cắt là "
        f"{percent(crop_validation['alternative']['pd']['accuracy'])}. "
        "Quyết định bật/tắt giữ nguyên khi mở test.",
        "",
        "![Hình 1. Kiểm tra ánh xạ CAM sau khi cắt trên ảnh validation PV](../model/outputs/domain-50-20261104/coordinate-audit/pv-01.png)",
        "",
        "*Hình 1. Checkpoint cha, chế độ bật cắt để kiểm tra toạ độ: CAM chỉ nằm trong khung được đưa vào mô hình.*",
        "",
        "![Hình 2. Hạn chế tách màu khi mép lá khô ít bão hoà](../model/outputs/domain-50-20261104/coordinate-audit/pd-02.png)",
        "",
        "*Hình 2. Ảnh validation PlantDoc cho thấy mép lá khô có thể bị bỏ sót. Hai hình kiểm toạ độ/giới hạn tiền xử lý, không phải số đo accuracy của checkpoint mới.*",
        "",
        f"Chốt XAI yêu cầu ít nhất **{percent(thresholds['min_leaf_mass'])} khối lượng heatmap nằm trong lá** "
        f"và lift chuẩn hoá ≥ **{thresholds['min_lift']:.2f}**; mask không rõ/CAM trống thì trả `heatmap=None`. "
        "Lift = (khối lượng trong lá − tỉ lệ diện tích lá)/(1 − tỉ lệ diện tích lá). "
        "Không dùng độ phẳng CAM để phân biệt domain. Các ngưỡng có trong YAML, giữ cố định trước khi mở test.",
        "",
        "**Bảng 4. Kết quả trả `None` thực từ predictor; phân loại giữ nguyên khi bật/tắt chốt.**",
        "",
        "| Bộ probe | Số ảnh | Không hiển thị heatmap | Tỉ lệ ẩn |",
        "|---|---:|---:|---:|",
    ]
    for tag, values in guards.items():
        text.append(
            f"| {tag} | {values['n']} | {values['hidden']} | {percent(values['hidden'] / values['n'])} |"
        )
    reasons = {
        reason: count
        for reason, count in guards["pv-test"]["reasons"].items()
        if reason != "accepted"
    }
    text += [
        "",
        "Lý do ẩn trên 300 ảnh PV test: "
        + (
            "; ".join(f"`{reason}`: {count} ảnh" for reason, count in reasons.items())
            if reasons
            else "không có ảnh bị ẩn"
        )
        + ". `unknown_leaf_mask` là không tách được lá đủ rõ; `outside_leaf` là khối lượng/lift "
        "không đạt ngưỡng. Đây có thể là lá thật bị bỏ phần giải thích vì heuristic bảo thủ; "
        "không được coi các ảnh đó là ảnh không phải lá hoặc âm thầm bỏ khỏi phép đo.",
    ]
    text += [
        "",
        "Ảnh lá bị ẩn vẫn được tính đầy đủ trong độ chính xác. Ảnh âm ở bảng này được probe "
        "không có gate để đo riêng chốt XAI; hệ thống thật còn bộ chặn chạy phía trước. "
        "Qua chốt chỉ cho biết CAM tập trung vào vùng lá **ước lượng**, không chứng minh mô hình "
        "đoán đúng bệnh, vết khoanh là tổn thương thật, hay mức độ bệnh chính xác. Mặt nạ tham chiếu "
        "56 ảnh hiện do AI khoanh mù, chưa được chuyên gia xác nhận.",
        "",
        f"Trong probe XAI trên GPU, accuracy nhóm PlantDoc qua chốt là "
        f"{percent(guards['pd-test']['accepted_accuracy'])}, so với "
        f"{percent(guards['pd-test']['all_accuracy'])} trên toàn bộ 66 ảnh. "
        "Chưa có bằng chứng chốt này dự báo được việc phân loại đúng/sai; mục đích là hạn chế vẽ vùng khi vị trí không đủ rõ.",
        "",
        f"![Hình 3. Chốt XAI ẩn vùng khoanh khi CAM không tập trung đủ trong vùng lá ước lượng](../model/{root.as_posix()}/evaluation/pd-test-1.png)",
        "",
        "*Hình 3. Checkpoint mới trên ảnh PlantDoc ghép nhiều nội dung: CAM phản ứng cả ở vùng quả; "
        "vùng khoanh được ẩn. Khung đỏ bên trái là khung lá ước lượng, không phải ảnh đầu vào đã cắt.*",
        "",
        "## 4. Hiệu năng và tích hợp",
        "",
        "**Bảng 5. Predict trên CPU, 32 ảnh sau một lượt làm nóng, cùng checkpoint được chọn.**",
        "",
        "| Chế độ | Median (ms) | P95 (ms) |",
        "|---|---:|---:|",
    ]
    for tag, values in latency.items():
        text.append(f"| `{tag}` | {values['median_ms']:.2f} | {values['p95_ms']:.2f} |")
    text += [
        "",
        "Đây là thời gian `predict`, không gồm tải mô hình, mạng, lưu ảnh hoặc toàn bộ request. "
        "Máy có tác vụ khác nên không coi một lần đo là benchmark hiệu năng tổng quát.",
        "",
        "Đã POST multipart qua FastAPI/TestClient bằng checkpoint thật, SQLite/thư mục ảnh tạm:",
        "",
    ]
    for tag, case in smoke.items():
        text.append(
            f"- `{tag}`: HTTP {case['status']}; ảnh có vùng rõ có overlay, vùng không rõ "
            "không có overlay và nhắc chụp lại; ảnh bị gate chặn trả 422."
            if tag == "hidden"
            else f"- `{tag}`: HTTP {case['status']}."
        )
    if (root / "api-http.json").exists():
        native = read("api-http.json")
        text += [
            "",
            "Đã kiểm thêm HTTP thật qua Uvicorn riêng trên CPU: đăng ký cấp token thật, "
            "loader nạp checkpoint và YAML mặc định thật; ảnh có vùng rõ được ghi/đọc lại qua API "
            "và tải được overlay; vùng không rõ trả null kèm lời nhắc chụp lại; ảnh âm trả 422. "
            "SQLite và storage đều tạm, không dùng DB dev.",
            f"Phiên bản `/health` xác nhận: `{native['health']['model_version']}`.",
        ]
    text += [
        "",
        "Mỗi ca lặp cùng một ảnh ba lần để kiểm hợp đồng endpoint nhận 3–5 ảnh, "
        "không tính thành ba mẫu đánh giá độc lập. Không sửa `Prediction` hoặc danh mục lớp. "
        "Offline trên Flutter vẫn là CAM cổ điển với checkpoint cũ; không gán số đo nâng cấp server cho offline.",
        "",
        "## 5. Tái lập và bằng chứng",
        "",
        "Từ thư mục `model/`:",
        "",
        "```powershell",
        f"python -m src.evaluation.verify_domain --run {root.as_posix()}",
        f"python -m src.evaluation.domain_report --run {root.as_posix()}",
        "```",
        "",
        f"Nguồn: `model/{root.as_posix()}/`. `protocol.json`, inventory SHA-256, lịch sử từng epoch, "
        "`selection.json`, kết quả cắt trên validation, dự đoán từng ảnh test, bootstrap ghép cặp, "
        "kết quả từng probe XAI, phép đo hệ thống và response API được giữ nguyên để đối chiếu. "
        "Không chạy lại training/evaluation vào thư mục cũ; dùng `--out` mới.",
        "",
    ]
    Path(args.out).write_text("\n".join(text), encoding="utf-8")
    print(args.out)


if __name__ == "__main__":
    main()
