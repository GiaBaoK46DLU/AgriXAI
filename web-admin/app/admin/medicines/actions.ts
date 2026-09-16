"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { adminFetch, ApiError } from "@/lib/api";
import type { DiseaseMedicineOut, MedicineOut } from "@/lib/types";

const BASE = "/admin/medicines";

function errorRedirect(disease: string | undefined, message: string): never {
  const suffix = disease ? `&disease=${encodeURIComponent(disease)}` : "";
  redirect(`${BASE}?error=${encodeURIComponent(message)}${suffix}`);
}

export async function createMedicineAction(formData: FormData) {
  const payload = {
    name: String(formData.get("name") ?? "").trim(),
    group: String(formData.get("group") ?? "").trim() || null,
    purchase_url: String(formData.get("purchase_url") ?? "").trim() || null,
  };

  try {
    await adminFetch<MedicineOut>("/medicines", { method: "POST", body: payload });
  } catch (err) {
    errorRedirect(undefined, err instanceof ApiError ? err.message : "Không tạo được thuốc");
  }

  revalidatePath(BASE);
  redirect(BASE);
}

export async function updateMedicineAction(medicineId: number, formData: FormData) {
  const payload = {
    name: String(formData.get("name") ?? "").trim(),
    group: String(formData.get("group") ?? "").trim() || null,
    purchase_url: String(formData.get("purchase_url") ?? "").trim() || null,
  };

  try {
    await adminFetch<MedicineOut>(`/medicines/${medicineId}`, { method: "PATCH", body: payload });
  } catch (err) {
    errorRedirect(undefined, err instanceof ApiError ? err.message : "Không sửa được thuốc");
  }

  revalidatePath(BASE);
  redirect(BASE);
}

export async function deleteMedicineAction(medicineId: number) {
  try {
    await adminFetch(`/medicines/${medicineId}`, { method: "DELETE" });
  } catch (err) {
    errorRedirect(undefined, err instanceof ApiError ? err.message : "Không xoá được thuốc");
  }

  revalidatePath(BASE);
  redirect(BASE);
}

export async function createAssignmentAction(formData: FormData) {
  const diseaseKey = String(formData.get("disease_key") ?? "");
  const payload = {
    disease_key: diseaseKey,
    medicine_id: Number(formData.get("medicine_id")),
    note: String(formData.get("note") ?? "").trim() || null,
  };

  try {
    await adminFetch<DiseaseMedicineOut>("/medicines/assignments", { method: "POST", body: payload });
  } catch (err) {
    errorRedirect(diseaseKey, err instanceof ApiError ? err.message : "Không gán được thuốc");
  }

  revalidatePath(BASE);
  redirect(`${BASE}?disease=${encodeURIComponent(diseaseKey)}`);
}

export async function deleteAssignmentAction(assignmentId: number, diseaseKey: string) {
  try {
    await adminFetch(`/medicines/assignments/${assignmentId}`, { method: "DELETE" });
  } catch (err) {
    errorRedirect(diseaseKey, err instanceof ApiError ? err.message : "Không gỡ được lượt gán");
  }

  revalidatePath(BASE);
  redirect(`${BASE}?disease=${encodeURIComponent(diseaseKey)}`);
}
