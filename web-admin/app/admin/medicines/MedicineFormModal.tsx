import { Modal } from "@/components/Modal";
import * as ui from "@/lib/ui";
import type { MedicineOut } from "@/lib/types";

import { createMedicineAction, updateMedicineAction } from "./actions";

export function MedicineFormModal({ medicine }: { medicine?: MedicineOut }) {
  const isEdit = Boolean(medicine);
  const action = isEdit ? updateMedicineAction.bind(null, medicine!.id) : createMedicineAction;

  return (
    <Modal title={isEdit ? "Sửa thuốc" : "Thêm thuốc"} closeHref="/admin/medicines">
      <form action={action} className="grid gap-3">
        <div>
          <label className={ui.label}>Tên thuốc</label>
          <input name="name" defaultValue={medicine?.name} required className={ui.input} />
        </div>
        <div>
          <label className={ui.label}>Nhóm hoạt chất</label>
          <input name="group" defaultValue={medicine?.group ?? ""} className={ui.input} />
        </div>
        <div>
          <label className={ui.label}>Link mua sản phẩm</label>
          <input
            name="purchase_url"
            type="url"
            defaultValue={medicine?.purchase_url ?? ""}
            className={ui.input}
          />
        </div>

        <div className="mt-2 flex justify-end gap-2.5">
          <a href="/admin/medicines" className={ui.btnGhost}>
            Huỷ
          </a>
          <button type="submit" className={ui.btnPrimary}>
            Lưu
          </button>
        </div>
      </form>
    </Modal>
  );
}
