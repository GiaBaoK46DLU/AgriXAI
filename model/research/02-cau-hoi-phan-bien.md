# Câu hỏi phản biện ↔ bài báo trả lời được

Mười câu dưới đây là loại hội đồng hay hỏi với đề tài nhận diện bệnh cây. Cột cuối
ghi bài nào trong `00-danh-muc-bai-bao.md` giúp trả lời.

Trả lời có trích dẫn khác hẳn trả lời bằng cảm tính — nhất là ở những câu mà câu trả
lời thành thật lại là điểm yếu của đề tài.

---

### 1. "Accuracy 99% có đáng tin không, hay mô hình học cái nền ảnh?"

Câu **nguy hiểm nhất** và gần như chắc chắn bị hỏi.

Trả lời thẳng: PlantVillage **có thiên lệch nền đã được chứng minh** — chỉ dùng 8 pixel
nền đã đoán đúng 49% trong khi đoán mò là 2,6%, và xoá nền không hết thiên lệch. Nhóm
em biết điều đó nên đã (a) đo thêm trên bộ ảnh đồng ruộng, (b) kiểm tra Grad-CAM có
khoanh vào lá hay vào nền.

→ **A2** (bằng chứng), **TN-3** trong `01-ke-hoach-thi-nghiem.md` (mình tự kiểm)

### 2. "Ra đồng thật thì tụt bao nhiêu?"

Có con số của người khác để đối chiếu: review 2024 đo được PlantVillage trung bình
90,18% còn dữ liệu đồng ruộng tự thu 84,66%. Con số của mình đo trên bộ H1 để cạnh đó.

→ **A3**, **H1**, **H2**

### 3. "Sao chọn EfficientNet-B0 mà không phải ResNet/DenseNet/ViT?"

Đừng trả lời "vì nó nhẹ". Trả lời bằng **bảng TN-1 do chính mình đo**, kèm đối chiếu
với các công bố khác.

→ **B1**, **B4**, **B6**, **B8**, bảng TN-1

### 4. "Sao không dùng Vision Transformer, nó mới hơn mà?"

ViT-Base đạt ~99,17% trên PlantVillage, tức **ngang chứ không vượt hẳn** CNN, đổi lại
là nhiều tham số hơn và suy luận chậm hơn. Với ràng buộc demo trên máy backend thì
đánh đổi đó không có lợi.

→ **B4**, **B5**, **C1**, **C4**

### 5. "Lớp `mosaic_virus` chỉ có 373 ảnh, mô hình nhận được không?"

Câu này **chắc chắn có** vì tự mình phải nêu trong báo cáo. Trả lời bằng recall từng
lớp chứ không bằng accuracy tổng, cộng với kết quả TN-4.

→ **E1**, **E2**, TN-4, issue **#15**

### 6. "Grad-CAM có đúng không, hay chỉ là hình cho đẹp?"

Đây là chỗ **mạnh nhất** của đề tài nếu làm TN-3. Grad-CAM là phương pháp *hậu nghiệm*
— nó cho biết mô hình nhìn vào đâu, không chứng minh mô hình suy luận đúng. Nhưng đo
được tỉ lệ heatmap rơi vào vùng lá là một cách kiểm chứng định lượng.

→ **D1** (bài gốc, nêu rõ hạn chế), **D2**, **D3**, **D11**, TN-3

### 7. "Đề tài khác gì các công trình đã có?"

Câu trả lời nằm ở **D4**: XSE-TomatoNet cũng EfficientNet-B0 + Grad-CAM trên cà chua,
99,11%. Họ dừng ở **heatmap kỹ thuật cho người nghiên cứu xem**. Đề tài này đi tiếp
một bước: chuyển heatmap thành **vùng khoanh đơn giản + một câu tiếng Việt thường
ngày cho nông dân**.

Củng cố bằng **D9**: khảo sát 40 nông dân thật cho thấy họ cần diễn giải kết quả, không
cần biết mô hình chạy thế nào. Tức khoảng trống này là có thật, không phải mình tự nghĩ ra.

→ **D4**, **D9**, **D10**

### 8. "Người dùng chụp nhầm cây khác thì sao?"

Hệ thống phải biết nói "không chắc". Hiện tại làm bằng ngưỡng độ tin cậy; hướng đầy đủ
là open-set recognition.

→ **F1**, **F2**, **F3**

### 9. "Sao không làm bệnh trên thân?"

Đã có sẵn câu trả lời trong `CLAUDE.md`: héo rũ Fusarium/Ralstonia **về bản chất không
chẩn đoán được qua ảnh** — phải cắt ngang thân xem bó mạch. Đây là **giới hạn của bài
toán chứ không phải của mô hình**. Nói được điều đó cho thấy hiểu bản chất nông học.

→ không cần bài báo, nhưng **A4** có bảng bệnh cà chua để dẫn chứng phạm vi

### 10. "Suy luận mất bao lâu, demo có kịp không?"

Đo thật rồi báo, kèm cấu hình máy. Nhóm C cho mốc so sánh nếu bị hỏi về triển khai
trên thiết bị yếu.

→ **C1**, **C2**, **C5**, rủi ro số 2 trong `CLAUDE.md`

---

## Ba câu trả lời thành thật ăn điểm hơn là né

1. **"Mô hình của em chưa chắc chạy tốt ngoài đồng, đây là con số cụ thể và đây là lý do."**
   Có A2 + A3 chống lưng thì đây là hiểu biết chuyên môn, không phải điểm yếu.
2. **"Cách xử lý lệch lớp em thử không cải thiện gì."**
   Kết quả âm tính có đo đạc vẫn là kết quả. E1 cho thấy các tác giả khác cũng gặp vậy.
3. **"Grad-CAM cho biết mô hình nhìn vào đâu, không chứng minh nó suy luận đúng."**
   Chính bài gốc D1 nói vậy. Trả lời thế cho thấy đã đọc bài gốc chứ không dùng theo phong trào.
