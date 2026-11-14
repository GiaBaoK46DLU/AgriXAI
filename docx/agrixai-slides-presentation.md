# BỘ SLIDE BẢO VỆ ĐỒ ÁN TỐT NGHIỆP: AgriXAI
**Chủ đề:** Ứng dụng Nhận diện bệnh cây trồng kết hợp XAI
**Phong cách:** Chuyên nghiệp, Học thuật, Tối giản
**Định dạng thiết kế chung:** 
- Font chữ: Times New Roman, cỡ chữ to (≥ 24pt cho nội dung).
- Màu sắc: Nền Trắng/Xám nhạt, Tiêu đề Xanh Navy đậm, Chữ nội dung Đen/Xám đậm.
- Hình ảnh: Line icons, sơ đồ khối (network diagram), ảnh minh họa thực tế mộc mạc.

---

## Slide 1: Trang bìa (Title Slide)
**Tiêu đề:** ỨNG DỤNG NHẬN DIỆN BỆNH CÂY TRỒNG KẾT HỢP XAI (EXPLAINABLE AI)
**Nội dung:**
- **Đồ án tốt nghiệp:** Khoa Công nghệ Thông tin - Trường Đại học Đà Lạt
- **Giáo viên hướng dẫn:** TS. Nguyễn Thị Lương
- **Sinh viên thực hiện:** 
  - Đinh Lâm Gia Bảo (2212343) - AI & XAI
  - Triệu Quang Học (2212375) - Backend & System
- **Lớp:** CTK46B - **Năm học:** 2026

---

## Slide 2: Nội dung trình bày (Agenda)
**Tiêu đề:** NỘI DUNG BÁO CÁO
**Nội dung:**
- Đặt vấn đề và Mục tiêu đề tài.
- Cơ sở lý thuyết và Giải pháp công nghệ.
- Kiến trúc và Xây dựng hệ thống.
- Quá trình phát triển Mô hình & XAI.
- Kết quả đạt được & Demo thực nghiệm.
- Hướng phát triển và Kết luận.

---

## Slide 3: Đặt vấn đề (Problem Statement)
**Tiêu đề:** ĐẶT VẤN ĐỀ
**Hình ảnh đề xuất:** Icon cảnh báo, hoặc ảnh nông dân cầm lá cây bị bệnh với dấu chấm hỏi.
**Nội dung:**
- Bệnh hại cây trồng làm giảm năng suất nghiêm trọng nhưng nông dân thiếu chuyên môn chẩn đoán sớm.
- Các mô hình AI hiện tại có độ chính xác cao nhưng hoạt động như một "hộp đen" (Black-box).
- AI chỉ trả về tên bệnh mà không giải thích, gây ra sự thiếu tin tưởng từ người dùng thực tế.
- Chưa có hệ thống toàn diện kết nối từ di động (chẩn đoán) đến quản trị tập trung (dashboard).

---

## Slide 4: Mục tiêu đề tài (Objectives)
**Tiêu đề:** MỤC TIÊU ĐỀ TÀI
**Hình ảnh đề xuất:** Icon mục tiêu (target) hoặc bóng đèn sáng tạo (lightbulb).
**Nội dung:**
- Xây dựng mô hình AI phân loại bệnh trên lá cây với độ chính xác cao.
- Tích hợp XAI (Explainable AI) để trực quan hóa, giải thích lý do hệ thống đưa ra kết quả.
- Phát triển ứng dụng di động cho nông dân: dễ sử dụng, phản hồi nhanh, giải thích tiếng Việt.
- Xây dựng Web Admin và hệ thống Backend quản lý, thống kê bệnh hại tập trung.

---

## Slide 5: Phạm vi nghiên cứu (Scope)
**Tiêu đề:** PHẠM VI NGHIÊN CỨU
**Hình ảnh đề xuất:** Lưới danh sách hoặc icon cây cà chua.
**Nội dung:**
- Đối tượng chính: Bệnh trên lá cây cà chua.
- Bộ dữ liệu: PlantVillage và dữ liệu thu thập thực tế.
- Phân loại 10 lớp: 9 loại bệnh phổ biến và 1 lớp lá khỏe mạnh.
- Các bệnh tiêu biểu: Đốm vi khuẩn, Đốm vòng, Mốc sương, Nhện đỏ,...
- Nền tảng: App Flutter (Mobile) và Next.js (Web Admin).

---

## Slide 6: Cơ sở lý thuyết - Explainable AI (XAI)
**Tiêu đề:** EXPLAINABLE AI (XAI) VÀ GRAD-CAM
**Hình ảnh đề xuất:** Sơ đồ luồng ảnh đi qua CNN sinh ra heatmap Grad-CAM.
**Nội dung:**
- **XAI:** Kỹ thuật giúp minh bạch hóa quy trình ra quyết định của các mô hình học sâu.
- **Grad-CAM:** Dùng đạo hàm của đặc trưng cuối để tạo bản đồ nhiệt (heatmap) thể hiện vùng ảnh quan trọng.
- Vấn đề của Grad-CAM: Bản đồ nhiệt màu sắc gây khó hiểu cho người không chuyên (nông dân).
- Giải pháp: Chuyển đổi heatmap thành khoanh vùng (bounding box/elip) trực quan, rõ ràng trên ảnh thực.

