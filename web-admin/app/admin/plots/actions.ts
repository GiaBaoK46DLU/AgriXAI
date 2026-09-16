"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { adminFetch, ApiError } from "@/lib/api";

const BASE = "/admin/plots";

function errorRedirect(message: string): never {
  redirect(`${BASE}?new=1&error=${encodeURIComponent(message)}`);
}

// Chỉ CREATE — lô đất vẫn là dữ liệu của nông dân, admin chỉ hỗ trợ tạo hộ
// (nhiều nông dân không tự thêm được), không có sửa/xoá qua trang này. Quyết
// định "chỉ đọc" trước đây (xem CLAUDE.md) đổi đúng phạm vi được yêu cầu, không
// mở rộng thêm.
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
