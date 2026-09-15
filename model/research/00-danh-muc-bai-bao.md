# Danh mục bài báo — nhận diện bệnh cây trồng + XAI

Lập ngày **28/08/2026**. Lọc theo đúng ba thứ đề tài cần: **mô hình huấn luyện gì**,
**kết quả bao nhiêu**, **giải thích ra sao**.

> Đọc phần "⚠️ Về số liệu" trong `README.md` trước khi trích bất cứ con số nào.
> ✅ = đã mở toàn văn · ⚪ = mới thấy qua tìm kiếm, chưa mở.

---

## Đọc theo thứ tự nào

Không đọc từ trên xuống. Sáu bài dưới đây đọc trước, vì mỗi bài chống được một
câu hỏi phản biện cụ thể:

| Thứ tự | Mã | Chống được câu hỏi |
|---|---|---|
| 1 | **A1** | "Bài toán này người ta làm tới đâu rồi?" — bài gốc, mốc so sánh 99,35% |
| 2 | **A2** | "99% của em là thật hay do mô hình học cái nền ảnh?" — bài chứng minh PlantVillage có thiên lệch |
| 3 | **A3** | "Ra đồng thật thì tụt bao nhiêu?" — review đo đúng con số đó trên hai nhóm dữ liệu |
| 4 | **D4** | Bài gần đề tài mình nhất: EfficientNet-B0 + Grad-CAM trên cà chua. Đọc để biết mình khác họ chỗ nào |
| 5 | **B1** | Bảng benchmark để biết đặt EfficientNet-B0 của mình vào đâu |
| 6 | **F1** | "Người dùng chụp cái không phải lá cà chua thì sao?" — nhánh `khác` của bộ định tuyến |

Bốn bài đầu đủ để viết xong chương tổng quan. Nhóm C, E, G để sau.

---

## A. Nền tảng và tổng quan — đọc trước tiên

