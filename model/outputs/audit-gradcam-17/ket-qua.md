# Kết quả đo Grad-CAM với mặt nạ khoanh tay (#17)

Sinh tự động bởi `src/xai/audit_score.py` — đừng sửa tay.

**KL** = tỉ lệ khối lượng bản đồ nhiệt · **DT** = tỉ lệ diện tích ô · **Tập trung** = KL ÷ DT (1,00× = rải đều, không ưu tiên gì) · **Nâng chuẩn hoá** = (KL − DT) ÷ (1 − DT), tức đi được bao nhiêu phần đoạn đường từ đoán mò (0,00) tới hoàn hảo (1,00). Chỉ đại lượng cuối so được giữa hai bộ ảnh có tỉ lệ diện tích lá khác nhau.

Mọi con số là **trung bình theo từng ảnh** (mỗi ảnh một phiếu), không phải gộp theo pixel.

## So hai bộ cạnh nhau — bảng chính

| | `pv` | `pd` |
|---|--:|--:|
| Số ảnh | 30 | 26 |
| Đoán đúng | 30/30 | 7/26 |
| Diện tích lá (khoanh tay) | 45,2 % | 70,0 % |
| Khối lượng heatmap trong lá | 68,6 % | 72,0 % |
| **Mức tập trung vào lá** | 1,65× | 1,10× |
| Trần lý thuyết của mức tập trung | 2,21× | 1,43× |
| **Nâng chuẩn hoá vào lá** | 0,41 | 0,03 |
| Đỉnh heatmap nằm trong lá | 93,3 % | 80,8 % |
| Đỉnh heatmap nằm trên vết bệnh | 53,3 % | 26,9 % |

Chỉ tính riêng nhóm **vết bệnh khu trú được** — nhóm duy nhất mà tỉ lệ vết-bệnh / lá-lành có nghĩa:

| | `pv` | `pd` |
|---|--:|--:|
| Số ảnh | 15 | 13 |
| Diện tích vết bệnh | 11,4 % | 18,3 % |
| Khối lượng heatmap trên vết bệnh | 19,8 % | 26,1 % |
| **Mức tập trung vào vết bệnh** | 1,88× | 1,56× |
| **Nâng chuẩn hoá vào vết bệnh** | 0,10 | 0,10 |
| Đỉnh heatmap nằm trên vết bệnh | 33,3 % | 38,5 % |
| Vùng app khoanh — phần trên vết bệnh | 31,5 % | 37,7 % |
| Vùng app khoanh — phần trên nền | 13,2 % | 22,2 % |

## Mặt nạ khoanh tay so với mặt nạ Otsu tự động — **trên đúng cùng một tập ảnh**

Đây là phép so mà #49 không làm được, và là lý do #17 tồn tại. Hai cột của mỗi bộ chạy trên cùng ảnh, cùng bản đồ nhiệt — khác nhau **duy nhất** ở chỗ mặt nạ lá lấy từ đâu.

| | `pv` tay | `pv` Otsu | `pd` tay | `pd` Otsu |
|---|--:|--:|--:|--:|
| Diện tích lá | 45,2 % | 33,2 % | 70,0 % | 47,3 % |
| Khối lượng heatmap trong lá | 68,6 % | 55,7 % | 72,0 % | 46,8 % |
| **Mức tập trung** | 1,65× | 1,82× | 1,10× | 0,99× |
| **Nâng chuẩn hoá** | 0,41 | 0,33 | 0,03 | 0,01 |
| Đỉnh heatmap nằm trong lá | 93,3 % | 73,3 % | 80,8 % | 42,3 % |

## Bộ `pv` — PlantVillage (tap test cua data/processed/split.csv)

30 ảnh, mô hình đoán đúng 30/30.

### Gộp, và tách theo kiểu triệu chứng

