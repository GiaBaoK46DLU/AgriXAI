import type { ReactNode } from "react";

// Mỗi cặp nền/chữ dưới đây đã tính tỉ lệ tương phản (WCAG) trước khi chọn —
// bản trước dùng nền pastel quá nhạt cho "moderate"/"neutral" khiến chip gần
// như biến mất trên nền trắng/canvas (~2.9:1, dưới cả ngưỡng AA-large 3:1).
// "severe"/"moderate" đổi sang nền đặc màu + chữ trắng (giống cách mobile tô
// nhãn "Nặng" — xem AgriColors.severeBg/severeFg) vì đây là hai mức cảnh báo
// quan trọng nhất, cần nổi bật chắc chắn chứ không chỉ tô màu nhẹ cho có.
const TONE_CLASSES = {
  primary: "bg-primary/12 text-primary-dark",
  accent: "bg-accent/16 text-accent-ink",
  severe: "bg-severe text-white",
  moderate: "bg-accent-ink text-white",
  mild: "bg-mild-bg text-mild",
  neutral: "bg-ink/10 text-ink/75",
} as const;

export type TagTone = keyof typeof TONE_CLASSES;

export function Tag({ tone, children }: { tone: TagTone; children: ReactNode }) {
  return (
    <span className={`inline-block whitespace-nowrap rounded-full px-2.5 py-1 text-xs font-bold ${TONE_CLASSES[tone]}`}>
      {children}
    </span>
  );
}

export function severityTone(severity: string): TagTone {
  switch (severity) {
    case "severe":
      return "severe";
    case "moderate":
      return "moderate";
    case "mild":
      return "mild";
    default:
      return "neutral";
  }
}

export function roleTone(role: string): TagTone {
  return role === "admin" ? "accent" : "primary";
}

export function statusTone(active: boolean): TagTone {
  return active ? "primary" : "severe";
}

export function plotStatusTone(status: string): TagTone {
  switch (status) {
    case "active":
      return "primary";
    case "fallow":
      return "moderate";
    default:
      return "neutral";
  }
}