---

## Slide 7: Kiến trúc hệ thống tổng quan (Architecture)
**Tiêu đề:** KIẾN TRÚC HỆ THỐNG
**Hình ảnh đề xuất:** Đưa sơ đồ kiến trúc hệ thống (Mobile, Web, Backend, Database, AI Model) vào giữa.
**Nội dung:**
- **Frontend:** Mobile App (Flutter) cho nông dân; Web Admin (React/Vite) quản trị.
- **Backend:** FastAPI xử lý nghiệp vụ, giao tiếp HTTP/JSON mượt mà.
- **AI Core (DiseasePredictor):** Tách biệt logic mô hình PyTorch & XAI, dễ dàng nâng cấp.
- **Lưu trữ:** PostgreSQL (metadata) và hệ thống lưu trữ ảnh gốc/ảnh XAI.

---

## Slide 8: Xây dựng dữ liệu huấn luyện (Dataset)
**Tiêu đề:** DỮ LIỆU HUẤN LUYỆN
**Hình ảnh đề xuất:** Biểu đồ phân bổ dữ liệu (pie chart) hoặc 3 ảnh lá bệnh đại diện.
**Nội dung:**
- Sử dụng tập dữ liệu chuẩn PlantVillage cho 10 lớp phân loại cà chua.
- Bổ sung ảnh chụp ngoài đồng thực tế để khắc phục độ lệch miền (Domain Gap).
- Quá trình tiền xử lý: Resize, Augmentation (xoay, lật, điều chỉnh độ sáng) để tăng tính đa dạng.
- Phân chia tập dữ liệu: Train (huấn luyện), Validation (kiểm chứng), Test (đánh giá).

---

## Slide 9: Huấn luyện Mô hình phân loại (Model Training)
**Tiêu đề:** HUẤN LUYỆN MÔ HÌNH HỌC SÂU
**Hình ảnh đề xuất:** Biểu đồ đường (Line chart) thể hiện Loss/Accuracy giảm/tăng theo Epoch.
**Nội dung:**
- Kiến trúc áp dụng: Mạng nơ-ron chập (CNN) kết hợp Transfer Learning.
- Quá trình huấn luyện sử dụng PyTorch với checkpoint tự động.
- Tinh chỉnh tham số (Hyperparameter tuning) tối ưu hóa độ chính xác nhận diện.
- Kết quả mô hình đạt độ chính xác cao trên tập Validation trước khi tích hợp.

---

## Slide 10: Quy trình tạo ảnh XAI (XAI Pipeline)
**Tiêu đề:** QUY TRÌNH KẾT HỢP XAI VÀO CHUẨN ĐOÁN
**Hình ảnh đề xuất:** Luồng 4 bước: Ảnh gốc -> AI -> Heatmap -> Ảnh khoanh vùng elip.
**Nội dung:**
- Bước 1: Mô hình phân loại trích xuất đặc trưng và đưa ra dự đoán xác suất.
- Bước 2: Grad-CAM tính toán và nội suy bản đồ nhiệt tại khu vực phát hiện vết bệnh.
- Bước 3: Thuật toán Image Processing lọc nhiễu, vẽ elip khoanh vùng chính xác vết bệnh.
- Bước 4: Ghép nhãn chẩn đoán và câu giải thích tiếng Việt để trả về cho người dùng.

---

## Slide 11: Xây dựng Backend & CSDL
**Tiêu đề:** HỆ THỐNG BACKEND & CƠ SỞ DỮ LIỆU
**Hình ảnh đề xuất:** Icon FastAPI và PostgreSQL.
**Nội dung:**
- Sử dụng **FastAPI**: Tốc độ cao, hỗ trợ Async/Await, sinh tài liệu API (Swagger) tự động.
- Quản lý cơ sở dữ liệu **PostgreSQL** chặt chẽ: Tài khoản, lô đất, lịch sử chẩn đoán.
- Thiết kế Interface `DiseasePredictor` độc lập: Backend gọi AI như một black-box đã được bọc lại.
- Tối ưu hóa lưu trữ file: Quản lý ảnh gốc chụp từ thiết bị và ảnh sinh ra bởi XAI riêng biệt.

---

## Slide 12: Ứng dụng Mobile cho nông dân
**Tiêu đề:** ỨNG DỤNG MOBILE (FLUTTER)
**Hình ảnh đề xuất:** 2-3 mockup màn hình điện thoại (Trang chủ, Chụp ảnh, Kết quả chẩn đoán).
**Nội dung:**
- Phát triển bằng Flutter: Hoạt động mượt mà đa nền tảng (Android/iOS).
- Giao diện trực quan: Danh sách lô đất, tính năng chụp/tải ảnh bệnh cây dễ dùng.
- Tốc độ xử lý: Kết quả trả về kèm ảnh phân tích XAI dưới 3 giây.
- Cung cấp giải pháp: Hiển thị hướng dẫn xử lý và gợi ý thuốc bảo vệ thực vật.