| Mã | Bài | Nguồn · Năm | Số liệu đáng nhớ | Vì sao đọc | TT |
|---|---|---|---|---|---|
| **A1** | [Using Deep Learning for Image-Based Plant Disease Detection](https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2016.01419/full) — Mohanty, Hughes, Salathé | Front. Plant Sci. 7:1419 · 2016 | 54.306 ảnh, 14 loài, 26 bệnh, AlexNet + GoogLeNet, F1 **0,9934** (GoogLeNet transfer, chia 80-20). Thử 5 tỉ lệ chia từ 80-20 tới 20-80. **Trên ảnh chụp điều kiện khác chỉ còn 31,40% và 31,69%** (38 lớp, đoán mò 2,63%) | Bài khai sinh cả bộ PlantVillage lẫn thói quen báo cáo 99%. Con số 31,40% là **bằng chứng domain gap mạnh nhất có thể trích**, vì đến từ chính tác giả benchmark | ✅ |
| **A2** | [Uncovering bias in the PlantVillage dataset](https://arxiv.org/abs/2206.04374) — Noyan | arXiv 2206.04374 · 2022 | Chỉ dùng **8 pixel nền** đã đoán đúng **49,0%** (đoán mò 2,6%). Xoá nền **không** hết thiên lệch | Bài quan trọng nhất danh mục. Chứng minh mô hình học nhãn từ cái nền chứ không từ vết bệnh. Đây chính là lý do Grad-CAM của mình phải khoanh trúng vết bệnh — heatmap sáng ở nền là dính đúng lỗi này | ✅ |
| **A3** | [Deep learning networks-based tomato disease and pest detection: a first review of research studies using real field datasets](https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2024.1493322/full) — Jelali | Front. Plant Sci. · 2024 | PlantVillage trung bình **90,18%** · dữ liệu đồng ruộng tự thu **84,66%**. Trên ảnh đồng: InceptionV3 93,70%, DenseNet 94,93% | Review **duy nhất chỉ đọc bài dùng ảnh đồng ruộng thật**. Cho con số domain gap có nguồn trích dẫn được, thay vì mình nói suông. Dùng để biện minh cho `data/field/` | ✅ |
| **A4** | [Deep learning-based classification, detection, and segmentation of tomato leaf diseases: a state-of-the-art review](https://www.sciencedirect.com/science/article/pii/S258972172500025X) | ScienceDirect · 2025 | Khảo 14 bệnh lá cà chua; PlantVillage là bộ dùng nhiều nhất | Review mới nhất riêng cho cà chua. Lấy bảng tổng hợp kiến trúc để dựng khung chương 2 | ⚪ |
| **A5** | [A systematic review of deep learning techniques for plant diseases](https://link.springer.com/article/10.1007/s10462-024-10944-7) | Artif. Intell. Rev. · 2024 | — | Review rộng hơn, mọi loài cây. Đọc lướt lấy cách phân loại phương pháp | ⚪ |
| **A6** | [Plant disease recognition datasets in the age of deep learning: challenges and opportunities](https://pmc.ncbi.nlm.nih.gov/articles/PMC11466843/) | PMC · 2024 | — | Bàn riêng về **bộ dữ liệu** chứ không về mô hình. Dùng cho mục "hạn chế của dữ liệu" | ⚪ |
| **A7** | [A review of plant leaf disease identification by deep learning algorithms](https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2025.1637241/full) | Front. Plant Sci. · 2025 | — | Review 2025, cập nhật phần "hướng nghiên cứu hiện nay" | ⚪ |

---

## B. So sánh kiến trúc — xương sống phần thực nghiệm

Nhóm phục vụ trực tiếp yêu cầu "huấn luyện rồi so sánh đánh giá".

| Mã | Bài | Nguồn · Năm | Mô hình & kết quả | Vì sao đọc | TT |
|---|---|---|---|---|---|
| **B1** | [Assessing the performance of domain-specific models for plant leaf disease classification: a comprehensive benchmark of transfer-learning on open datasets](https://www.nature.com/articles/s41598-025-03235-w) | Sci. Rep. · 2025 | Đo trên **PlantVillage + Taiwan + Citrus** | Benchmark chuẩn mực nhất nhóm này: cùng một quy trình đo nhiều kiến trúc trên nhiều bộ dữ liệu. Bắt chước cách trình bày bảng của họ | ⚪ |
| **B2** | [Deep learning based ensemble model for accurate tomato leaf disease classification by leveraging ResNet50 and MobileNetV2](https://www.nature.com/articles/s41598-025-98015-x) | Sci. Rep. · 2025 | Ensemble ResNet50 + MobileNetV2, 11.000 ảnh, 10 lớp | **10 lớp trùng khít đề tài mình.** Xem ensemble có đáng làm không, hay chỉ tốn gấp đôi thời gian suy luận | ⚪ |
| **B3** | [Bayesian optimized multimodal deep hybrid learning approach for tomato leaf disease classification](https://www.nature.com/articles/s41598-024-72237-x) | Sci. Rep. · 2024 | 7 mô hình lai DL+ML, 10 lớp (9 bệnh + 1 khoẻ), **98,268%** | Cũng đúng 10 lớp. Hướng "CNN trích đặc trưng + SVM/LR phân loại" — rẻ, chạy được trên máy mình, làm baseline so sánh rất hợp | ⚪ |
| **B4** | [Early detection of tomato leaf diseases using transformers and transfer learning](https://www.sciencedirect.com/science/article/pii/S1161030125001212) | Eur. J. Agronomy · 2025 | ViT-Base **99,17%** trên PlantVillage | Bài để trả lời "sao không dùng Transformer?". Xem họ trả giá bao nhiêu về tham số và thời gian | ⚪ |
| **B5** | [Tomato Leaf Disease Classification with Vision Transformer Variants](https://link.springer.com/chapter/10.1007/978-3-031-47634-1_8) | Springer chapter · 2023 | So **ViT vs Swin vs CCT** | So sánh sạch giữa ba biến thể Transformer trên đúng bài toán mình | ⚪ |
| **B6** | [Advanced neural network architectures for tomato leaf disease diagnosis in precision agriculture](https://link.springer.com/article/10.1007/s43621-025-01149-1) | Discov. Sustain. · 2025 | DenseNet121 **99,61%**, ResNet50 99,48%, VGG16 99,08% | Bảng số liệu dày, tiện làm cột "công bố khác" trong bảng đối chiếu của mình | ⚪ |
| **B7** | [A robust deep learning approach for tomato plant leaf disease localization and classification](https://www.nature.com/articles/s41598-022-21498-5) | Sci. Rep. · 2022 | DenseNet-77 + CornerNet, **~99,98%** | Con số cao bất thường — đọc kỹ **cách chia tập** của họ. Nghi vấn rò rỉ dữ liệu là chỗ đáng phân tích trong báo cáo | ⚪ |
| **B8** | [AgriPath: A Systematic Exploration of Architectural Trade-offs for Crop Disease Classification](https://arxiv.org/pdf/2603.13354) | arXiv · 2026 | — | Chuyên về đánh đổi kiến trúc, hợp phần "vì sao chọn EfficientNet-B0" | ⚪ |
| **B9** | [A biologically structured hierarchical vision transformer-CNN framework for robust tomato leaf disease classification](https://www.frontiersin.org/journals/artificial-intelligence/articles/10.3389/frai.2026.1880070/full) | Front. AI · 2026 | ViT định tuyến + CNN chuyên biệt | **Rất giống ý tưởng bộ định tuyến lá/quả của mình** — tầng trên phân nhánh, tầng dưới phân loại chi tiết. Đọc trước khi làm mốc 6 | ⚪ |
| **B10** | [Tomato leaf disease classification using a vision transformer with cascaded group attention (ViT-CGA)](https://link.springer.com/article/10.1007/s41348-026-01274-7) | J. Plant Dis. Prot. · 2026 | ViT-CGA vượt CNN baseline, YOLOv7, SFMS | Bài mới nhất nhóm này, hợp phần "hướng phát triển" | ⚪ |

---

## C. Mô hình nhẹ / chạy trên thiết bị yếu

Liên quan tới **rủi ro số 2** trong `CLAUDE.md` (tốc độ suy luận lúc demo).

| Mã | Bài | Nguồn · Năm | Đáng chú ý | TT |
|---|---|---|---|---|
| **C1** | [A comprehensive evaluation of lightweight deep learning models for tomato disease classification on edge computing environments](https://www.nature.com/articles/s41598-026-42439-6) | Sci. Rep. · 2026 | So MobileNetV3 / EfficientNet-B0 / ShuffleNetV2 trên thiết bị biên, **đúng bài toán cà chua**. Bài số 1 của nhóm này | ⚪ |
| **C2** | [Mobile-Friendly Deep Learning for Plant Disease Detection: A Lightweight CNN Benchmark Across 101 Classes of 33 Crops](https://arxiv.org/pdf/2508.10817) | arXiv · 2025 | Benchmark quy mô lớn, có số đo tham số và độ trễ để trích | ⚪ |
| **C3** | [RTR_Lite_MobileNetV2: A lightweight and efficient model for plant disease detection and classification](https://www.sciencedirect.com/science/article/pii/S2214662825000271) | ScienceDirect · 2025 | MobileNetV2 + attention, vượt ResNet101 và EfficientNetV2 | ⚪ |
| **C4** | [PMVT: a lightweight vision transformer for plant disease identification on mobile devices](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10562605/) | PMC · 2023 | Transformer đủ nhẹ để chạy trên điện thoại | ⚪ |
| **C5** | [Evaluation of lightweight and efficient deep learning models for plant disease classification](https://link.springer.com/article/10.1007/s43926-026-00310-0) | Discov. IoT · 2026 | Có knowledge distillation, quantization, pruning trên Raspberry Pi / Jetson Nano | ⚪ |
| **C6** | [Plant disease detection model for edge computing devices](https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2023.1308528/full) | Front. Plant Sci. · 2023 | — | ⚪ |
| **C7** | [Siamese Network-based Lightweight Framework for Tomato Leaf Disease Recognition](https://arxiv.org/pdf/2209.11214) | arXiv · 2022 | Hướng few-shot — hữu ích nếu ảnh tự chụp quá ít | ⚪ |

> Đề tài mình **suy luận ở backend chứ không trên điện thoại**, nên nhóm này là để
> phòng khi bị hỏi "sao không chạy thẳng trên máy", không phải việc phải làm.

---

## D. XAI — trọng tâm của đề tài

| Mã | Bài | Nguồn · Năm | Đáng chú ý | TT |
|---|---|---|---|---|
| **D1** | [Grad-CAM: Visual Explanations from Deep Networks via Gradient-based Localization](https://arxiv.org/abs/1610.02391) — Selvaraju et al. | ICCV 2017 / IJCV 2020 | **Bài gốc của kỹ thuật mình đang dùng.** Bắt buộc trích dẫn. Tác giả **tự nhận** phương pháp cho "coarse localization map"; cách khắc phục của chính họ là **Guided Grad-CAM**. Trích thẳng khi bị hỏi vì sao heatmap thô | ⚠️ mới tóm tắt |
| **D2** | [Grad-CAM++: Improved Visual Explanations for Deep Convolutional Networks](https://arxiv.org/abs/1710.11063) — Chattopadhay et al. | WACV 2018 | Dùng tổ hợp có trọng số của các **đạo hàm riêng dương**. Tốt hơn khi ảnh có **nhiều thể hiện rời rạc của cùng một lớp** và khi đối tượng chỉ xuất hiện một phần — đúng ca đốm Septoria và đốm lá vi khuẩn. Ứng viên số 1 để nâng cấp `src/xai/gradcam.py` trong #16. ⚠️ PDF arXiv không giải mã tự động được, **phải mở tay** để lấy công thức và bảng số | ⚠️ mới tóm tắt |
| **D3** | [Score-CAM: Score-Weighted Visual Explanations for Convolutional Neural Networks](https://arxiv.org/abs/1910.01279) — Wang et al. | CVPRW 2020 | Không cần gradient nên ổn định hơn, nhưng chậm hơn nhiều lần. Nêu ở phần "phương án đã cân nhắc" | ⚪ |
| **D4** | [XSE-TomatoNet: An explainable AI based tomato leaf disease classification method using EfficientNetB0 with squeeze-and-excitation blocks and multi-scale feature fusion](https://www.sciencedirect.com/science/article/pii/S221501612500007X) — Assaduzzaman et al. · [bản PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC12255360/) | MethodsX · 01/2025 | **Bài gần đề tài mình nhất.** EfficientNetB0 + SE, 11 lớp cà chua, 32.532 ảnh, **99,11%**, dùng cả LIME + SHAP + Grad-CAM + Grad-CAM++, triển khai bằng Flask. Khác biệt của mình: họ dừng ở heatmap kỹ thuật, mình chuyển thành vùng khoanh + câu tiếng Việt. **Đây là chỗ chứng minh đề tài không trùng lặp** | ✅ |
| **D5** | [Leaf-Based Plant Disease Detection and Explainable AI](https://arxiv.org/html/2404.16833v1) | arXiv · 2024 | Khảo sát các phương pháp XAI cho riêng bài toán bệnh lá | ⚪ |
| **D6** | [A lightweight neural network framework for sustainable tomato leaf disease detection using explainable artificial intelligence](https://link.springer.com/article/10.1007/s43621-026-03163-3) | Discov. Sustain. · 2026 | Nhẹ + XAI, đúng hai ràng buộc của mình cùng lúc | ⚪ |
| **D7** | [Deep learning and explainable AI for classification of potato leaf diseases](https://pmc.ncbi.nlm.nih.gov/articles/PMC11830750/) | PMC · 2025 | Khác loài cây nhưng quy trình XAI trình bày rõ, dễ bắt chước cách viết | ⚪ |
| **D8** | [Explainable AI in agriculture: review of applications, methodologies, and future directions](https://iopscience.iop.org/article/10.1088/2631-8695/ae086a) | IOP Eng. Res. Express · 2025 | Review XAI nông nghiệp — trích ở phần đặt vấn đề | ⚪ |
| **D9** | [Explainability Needs in Agriculture: Exploring Dairy Farmers User Personas](https://arxiv.org/html/2509.16249) | arXiv · 2025 | Khảo sát **40 nông dân thật**: họ cần *diễn giải kết quả*, không cần biết mô hình chạy thế nào. **Bằng chứng học thuật cho quyết định thiết kế cốt lõi của đề tài** — đưa vùng khoanh + câu chữ thay vì bản đồ nhiệt | ⚪ |
| **D10** | [The role of explainability in AI for agriculture](https://www.ifpri.org/blog/the-role-of-explainability-in-ai-for-agriculture-making-digital-systems-easier-to-understand-for-farmers/) — IFPRI | blog · — | Không phải bài báo, nhưng viết gọn về việc nông dân bỏ qua khuyến nghị AI khi không hiểu lý do. Dùng làm câu dẫn nhập | ⚪ |
| **D11** | [jacobgil/pytorch-grad-cam](https://github.com/jacobgil/pytorch-grad-cam) | thư viện | Cài sẵn Grad-CAM, Grad-CAM++, Score-CAM, Eigen-CAM… **Dùng để đối chiếu** với `src/xai/gradcam.py` tự viết, xem có ra cùng kết quả không | ⚪ |

---

## E. Mất cân bằng lớp và tăng cường dữ liệu

Nhóm này giải quyết vấn đề đã biết chắc: **lệch lớp 14,4 lần**, `mosaic_virus` chỉ
373 ảnh so với `yellow_leaf_curl_virus` 5.357 ảnh. Đọc trước khi làm **#15**.

| Mã | Bài | Nguồn · Năm | Đáng chú ý | TT |
|---|---|---|---|---|
| **E1** | [Data-Centric Preprocessing Outperforms Loss Modifications for Hard-Class Plant Disease Classification Using MobileNetV3](https://jurnal.uny.ac.id/index.php/elinvo/article/view/95319) | Elinvo · 2025 | **Kết quả ngược trực giác, đã xác minh:** trên MobileNetV3-Small, 12 lớp khó — cross-entropy thường **0,9668** > focal loss mặc định 0,9647 > trọng số tần suất nghịch đảo 0,9621. Kết luận: hướng **data-centric** hơn hẳn sửa hàm mất mát (+4,08 điểm). → Nhóm **không thêm class weight** vào `train.py`, có căn cứ | ✅ |
| **E2** | [Classification of imbalanced multi-label leaf diseases using CaRiT: class attention enabled RegionViT](https://link.springer.com/article/10.1007/s11042-023-17678-8) | MTAP · 2024 | Hướng attention theo lớp cho dữ liệu lệch | ⚪ |
| **E3** | [Handling imbalance and few-sample size in ML based Onion disease classification](https://arxiv.org/pdf/2509.05341) | arXiv · 2025 | Bài toán nhỏ, dữ liệu ít — giống tình cảnh phần quả của mình | ⚪ |
| **E4** | [FWDGAN-based data augmentation for tomato leaf disease identification](https://www.sciencedirect.com/science/article/abs/pii/S0168169922000965) | Comput. Electron. Agric. · 2022 | GAN sinh ảnh lá cà chua | ⚪ |
| **E5** | [Tomato plant disease detection using transfer learning with C-GAN synthetic images](https://www.sciencedirect.com/science/article/abs/pii/S0168169921002969) | Comput. Electron. Agric. · 2021 | **99,51%** cho bài 5 lớp nhờ ảnh tổng hợp | ⚪ |
| **E6** | [Enhanced classification performance through GauGAN-based data augmentation for tomato leaf images](https://ietresearch.onlinelibrary.wiley.com/doi/10.1049/ipr2.13069) | IET Image Process. · 2024 | — | ⚪ |
| **E7** | [Harnessing the power of diffusion models for plant disease image augmentation](https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2023.1280496/full) | Front. Plant Sci. · 2023 | Diffusion thay cho GAN — mới hơn, ảnh sạch hơn | ⚪ |
| **E8** | [New Method for Tomato Disease Detection Based on Image Segmentation and Cycle-GAN Enhancement](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11510809/) | PMC · 2024 | Tách nền + Cycle-GAN — **liên quan trực tiếp tới A2**, vì tách nền là một cách chống thiên lệch nền | ⚪ |

> Cảnh báo về nhóm GAN (E4–E8): sinh ảnh giả rồi báo accuracy tăng là chỗ **rất dễ
> bị hỏi vặn** — ảnh giả có lọt vào tập test không? Nếu làm, phải nói rõ chỉ augment
> tập train. Với thời gian còn lại, ưu tiên **chụp ảnh thật** hơn là sinh ảnh giả.

---

## F. Biết khi nào không nên trả lời — open-set / OOD

Nhóm này phục vụ **nhánh `khác`** của bộ định tuyến trong `CLAUDE.md`: người dùng
chụp cái gì đó không phải lá/quả cà chua thì hệ thống phải nói "chụp lại giúp mình"
chứ không được trả về "Mốc lá 87%".

| Mã | Bài | Nguồn · Năm | Đáng chú ý | TT |
|---|---|---|---|---|
| **F1** | [The impact of fine-tuning paradigms on unknown plant diseases recognition](https://www.nature.com/articles/s41598-024-66958-2) · [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC11297179/) | Sci. Rep. · 2024 | Dựng chuẩn đo cho **OSR, OOD và few-shot OOD trên 5 bộ dữ liệu bệnh cây**. Bài vào việc nhất nhóm này | ⚪ |
| **F2** | [Known and unknown class recognition on plant species and diseases](https://www.sciencedirect.com/science/article/abs/pii/S0168169923007962) | Comput. Electron. Agric. · 2023 | Nhận cả loài lẫn bệnh, có nhánh từ chối | ⚪ |
| **F3** | [A New Deep Learning-based Dynamic Paradigm Towards Open-World Plant Disease Detection](https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2023.1243822/full) | Front. Plant Sci. · 2023 | — | ⚪ |
| **F4** | [Enhancing anomaly detection in plant disease recognition with knowledge ensemble](https://pmc.ncbi.nlm.nih.gov/articles/PMC12394223/) | PMC · 2025 | — | ⚪ |
| **F5** | [Harnessing prototype networks for novel plant species and disease classification in open-world scenarios](https://www.sciencedirect.com/science/article/abs/pii/S0952197625010164) | Eng. Appl. AI · 2025 | — | ⚪ |

> Lưu ý thực tế: cách rẻ nhất là **ngưỡng độ tin cậy** — dưới ngưỡng thì trả lời
> "không chắc". Đọc F1 để biết ngưỡng đơn giản yếu tới đâu rồi mới quyết có làm phức
> tạp hơn không. Đừng làm OSR đầy đủ trước cổng go/no-go 15/09.

---

## G. Bệnh trên quả — mốc 6, chỉ đọc sau 15/09

⚠️ **Chưa qua cổng go/no-go thì đừng đụng nhóm này.** Để đây cho khỏi phải tìm lại.

| Mã | Bài | Nguồn · Năm | Đáng chú ý | TT |
|---|---|---|---|---|
| **G1** | [Disease Detection in Tomato Fruit Using Deep Learning Algorithms: Comparative Analysis](https://www.researchgate.net/publication/393194012_Disease_Detection_in_Tomato_Fruit_Using_Deep_Learning_Algorithms_Comparative_Analysis) | ResearchGate · 2025 | **5 lớp: Anthracnose, Bacterial Spot, Botrytis, Fruit Worm Bore, Cracking** — trùng 2 lớp với mình. Tập 1.295 train / 370 test / 185 val, cỡ đúng bằng mục tiêu ~1.500 ảnh của mình | ⚪ |
| **G2** | [Identification of Tomato Disease Types and Detection of Infected Areas Based on Deep CNN and Object Detection](https://onlinelibrary.wiley.com/doi/10.1155/2019/9142753) — Wang et al. | Comput. Intell. Neurosci. · 2019 | 10 bệnh **trên quả**, có cả `blossom-end rot` và `anthracnose` — đúng hai lớp mới của mình | ⚪ |
| **G3** | [Tomato Triage: Tomato Fruit Disease Detection and Pesticide Strategies using Deep Learning](https://www.researchgate.net/publication/382679407_Tomato_Triage_Tomato_Fruit_Disease_Detection_and_Pesticide_Strategies_using_Deep_Learning) | ResearchGate · 2024 | Có phần khuyến nghị xử lý — giống phần lời khuyên tiếng Việt của mình | ⚪ |
| **G4** | [Comparative Analysis of Deep Learning-Based Feature Extraction and Traditional Classification Approaches for Tomato Disease Detection](https://doi.org/10.3390/agronomy15071509) | Agronomy · 2025 | 21 kiến trúc trích đặc trưng + 5 cách chọn đặc trưng | ⚪ |
| **G5** | [Multi-stage tomato fruit recognition method based on improved YOLOv8](https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2024.1447263/full) | Front. Plant Sci. · 2024 | Nhận diện quả theo giai đoạn chín | ⚪ |
| **G6** | [Vegetable disease detection using an improved YOLOv8 algorithm in the greenhouse plant environment](https://www.nature.com/articles/s41598-024-54540-9) | Sci. Rep. · 2024 | Có lớp **blossom end rot** trong bốn lớp họ làm | ⚪ |
| **G7** | [Optimization of Improved YOLOv8 for Precision Tomato Leaf Disease Detection in Sustainable Agriculture](https://www.mdpi.com/1424-8220/25/5/1398) | Sensors · 2025 | — | ⚪ |
| **G8** | [DM-YOLO: improved YOLOv9 model for tomato leaf disease detection](https://pmc.ncbi.nlm.nih.gov/articles/PMC11850125/) | PMC · 2025 | — | ⚪ |

> Nhóm YOLO (G5–G8) làm **phát hiện có khung bao**, không phải phân loại cả ảnh như
> mình. Đọc để biết khác biệt, nhưng **đừng đổi sang YOLO** — đổi bài toán giữa chừng
> là tự sát về tiến độ.

---

## H. Bộ dữ liệu để đo domain gap

Cần cho **rủi ro số 1**.

> ⚠️ **Cập nhật 15/09/2026 — mục này đã bị thực tế bác bỏ một phần. Đọc trước khi tin bảng dưới.**
>
> Ảnh tự chụp ở Đà Lạt: **hoãn vô thời hạn** (không liên hệ được nhà vườn, xem `CLAUDE.md`
> rủi ro số 1). Và câu *"ba bộ dưới đây tải về đo được ngay"* **sai với H1**: đã tải về kiểm
> thì H1 không gán nhãn phân loại được, đã **loại hẳn**. Bộ đo chính nay là **H2 (PlantDoc)**.
> Căn cứ đầy đủ: `docx/Plan_model.md` mục 5.2.

| Mã | Bộ dữ liệu | Quy mô | Vì sao dùng | TT |
|---|---|---|---|---|
| ~~**H1**~~ | ~~[Tomato leaf dataset](https://pmc.ncbi.nlm.nih.gov/articles/PMC12008584/) — Imtiaz et al., Data in Brief 2025 · [Mendeley](https://doi.org/10.17632/bpfd9cns5g.2)~~ | Công bố "731 ảnh, 7 lớp, chụp tại Bangladesh". **Đếm thật: 308 ảnh gốc** (phần còn lại là bản nhân bản Roboflow) | ❌ **ĐÃ LOẠI 15/09/2026.** Bản trên Mendeley là export Roboflow/YOLO **không kèm `data.yaml`** → không biết class ID nào là bệnh nào; 230/689 ảnh có nhãn đa lớp → không gán được một nhãn/ảnh. Xem `docx/Plan_model.md` mục 5.2 | ❌ |
| **H2** | [PlantDoc](https://github.com/pratikkayal/PlantDoc-Dataset) — Singh et al., CoDS-COMAD 2020 · [bài báo](https://dl.acm.org/doi/10.1145/3371158.3371196) | Bài báo ghi 2.598 ảnh / 13 loài / 17 lớp. **Phần cà chua tự đếm 15/09: 744 ảnh dùng được trên 8 lớp** (675 `train` + 69 `test`) | **Bộ đo chính của đề tài.** Chia thư mục theo lớp, tên thư mục viết rõ bằng chữ nên **không phải đoán ánh xạ** — khác hẳn H1. Thiếu `target_spot`; `spider_mites` chỉ 2 ảnh nên loại khỏi phép đo | ✅ |
| **H3** | Taiwan tomato leaves | 622 ảnh, 6 lớp (bacterial spot 100, black mold 67, gray spot 84, healthy 106, late blight 98, powdery mildew 157) | Ảnh có bóng đổ, nhiều lá chồng, nền lộn xộn. Chỉ trùng 3 lớp với mình. Xem cách dùng trong **B1** | ⚪ |
| **H4** | [Benchmarking In-the-Wild Multimodal Plant Disease Recognition and A Versatile Baseline](https://arxiv.org/html/2408.03120v1) | — | Chuẩn đo mới cho ảnh ngoài tự nhiên | ⚪ |

> **Bài học 15/09/2026, đáng ghi lại hơn cả bảng trên:** dòng H1 cũ ở đây từng viết
> *"Dùng được ngay hôm nay… chạy `evaluate.py` lên bộ này là có ngay con số domain gap"*,
> và được đánh dấu ✅ chỉ vì **đã mở được toàn văn bài báo** — chưa ai tải bộ dữ liệu về
> kiểm. Khi tải về thì nhãn không tra được.
>
> Rút ra hai điều cho mọi dòng trong bảng này:
>
> 1. **Cột TT (✅/⚠️/⚪) nói về bài báo, không nói về bộ dữ liệu.** Một bộ ✅ vẫn có thể
>    không dùng được. Với nhóm H, phải kiểm riêng: đếm file theo lớp, băm tìm ảnh trùng,
>    đối chiếu ánh xạ nhãn — **trước khi** ghi số vào báo cáo.
> 2. **Đừng trích quy mô từ bài báo.** H1 công bố 731 ảnh, thật ra 308. Số của H2 trong
>    bảng trên là **tự đếm**, nên dùng được.
>
> Phần kiểm chứng này không phải công toi — nó là nội dung **đánh giá chất lượng dữ liệu**,
> trả lời trực tiếp câu phản biện *"nhóm chọn dữ liệu thế nào"* (xem câu **11** trong
> `02-cau-hoi-phan-bien.md`).

---

## Đã đọc — ghi chú ở đâu

Tổng hợp đối chiếu toàn bộ những bài dưới đây với kết quả huấn luyện của nhóm nằm ở
**[`03-tong-hop-doi-chieu.md`](03-tong-hop-doi-chieu.md)**.

| Mã | Ngày đọc | Mức | Thu được gì |
|---|---|---|---|
| A1 | 07/09/2026 | toàn văn | Bảng 5 tỉ lệ chia tập · **31,40% trên ảnh điều kiện khác** |
| A2 | 07/09/2026 | toàn văn | 8 pixel nền → 49,0%; xoá nền không hết thiên lệch |
| A3 | 07/09/2026 | toàn văn | PlantVillage 90,18% vs đồng ruộng 84,66% |
| D4 | 07/09/2026 | toàn văn | Bảng chỉ số từng lớp; **không nêu rõ augment trước hay sau khi chia** |
| E1 | 07/09/2026 | toàn văn | CE 0,9668 > focal 0,9647 > class weight 0,9621 |
| D1 | 07/09/2026 | tóm tắt | Tác giả tự nhận heatmap thô; lối ra là Guided Grad-CAM |
| D2 | 07/09/2026 | tóm tắt | Đạo hàm riêng dương; mạnh khi nhiều vết rời rạc. Chưa lấy được công thức |
