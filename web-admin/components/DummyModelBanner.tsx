import { WarningIcon } from "@/components/icons";
import { getHealth } from "@/lib/api";

/** Dải cảnh báo mô hình giả (#34/WA-07) — cố ý sống trong `AdminLayout` chứ
 * không riêng ở trang tổng quan, để hiện trên MỌI trang có số liệu như ticket
 * yêu cầu. Không có nút đóng: cho tắt thì sẽ có người tắt rồi quên mất. */
export async function DummyModelBanner() {
  const health = await getHealth();
  if (health.using_real_model) return null;

  return (
    <div className="flex items-start gap-3 border-b border-accent/35 bg-accent/14 px-7 py-3 text-sm font-semibold text-accent-ink">
      <WarningIcon className="mt-0.5 shrink-0" width={18} height={18} />
      <span>
        Đang chạy mô hình giả ({health.model_version}) — số liệu chẩn đoán hiện có không có ý
        nghĩa thực tế. Trỏ <code className="rounded bg-white/50 px-1">MODEL_CHECKPOINT</code> trong{" "}
        <code className="rounded bg-white/50 px-1">backend/.env</code> tới checkpoint thật để
        chuyển đổi.
      </span>
    </div>
  );
}