---

## Slide 13: Giao diện Web Admin quản trị
**Tiêu đề:** HỆ THỐNG WEB ADMIN
**Hình ảnh đề xuất:** Ảnh chụp màn hình Dashboard quản trị (có biểu đồ).
**Nội dung:**
- Xây dựng bằng Next.js (React) cho tốc độ tải trang nhanh, giao diện hiện đại.
- **Dashboard:** Thống kê tổng quan số lượng chẩn đoán, tỉ lệ các loại bệnh qua biểu đồ.
- Quản lý danh mục: Cập nhật thông tin bệnh lý, tài khoản người dùng và bài đăng diễn đàn.
- Hỗ trợ ra quyết định tập trung cho cán bộ nông nghiệp hoặc nhà quản lý.

---

## Slide 14: Kịch bản Thực nghiệm (Demo)
**Tiêu đề:** KỊCH BẢN THỰC NGHIỆM TÍCH HỢP
**Hình ảnh đề xuất:** Timeline 3 bước đơn giản (Chụp -> AI Xử lý -> Dashboard nhận).
**Nội dung:**
- Ứng dụng Mobile: Nông dân chọn lô đất cà chua, chụp ảnh lá bệnh gửi đi.
- Máy chủ AI xử lý: Nhận diện "Đốm lá vi khuẩn - 87%" và vẽ khoanh vùng giải thích.
- Kết quả hiển thị tức thời: Thông báo tình trạng, hướng dẫn xử lý hiện trên Mobile.
- Đồng bộ Admin: Quản trị viên mở Web Dashboard, bản ghi mới và biểu đồ tự động cập nhật.

---

## Slide 15: Kết quả đạt được
**Tiêu đề:** KẾT QUẢ ĐẠT ĐƯỢC
**Hình ảnh đề xuất:** Icon Checkmark hoặc cúp vinh danh.
**Nội dung:**
- Xây dựng thành công toàn bộ hệ thống khép kín: Mô hình AI, Backend, Web, Mobile.
- Cải thiện niềm tin người dùng: Đổi Grad-CAM kỹ thuật thành ảnh khoanh vùng thân thiện.
- Kiến trúc decouple (tách rời): Hệ thống hoạt động độc lập, không gián đoạn giữa team AI và Backend.
- Đảm bảo độ trễ thấp (latency) cho luồng chẩn đoán từ Mobile đến AI.

---

## Slide 16: Hạn chế & Thách thức
**Tiêu đề:** ĐÁNH GIÁ VÀ HẠN CHẾ
**Hình ảnh đề xuất:** Icon phân tích (magnifying glass) hoặc thước đo.
**Nội dung:**
- **Domain gap:** Đạt độ chính xác cao trên PlantVillage nhưng ảnh thực tế ngoài đồng còn nhiễu (ánh sáng, nền đất).
- Tài nguyên tính toán: Tốc độ suy luận (Inference time) phụ thuộc cấu hình máy chủ triển khai.
- Khuyến cáo thuốc: Dữ liệu hiện tại mang tính học thuật, cần tham vấn chuyên gia thực tiễn để tăng tính an toàn.
- Cần mở rộng bộ dữ liệu cho nhiều loại cây trồng khác nhau.

---

## Slide 17: Hướng phát triển tương lai
**Tiêu đề:** HƯỚNG PHÁT TRIỂN
**Hình ảnh đề xuất:** Icon mũi tên hướng lên (growth/future).
**Nội dung:**
- Thu thập thêm ảnh thực tế tại vườn để Fine-tune, khắc phục triệt để Domain Gap.
- Tích hợp chéo với các hệ thống khác (Nhật ký canh tác, Bản đồ số GIS - định vị ổ dịch).
- Tối ưu hóa mô hình AI: Chuyển đổi (Quantization) để có thể chạy offline ngay trên điện thoại.
- Triển khai cảnh báo tự động SMS/Email cho cộng đồng khi phát hiện vùng dịch diện rộng.

---

## Slide 18: Kết luận & Lời cảm ơn
**Tiêu đề:** KẾT LUẬN & CẢM ƠN
**Hình ảnh đề xuất:** Ảnh tập thể nhóm hoặc icon handshake.
**Nội dung:**
- Đề tài chứng minh tính khả thi của việc đưa Explainable AI vào nông nghiệp thực tế.
- Giải quyết bài toán "niềm tin" của nông dân bằng cách minh bạch hóa dự đoán của máy móc.
- Trân trọng cảm ơn TS. Nguyễn Thị Lương đã tận tình định hướng, hướng dẫn nhóm.
- Cảm ơn quý Thầy Cô trong Hội đồng đã lắng nghe.
- **Q&A - Mời Hội đồng đặt câu hỏi.**
