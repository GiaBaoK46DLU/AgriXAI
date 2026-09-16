"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { adminFetch, ApiError } from "@/lib/api";
import type { DiseaseGuideOut } from "@/lib/types";

const BASE = "/admin/guides";

function errorRedirect(message: string): never {
  redirect(`${BASE}?error=${encodeURIComponent(message)}`);
}

export async function saveGuideAction(diseaseKey: string, formData: FormData) {
  const videoUrl = String(formData.get("video_url") ?? "").trim();
  if (!videoUrl) errorRedirect("Nhập link video trước khi lưu");

  try {
    await adminFetch<DiseaseGuideOut>(`/medicines/guides/${diseaseKey}`, {
      method: "PUT",
      body: { video_url: videoUrl },
    });
  } catch (err) {
    errorRedirect(err instanceof ApiError ? err.message : "Không lưu được video");
  }

  revalidatePath(BASE);
  redirect(BASE);
}

export async function deleteGuideAction(diseaseKey: string) {
  try {
    await adminFetch(`/medicines/guides/${diseaseKey}`, { method: "DELETE" });
  } catch (err) {
    errorRedirect(err instanceof ApiError ? err.message : "Không gỡ được video");
  }

  revalidatePath(BASE);
  redirect(BASE);
}
