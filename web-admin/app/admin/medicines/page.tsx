import Link from "next/link";

import { adminFetch } from "@/lib/api";
import * as ui from "@/lib/ui";
import { ConfirmSubmitButton } from "@/components/ConfirmSubmitButton";
import type { DiseaseInfo, DiseaseMedicineOut, MedicineOut } from "@/lib/types";

import {
  createAssignmentAction,
  deleteAssignmentAction,
  deleteMedicineAction,
} from "./actions";
import { MedicineFormModal } from "./MedicineFormModal";

export const metadata = { title: "Thuốc gợi ý — AgriXAI Admin" };

export default async function MedicinesPage({
  searchParams,
}: {
  searchParams: Promise<{ new?: string; edit?: string; disease?: string; error?: string }>;
}) {
  const sp = await searchParams;

  const [medicines, diseases] = await Promise.all([
    adminFetch<MedicineOut[]>("/medicines"),
    adminFetch<DiseaseInfo[]>("/diseases"),
  ]);

  const selectedDisease = sp.disease || diseases[0]?.key || "";
  const assignments = selectedDisease
    ? await adminFetch<DiseaseMedicineOut[]>("/medicines/assignments", {
        searchParams: { disease_key: selectedDisease },
      })
    : [];

  const editingMedicine = sp.edit ? medicines.find((m) => m.id === Number(sp.edit)) : undefined;
  const assignedIds = new Set(assignments.map((a) => a.medicine_id));
  const availableForAssignment = medicines.filter((m) => !assignedIds.has(m.id));

  return (
    <div>
      <h1 className="mb-5 text-xl font-extrabold tracking-[-0.01em]">Thuốc gợi ý</h1>

      {sp.error && (
        <div className="mb-4 rounded-xl border border-severe/25 bg-severe-bg px-4 py-2.5 text-sm font-semibold text-severe">
          {sp.error}
        </div>
      )}

      <div className="mb-3.5 flex items-center justify-between">
        <div className="text-[15px] font-bold">Danh sách thuốc bảo vệ thực vật</div>
        <Link href="/admin/medicines?new=1" className={ui.btnPrimary}>
          + Thêm thuốc
        </Link>
      </div>
      <div className={`${ui.card} mb-7`}>
        <table className="w-full border-collapse text-[13px]">
          <thead>
            <tr className="bg-canvas">
              <th className={ui.th}>Tên thuốc</th>
              <th className={ui.th}>Nhóm hoạt chất</th>
              <th className={ui.th}>Link mua</th>
              <th className={ui.th}></th>
            </tr>
          </thead>
          <tbody>
            {medicines.map((m) => (
              <tr key={m.id} className={ui.tr}>
                <td className={`${ui.td} font-semibold`}>{m.name}</td>
                <td className={ui.td}>{m.group ?? "—"}</td>
                <td className={ui.td}>
                  {m.purchase_url ? (
                    <a href={m.purchase_url} target="_blank" rel="noreferrer">
                      Xem sản phẩm
                    </a>
                  ) : (
                    "—"
                  )}
                </td>
                <td className={`${ui.td} whitespace-nowrap text-right`}>
                  <Link
                    href={`/admin/medicines?edit=${m.id}`}
                    className="mr-1 rounded-lg p-1.5 text-ink/60 hover:bg-ink/8"
                    aria-label="Sửa"
                  >
                    ✎
                  </Link>
                  <form action={deleteMedicineAction.bind(null, m.id)} className="inline">
                    <ConfirmSubmitButton
                      confirmMessage={`Xoá thuốc "${m.name}"? Mọi lượt gán cho bệnh cũng bị gỡ theo.`}
                      className="rounded-lg p-1.5 text-ink/60 hover:bg-severe-bg hover:text-severe"
                    >
                      ✕
                    </ConfirmSubmitButton>
                  </form>
                </td>
              </tr>
            ))}
            {medicines.length === 0 && (
              <tr>
                <td colSpan={4} className="px-4 py-8 text-center text-ink/60">
                  Chưa có thuốc nào
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="mb-3.5 text-[15px] font-bold">Gán thuốc theo bệnh</div>
      <div className={`${ui.card} p-5`}>
        <form className="mb-4">
          <select name="disease" defaultValue={selectedDisease} className={`${ui.select} w-auto`}>
            {diseases.map((d) => (
              <option key={d.key} value={d.key}>
                {d.name_vi}
              </option>
            ))}
          </select>
          <button type="submit" className={`${ui.btnGhost} ml-2`}>
            Xem
          </button>
        </form>

        <div className="mb-4 grid gap-2.5">
          {assignments.map((a) => (
            <div
              key={a.id}
              className="flex items-start justify-between gap-3 rounded-xl bg-canvas px-3.5 py-3"
            >
              <div>
                <div className="text-[13px] font-bold">{a.medicine_name}</div>
                {a.note && <div className="mt-0.5 text-xs text-ink/70">{a.note}</div>}
              </div>
              <form action={deleteAssignmentAction.bind(null, a.id, selectedDisease)}>
                <ConfirmSubmitButton
                  confirmMessage={`Gỡ thuốc "${a.medicine_name}" khỏi bệnh này?`}
                  className="shrink-0 text-[13px] text-ink/60 hover:text-severe"
                >
                  ✕
                </ConfirmSubmitButton>
              </form>
            </div>
          ))}
          {assignments.length === 0 && (
            <p className="rounded-xl bg-accent/14 px-3.5 py-3 text-[13px] text-accent-ink">
              Bệnh này chưa được gán thuốc nào.
            </p>
          )}
        </div>

        {availableForAssignment.length > 0 ? (
          <form action={createAssignmentAction} className="flex flex-wrap items-end gap-2">
            <input type="hidden" name="disease_key" value={selectedDisease} />
            <select name="medicine_id" required className={`${ui.select} w-auto`}>
              {availableForAssignment.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.name}
                </option>
              ))}
            </select>
            <input
              name="note"
              placeholder="Ghi chú sử dụng..."
              className={`${ui.input} min-w-[180px] flex-1`}
            />
            <button type="submit" className={ui.btnPrimary}>
              Gán
            </button>
          </form>
        ) : (
          medicines.length > 0 && (
            <p className="text-xs text-ink/60">Mọi thuốc trong danh mục đã được gán cho bệnh này.</p>
          )
        )}
      </div>

      {sp.new === "1" && <MedicineFormModal />}
      {editingMedicine && <MedicineFormModal medicine={editingMedicine} />}
    </div>
  );
}
