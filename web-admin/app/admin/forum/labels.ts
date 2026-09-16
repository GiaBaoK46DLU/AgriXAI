import type { TagTone } from "@/components/Tag";
import type { ForumPostType } from "@/lib/types";

export const TYPE_LABEL: Record<ForumPostType, string> = {
  agree: "Đồng ý với kết quả",
  disagree: "Nghĩ là bệnh khác",
  medicine_issue: "Thuốc gợi ý không phù hợp",
  tip: "Kinh nghiệm xử lý khác",
};

export const TYPE_TONE: Record<ForumPostType, TagTone> = {
  agree: "primary",
  disagree: "moderate",
  medicine_issue: "severe",
  tip: "accent",
};

export function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString("vi-VN", { dateStyle: "short", timeStyle: "short" });
}
