<!--
Tiêu đề PR đặt như commit: type(scope): short description
Ví dụ: feat(mobile): add diagnosis result screen
-->

## Issue

<!-- "Closes #26" để issue tự đóng khi merge -->

Closes #

## Đã làm gì

<!-- Tóm tắt cho người review, không phải chép lại danh sách commit -->

## Đã tự kiểm

- [ ] Toàn bộ tiêu chí hoàn thành trong issue đã tick
- [ ] Đã chạy thử thật, không chỉ "code trông có vẻ đúng"
- [ ] Đã thử ít nhất một ca lỗi (mất mạng, sai mật khẩu, dữ liệu rỗng…)
- [ ] `pytest` trong `backend/` vẫn pass — nếu PR có đụng tới backend
- [ ] Không commit `.env`, checkpoint, `node_modules/`, ảnh dữ liệu
- [ ] Commit chia nhỏ theo từng nhiệm vụ, đọc `git log` hiểu được
- [ ] Tên nhánh đúng quy ước `<bao|hoc>/task-<số issue>-<mô tả>`

## Đã chạy thử thế nào

<!-- Thao tác cụ thể + kết quả. Có ảnh chụp màn hình thì càng tốt. -->

## Chỗ cần người review để ý

<!--
Chỗ tự thấy chưa chắc, hoặc quyết định có thể bàn lại.

Nếu PR đụng tới `model/src/predictor.py` hoặc `shared/data/tomato_diseases.json`
thì nói rõ ở đây — đó là hợp đồng dùng chung giữa hai phần, đổi là ảnh hưởng
người kia.
-->
