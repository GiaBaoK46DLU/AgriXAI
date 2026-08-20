"""Mô hình nhận diện bệnh lá cà chua + XAI (phần phụ trách: Gia Bảo)."""

import sys

__version__ = "0.1.0"

# Ép UTF-8 cho output.
#
# Mọi script trong package này đều in tiếng Việt. Chạy thẳng trong terminal thì
# không sao, nhưng khi output bị chuyển hướng ra file hoặc pipe, Python trên
# Windows thôi dùng console API và rơi về bảng mã cp1252 — bảng này không có ký
# tự tiếng Việt, nên chương trình sập giữa chừng với UnicodeEncodeError. Nghĩa
# là một lượt huấn luyện dài đang chạy sẽ chết ngay dòng in đầu tiên chỉ vì
# người dùng muốn giữ log:
#
#     python -m src.training.train > outputs/logs/train.log
#
# Đặt ở đây vì src/__init__.py là chỗ duy nhất mà mọi lệnh `python -m src.*`
# đều đi qua, nên sửa một lần là hết cho toàn bộ script.
for _stream in (sys.stdout, sys.stderr):
    # Không phải lúc nào cũng là TextIOWrapper — pythonw không có stdout, còn
    # pytest thay stdout bằng đối tượng bắt output riêng của nó.
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")
