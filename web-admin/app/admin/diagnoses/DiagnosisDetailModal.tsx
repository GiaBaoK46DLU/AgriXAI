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
  const d = await adminFetch<DiagnosisDetail>(`/diagnoses/${diagnosisId}`);

  let userName = "—";
  try {
    const user = await adminFetch<UserOut>(`/users/${d.user_id}`);
    userName = user.full_name;
  } catch (err) {
    if (!(err instanceof ApiError && err.status === 404)) throw err;
  }

  return (
    <Modal title={d.disease_name} closeHref="/admin/diagnoses" maxWidth={780}>
      <div className="-mt-3 mb-4 flex items-center gap-2.5">
        <Tag tone={severityTone(d.severity)}>{d.severity_name}</Tag>
        <span className="text-[13px] text-ink/65">
          {userName} · {d.plot_name ?? d.plot_puc ?? "Không gắn lô"} · {formatDateTime(d.created_at)}{" "}
          · Độ tin cậy {d.confidence.toFixed(1)}%
        </span>
      </div>

      <div className="mb-4.5 grid grid-cols-2 gap-3.5">
        <div>
          <div className="mb-1.5 text-xs font-semibold text-ink/60">Ảnh gốc</div>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={storageUrl(d.image_url)}
            alt="Ảnh lá gốc"
            className="h-[260px] w-full rounded-2xl object-cover"
          />
        </div>
        <div>
          <div className="mb-1.5 text-xs font-semibold text-ink/60">
            Ảnh khoanh vùng vết bệnh (Grad-CAM)
          </div>
          {d.overlay_url ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={storageUrl(d.overlay_url)}
              alt="Ảnh khoanh vùng XAI"
              className="h-[260px] w-full rounded-2xl object-cover"
            />
          ) : (
            <div className="flex h-[260px] items-center justify-center rounded-2xl bg-canvas text-sm text-ink/60">
              Không khoanh vùng (heatmap quá yếu)
            </div>
          )}
        </div>
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
