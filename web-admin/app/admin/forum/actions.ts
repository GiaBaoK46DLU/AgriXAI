"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { adminFetch, ApiError } from "@/lib/api";
import type { ForumCommentOut } from "@/lib/types";

const BASE = "/admin/forum";

export async function createCommentAction(postId: number, formData: FormData) {
  const content = String(formData.get("content") ?? "").trim();
  if (!content) {
    redirect(`${BASE}?detail=${postId}&error=${encodeURIComponent("Nhập nội dung bình luận")}`);
  }

  try {
    await adminFetch<ForumCommentOut>(`/forum/posts/${postId}/comments`, {
      method: "POST",
      body: { content },
    });
  } catch (err) {
    const message = err instanceof ApiError ? err.message : "Không đăng được bình luận";
    redirect(`${BASE}?detail=${postId}&error=${encodeURIComponent(message)}`);
  }

  revalidatePath(BASE);
  redirect(`${BASE}?detail=${postId}`);
}

export async function deletePostAction(postId: number) {
  try {
    await adminFetch(`/forum/posts/${postId}`, { method: "DELETE" });
  } catch (err) {
    const message = err instanceof ApiError ? err.message : "Không xoá được bài viết";
    redirect(`${BASE}?detail=${postId}&error=${encodeURIComponent(message)}`);
  }

  revalidatePath(BASE);
  redirect(BASE);
}

export async function deleteCommentAction(commentId: number, postId: number) {
  try {
    await adminFetch(`/forum/comments/${commentId}`, { method: "DELETE" });
  } catch (err) {
    const message = err instanceof ApiError ? err.message : "Không xoá được bình luận";
    redirect(`${BASE}?detail=${postId}&error=${encodeURIComponent(message)}`);
  }

  revalidatePath(BASE);
  redirect(`${BASE}?detail=${postId}`);
}
