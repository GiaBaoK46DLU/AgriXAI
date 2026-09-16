import { Modal } from "@/components/Modal";
import * as ui from "@/lib/ui";
import type { UserOut } from "@/lib/types";

import { createPlotAction } from "./actions";

const STATUS_OPTIONS: { value: string; label: string }[] = [
  { value: "active", label: "Đang canh tác" },
  { value: "fallow", label: "Bỏ hoá" },
  { value: "archived", label: "Lưu trữ" },
];

/** Nhiều nông dân không tự thêm được lô đất qua app — admin tạo hộ ở đây.
 * `owner_id` bắt buộc chọn (khác app mobile, nơi lô đất luôn tự gán cho chính
 * người tạo) vì đây là chỗ DUY NHẤT hệ thống cho tạo lô đất thay người khác —
 * backend chỉ nhận `owner_id` từ tài khoản admin (xem `POST /plots`). */
export function PlotFormModal({ farmers }: { farmers: UserOut[] }) {
  return (
    <Modal title="Thêm lô đất" closeHref="/admin/plots" maxWidth={520}>
      <form action={createPlotAction} className="grid gap-3">
        <div>
          <label className={ui.label}>Tên lô</label>
          <input name="name" required className={ui.input} />
        </div>
        <div>
          <label className={ui.label}>Chủ lô (nông dân)</label>
          <select name="owner_id" required defaultValue="" className={ui.select}>
            <option value="" disabled>
              Chọn nông dân...
            </option>
            {farmers.map((f) => (
              <option key={f.id} value={f.id}>
                {f.full_name} ({f.username})
              </option>
            ))}
          </select>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className={ui.label}>Mã PUC</label>
            <input name="puc" placeholder="Để trống để tự sinh" className={ui.input} />
          </div>
          <div>
            <label className={ui.label}>Trạng thái</label>
            <select name="status" defaultValue="active" className={ui.select}>
              {STATUS_OPTIONS.map((s) => (
                <option key={s.value} value={s.value}>
                  {s.label}
                </option>
              ))}
            </select>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className={ui.label}>Khu vực</label>
            <input name="region" className={ui.input} />
          </div>
          <div>
            <label className={ui.label}>Diện tích (m²)</label>
            <input name="area_m2" type="number" min={0} step="0.1" className={ui.input} />
          </div>
        </div>
        <div>
          <label className={ui.label}>Ghi chú</label>
          <input name="note" className={ui.input} />
        </div>

        <div className="mt-1 flex justify-end gap-2.5">
          <a href="/admin/plots" className={ui.btnGhost}>
            Huỷ
          </a>
          <button type="submit" className={ui.btnPrimary}>
            Tạo lô đất
          </button>
        </div>
      </form>
    </Modal>
  );
}
