import { notFound } from "next/navigation";

import { adminFetch, ApiError, storageUrl } from "@/lib/api";
import { Modal } from "@/components/Modal";
import { Tag, severityTone } from "@/components/Tag";
import type { DiagnosisDetail, UserOut } from "@/lib/types";

function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString("vi-VN", { dateStyle: "short", timeStyle: "short" });
}

/** Chỉ nhận `diagnosisId` — cố tình KHÔNG nhận `userName` từ trang danh sách
 * gọi vào. Trang danh sách chỉ biết tên nông dân trong DANH SÁCH ĐÃ LỌC/PHÂN
 * TRANG hiện tại; khi mở modal này từ một nơi khác (ví dụ liên kết "Xem lần
 * chẩn đoán liên kết" trong chi tiết bài diễn đàn), bản ghi thường không nằm
 * trong trang hiện tại nên tra theo cách đó luôn ra "—". Modal tự fetch
 * user theo `user_id` của chính bản ghi, độc lập với danh sách gọi nó. */
export async function DiagnosisDetailModal({ diagnosisId }: { diagnosisId: number }) {
  let d: DiagnosisDetail;
  try {
    d = await adminFetch<DiagnosisDetail>(`/diagnoses/${diagnosisId}`);
  } catch (err) {
    // `?detail=` bị sửa tay thành một id không tồn tại — hiện trang 404 thay vì
    // để lỗi ApiError chưa bắt làm sập cả trang danh sách chẩn đoán.
    if (err instanceof ApiError && err.status === 404) notFound();
    throw err;
  }

  let userName = "—";
  try {
    const user = await adminFetch<UserOut>(`/users/${d.user_id}`);
    userName = user.full_name;
  } catch (err) {
    if (!(err instanceof ApiError && err.status === 404)) throw err;
  }

  // Người dùng tải lên 3–5 ảnh mỗi lần chẩn đoán, mỗi ảnh có kết quả riêng
  // (xem `DiagnosisImageOut`); `d.image_url`/`d.overlay_url` ở cấp ngoài chỉ là
  // MỘT ảnh đại diện (`agg.representative` — xem `diagnosis_service.py`) được
  // chọn để hiển thị nhanh ở danh sách. Bản trước chỉ vẽ hai ảnh đó nên admin
  // không xem được phần còn lại của lô ảnh. Ảnh chẩn đoán cũ (trước khi có
  // tính năng nhiều ảnh) không có `d.images` — dựng tạm một phần tử từ dữ liệu
  // cấp ngoài để vẫn hiển thị được, không vỡ giao diện.
  const images = d.images.length > 0
    ? d.images
    : [
        {
          id: 0,
          disease_key: d.disease_key,
          disease_name: d.disease_name,
          confidence: d.confidence,
          image_path: d.image_path,
          overlay_path: d.overlay_path,
          image_url: d.image_url,
          overlay_url: d.overlay_url,
        },
      ];

  return (
    <Modal title={d.disease_name} closeHref="/admin/diagnoses" maxWidth={900}>
      <div className="-mt-3 mb-4 flex items-center gap-2.5">
        <Tag tone={severityTone(d.severity)}>{d.severity_name}</Tag>
        <span className="text-[13px] text-ink/65">
          {userName} · {d.plot_name ?? d.plot_puc ?? "Không gắn lô"} · {formatDateTime(d.created_at)}{" "}
          · Độ tin cậy {d.confidence.toFixed(1)}%
        </span>
      </div>

      <div className="mb-1.5 flex items-center justify-between text-xs font-semibold text-ink/60">
        <span>Ảnh đã tải lên ({images.length})</span>
        <span>Gốc / Khoanh vùng vết bệnh (Grad-CAM)</span>
      </div>
      <div className="mb-4.5 flex gap-3 overflow-x-auto pb-1">
        {images.map((img, i) => (
          <div key={img.id} className="w-[220px] shrink-0 rounded-2xl border border-border bg-canvas p-2.5">
            <div className="mb-1.5 flex items-center justify-between text-[11px] font-semibold text-ink/55">
              <span>Ảnh {i + 1}</span>
              <span>{img.confidence.toFixed(1)}%</span>
            </div>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={storageUrl(img.image_url)}
              alt={`Ảnh gốc ${i + 1}`}
              className="mb-1.5 h-[120px] w-full rounded-xl object-cover"
            />
            {img.overlay_url ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={storageUrl(img.overlay_url)}
                alt={`Ảnh khoanh vùng ${i + 1}`}
                className="h-[120px] w-full rounded-xl object-cover"
              />
            ) : (
              <div className="flex h-[120px] items-center justify-center rounded-xl bg-none-bg text-center text-[11px] text-ink/50">
                Không khoanh vùng
                <br />
                (heatmap quá yếu)
              </div>
            )}
            {img.disease_key !== d.disease_key && (
              <div className="mt-1.5 text-[11px] font-semibold text-accent-ink">
                Ảnh này: {img.disease_name}
              </div>
            )}
          </div>
        ))}
      </div>

      {d.explanation && (
        <div className="mb-4.5 rounded-2xl bg-canvas p-4">
          <div className="mb-1.5 text-[13px] font-bold">Vì sao mô hình kết luận vậy?</div>
          <div className="text-[13px] leading-relaxed">{d.explanation}</div>
        </div>
      )}

      {d.note && (
        <div className="mb-4.5 text-[13px]">
          <span className="font-bold">Ghi chú người dùng: </span>
          {d.note}
        </div>
      )}

      <div className="mb-2.5 text-[13px] font-bold">Top 3 khả năng</div>
      {d.top_predictions.map((t) => (
        <div key={t.disease_key} className="mb-2.5">
          <div className="mb-1 flex justify-between text-[13px]">
            <span>{t.name_vi}</span>
            <span className="text-ink/60">{(t.probability * 100).toFixed(1)}%</span>
          </div>
          <div className="h-2 rounded-full bg-none-bg">
            <div
              className="h-full rounded-full bg-primary-light"
              style={{ width: `${t.probability * 100}%` }}
            />
          </div>
        </div>
      ))}
    </Modal>
  );
}