| Nhóm | n | KL vết bệnh | KL lá lành | KL nền | DT vết bệnh | Tập trung vết bệnh | DT lá | KL lá | Tập trung lá | Nâng chuẩn hoá (lá) | Đỉnh trong lá | Đỉnh trên vết |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| **Toàn bộ** | 30 | 31,7 % | 36,9 % | 31,4 % | 15,8 % | 1,99× | 45,2 % | 68,6 % | 1,65× | 0,41 | 93,3 % | 53,3 % |
| vết bệnh khu trú được | 15 | 19,8 % | 48,9 % | 31,3 % | 11,4 % | 1,88× | 50,7 % | 68,7 % | 1,48× | 0,35 | 86,7 % | 33,3 % |
| triệu chứng khuếch tán cả phiến lá | 12 | 54,4 % | 14,5 % | 31,0 % | 25,4 % | 2,13× | 36,2 % | 69,0 % | 1,95× | 0,51 | 100,0 % | 91,7 % |
| không khoanh được vết bệnh nào | 3 | 0,0 % | 66,7 % | 33,3 % | 0,0 % | — | 53,2 % | 66,7 % | 1,25× | 0,29 | 100,0 % | 0,0 % |
| *chỉ ảnh đoán đúng* | 30 | 31,7 % | 36,9 % | 31,4 % | 15,8 % | 1,99× | 45,2 % | 68,6 % | 1,65× | 0,41 | 93,3 % | 53,3 % |
| *bỏ ảnh có vấn đề dữ liệu* | 30 | 31,7 % | 36,9 % | 31,4 % | 15,8 % | 1,99× | 45,2 % | 68,6 % | 1,65× | 0,41 | 93,3 % | 53,3 % |

### Theo từng lớp (n=3 — chỉ đọc định tính)

| Nhóm | n | KL vết bệnh | KL lá lành | KL nền | DT vết bệnh | Tập trung vết bệnh | DT lá | KL lá | Tập trung lá | Nâng chuẩn hoá (lá) | Đỉnh trong lá | Đỉnh trên vết |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| Đốm lá vi khuẩn | 3 | 11,8 % | 58,4 % | 29,8 % | 10,9 % | 1,23× | 58,7 % | 70,2 % | 1,20× | 0,27 | 66,7 % | 0,0 % |
| Đốm vòng (đốm nâu) | 3 | 17,3 % | 40,9 % | 41,8 % | 15,1 % | 1,33× | 55,6 % | 58,2 % | 1,05× | 0,05 | 66,7 % | 33,3 % |
| Lá khoẻ mạnh | 3 | 0,0 % | 66,7 % | 33,3 % | 0,0 % | — | 53,2 % | 66,7 % | 1,25× | 0,29 | 100,0 % | 0,0 % |
| Mốc sương muộn | 3 | 45,9 % | 29,6 % | 24,5 % | 16,7 % | 3,31× | 39,8 % | 75,5 % | 2,34× | 0,61 | 100,0 % | 100,0 % |
| Mốc lá | 3 | 45,8 % | 24,8 % | 29,4 % | 19,0 % | 2,39× | 40,0 % | 70,6 % | 1,82× | 0,50 | 100,0 % | 100,0 % |
| Virus khảm | 3 | 62,4 % | 0,7 % | 36,9 % | 30,4 % | 2,08× | 32,1 % | 63,1 % | 1,97× | 0,46 | 100,0 % | 100,0 % |
| Đốm lá Septoria | 3 | 20,7 % | 40,5 % | 38,8 % | 12,2 % | 1,98× | 48,6 % | 61,2 % | 1,26× | 0,24 | 100,0 % | 33,3 % |
| Nhện đỏ hai chấm | 3 | 57,5 % | 10,6 % | 31,9 % | 24,8 % | 2,25× | 31,0 % | 68,1 % | 2,20× | 0,54 | 100,0 % | 100,0 % |
| Đốm mắt cua | 3 | 3,5 % | 74,9 % | 21,6 % | 1,9 % | 1,53× | 51,0 % | 78,4 % | 1,53× | 0,57 | 100,0 % | 0,0 % |
| Virus xoăn vàng lá | 3 | 52,0 % | 22,0 % | 26,1 % | 27,2 % | 1,77× | 41,8 % | 73,9 % | 1,83× | 0,55 | 100,0 % | 66,7 % |

