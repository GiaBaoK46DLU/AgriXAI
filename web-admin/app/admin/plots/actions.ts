"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { adminFetch, ApiError } from "@/lib/api";

const BASE = "/admin/plots";

function errorRedirect(message: string): never {
  redirect(`${BASE}?new=1&error=${encodeURIComponent(message)}`);
}

// Chỉ CREATE — không có sửa/xoá qua trang này. Chốt 30/09/2026 (xem CLAUDE.md):
// chỉ quản trị được tạo lô đất, luôn gán thẳng cho một nông dân (owner_id bắt
// buộc — backend 422/403 nếu thiếu hoặc gọi bởi tài khoản không phải admin).
// Đây không còn là "tạo hộ" tạm thời mà là con đường DUY NHẤT tạo lô đất trong
// hệ thống; nông dân chỉ nhận lô rồi tự sửa cây trồng/trạng thái/ghi chú trên
// mobile (`PATCH /plots/{id}`, giới hạn ở `FARMER_EDITABLE_FIELDS`).
export async function createPlotAction(formData: FormData) {
  const name = String(formData.get("name") ?? "").trim();
  const ownerId = Number(formData.get("owner_id"));
  if (!name) errorRedirect("Nhập tên lô đất");
  if (!Number.isFinite(ownerId) || ownerId <= 0) errorRedirect("Chọn chủ lô đất");

  const puc = String(formData.get("puc") ?? "").trim();
  const region = String(formData.get("region") ?? "").trim();
  const areaRaw = String(formData.get("area_m2") ?? "").trim();
  const note = String(formData.get("note") ?? "").trim();
  const status = String(formData.get("status") ?? "active");

  try {
    await adminFetch("/plots", {
      method: "POST",
      body: {
        name,
        owner_id: ownerId,
        puc: puc || undefined,
        region: region || undefined,
        area_m2: areaRaw ? Number(areaRaw) : undefined,
        note: note || undefined,
        status,
      },
    });
  } catch (err) {
    errorRedirect(err instanceof ApiError ? err.message : "Không tạo được lô đất");
  }

  revalidatePath(BASE);
  redirect(BASE);
}