### Vùng app thật sự khoanh cho nông dân (ô có CAM ≥ 0,5)

| Nhóm | n | % diện tích ảnh | trên vết bệnh | trên lá lành | trên nền |
|---|--:|--:|--:|--:|--:|
| **Toàn bộ** | 30 | 17,0 % | 48,6 % | 44,2 % | 7,3 % |
| vết bệnh khu trú được | 15 | 19,3 % | 31,5 % | 55,3 % | 13,2 % |
| triệu chứng khuếch tán cả phiến lá | 12 | 12,0 % | 82,1 % | 17,5 % | 0,4 % |
| không khoanh được vết bệnh nào | 3 | 25,2 % | 0,0 % | 95,2 % | 4,8 % |

### Kiểm chứng: dùng CAM THÔ (chưa chuẩn hoá min-max)

| Nhóm | n | KL vết bệnh | KL lá lành | KL nền | Tập trung lá |
|---|--:|--:|--:|--:|--:|
| **Toàn bộ** | 30 | 29,4 % | 35,7 % | 34,9 % | 1,44× |
| vết bệnh khu trú được | 15 | 18,9 % | 47,4 % | 33,7 % | 1,31× |
| triệu chứng khuếch tán cả phiến lá | 12 | 49,8 % | 13,9 % | 36,2 % | 1,76× |
| không khoanh được vết bệnh nào | 3 | 0,0 % | 64,0 % | 36,0 % | 1,20× |

Độ phẳng CAM thô (trung bình ÷ đỉnh; càng gần 1 càng phẳng): **0,30** (KTC 95 %: 0,26–0,34)

## Bộ `pd` — PlantDoc (742 anh, manifest data/processed/plantdoc-all/split.csv)

26 ảnh, mô hình đoán đúng 7/26.

### Gộp, và tách theo kiểu triệu chứng

| Nhóm | n | KL vết bệnh | KL lá lành | KL nền | DT vết bệnh | Tập trung vết bệnh | DT lá | KL lá | Tập trung lá | Nâng chuẩn hoá (lá) | Đỉnh trong lá | Đỉnh trên vết |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| **Toàn bộ** | 26 | 20,3 % | 51,8 % | 28,0 % | 15,6 % | 1,32× | 70,0 % | 72,0 % | 1,10× | 0,03 | 80,8 % | 26,9 % |
| vết bệnh khu trú được | 13 | 26,1 % | 48,9 % | 25,0 % | 18,3 % | 1,56× | 73,9 % | 75,0 % | 1,11× | -0,03 | 76,9 % | 38,5 % |
| triệu chứng khuếch tán cả phiến lá | 9 | 20,8 % | 53,2 % | 25,9 % | 18,7 % | 0,96× | 71,1 % | 74,1 % | 1,05× | 0,07 | 88,9 % | 22,2 % |
| không khoanh được vết bệnh nào | 4 | 0,0 % | 57,8 % | 42,2 % | 0,0 % | — | 54,6 % | 57,8 % | 1,16× | 0,10 | 75,0 % | 0,0 % |
| *chỉ ảnh đoán đúng* | 7 | 36,7 % | 53,3 % | 10,1 % | 24,2 % | 1,90× | 87,2 % | 89,9 % | 1,04× | 0,30 | 85,7 % | 57,1 % |
| *chỉ ảnh đoán sai* | 19 | 14,2 % | 51,2 % | 34,5 % | 12,5 % | 1,04× | 63,6 % | 65,5 % | 1,12× | -0,03 | 78,9 % | 15,8 % |
| *bỏ ảnh có vấn đề dữ liệu* | 22 | 23,2 % | 52,7 % | 24,1 % | 17,6 % | 1,39× | 74,1 % | 75,9 % | 1,07× | 0,04 | 77,3 % | 31,8 % |

### Theo từng lớp (n=3 — chỉ đọc định tính)

| Nhóm | n | KL vết bệnh | KL lá lành | KL nền | DT vết bệnh | Tập trung vết bệnh | DT lá | KL lá | Tập trung lá | Nâng chuẩn hoá (lá) | Đỉnh trong lá | Đỉnh trên vết |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| Đốm lá vi khuẩn | 3 | 24,1 % | 29,1 % | 46,8 % | 14,8 % | 1,67× | 38,6 % | 53,2 % | 1,61× | 0,21 | 100,0 % | 33,3 % |
| Đốm vòng (đốm nâu) | 3 | 12,5 % | 54,6 % | 32,9 % | 10,7 % | 0,97× | 71,3 % | 67,1 % | 0,93× | -0,04 | 33,3 % | 0,0 % |
| Lá khoẻ mạnh | 3 | 0,0 % | 63,2 % | 36,8 % | 0,0 % | — | 64,6 % | 63,2 % | 0,98× | 0,06 | 66,7 % | 0,0 % |
| Mốc sương muộn | 3 | 52,3 % | 47,4 % | 0,3 % | 28,9 % | 2,73× | 99,3 % | 99,7 % | 1,00× | 0,54 | 100,0 % | 100,0 % |
| Mốc lá | 3 | 7,6 % | 70,8 % | 21,6 % | 7,7 % | 0,82× | 73,8 % | 78,4 % | 1,08× | 0,17 | 100,0 % | 0,0 % |
| Virus khảm | 3 | 34,0 % | 24,7 % | 41,2 % | 26,9 % | 1,59× | 50,0 % | 58,8 % | 1,28× | 0,15 | 66,7 % | 33,3 % |
| Đốm lá Septoria | 3 | 19,4 % | 52,5 % | 28,2 % | 20,9 % | 1,01× | 77,7 % | 71,8 % | 0,93× | -0,46 | 66,7 % | 33,3 % |
| Nhện đỏ hai chấm | 2 | 4,7 % | 63,6 % | 31,7 % | 7,1 % | 0,67× | 74,0 % | 68,3 % | 0,92× | -0,22 | 100,0 % | 0,0 % |
| Virus xoăn vàng lá | 3 | 22,7 % | 63,9 % | 13,4 % | 20,7 % | 0,96× | 81,8 % | 86,6 % | 1,08× | 0,21 | 100,0 % | 33,3 % |

### Vùng app thật sự khoanh cho nông dân (ô có CAM ≥ 0,5)

| Nhóm | n | % diện tích ảnh | trên vết bệnh | trên lá lành | trên nền |
|---|--:|--:|--:|--:|--:|
| **Toàn bộ** | 26 | 22,1 % | 27,7 % | 46,9 % | 25,4 % |
| vết bệnh khu trú được | 13 | 23,9 % | 37,7 % | 40,1 % | 22,2 % |
| triệu chứng khuếch tán cả phiến lá | 9 | 20,4 % | 25,6 % | 49,1 % | 25,3 % |
| không khoanh được vết bệnh nào | 4 | 20,4 % | 0,0 % | 64,2 % | 35,8 % |

### Kiểm chứng: dùng CAM THÔ (chưa chuẩn hoá min-max)

| Nhóm | n | KL vết bệnh | KL lá lành | KL nền | Tập trung lá |
|---|--:|--:|--:|--:|--:|
| **Toàn bộ** | 26 | 19,7 % | 52,4 % | 27,9 % | 1,03× |
| vết bệnh khu trú được | 13 | 25,1 % | 50,0 % | 24,9 % | 1,02× |
| triệu chứng khuếch tán cả phiến lá | 9 | 20,7 % | 53,4 % | 25,9 % | 1,04× |
| không khoanh được vết bệnh nào | 4 | 0,0 % | 57,8 % | 42,2 % | 1,06× |

Độ phẳng CAM thô (trung bình ÷ đỉnh; càng gần 1 càng phẳng): **0,32** (KTC 95 %: 0,28–0,37)
