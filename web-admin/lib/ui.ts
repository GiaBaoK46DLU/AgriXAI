// Chuỗi class Tailwind dùng lặp lại nhiều nơi — gom một chỗ để các trang
// module không phải lặp lại cả một dòng class dài mỗi lần viết input/nút.

export const input =
  "w-full rounded-[10px] border border-border bg-surface px-3.5 py-2.5 text-[13px] text-ink " +
  "outline-none placeholder:text-ink/40 focus:border-primary";

export const select = input;

export const label = "mb-1.5 block text-xs font-semibold text-ink";

export const btnPrimary =
  "rounded-full bg-primary px-[18px] py-2.5 text-[13px] font-bold text-white transition hover:bg-primary-dark " +
  "disabled:cursor-not-allowed disabled:opacity-60";

export const btnGhost =
  "rounded-full border border-border bg-surface px-4 py-2.5 text-[13px] font-bold text-ink transition hover:bg-canvas";

export const btnDanger =
  "rounded-full border border-severe/30 bg-severe-bg px-4 py-2.5 text-[13px] font-bold text-severe transition hover:bg-severe/15";

export const card = "rounded-[20px] border border-border bg-surface";

export const th =
  "px-4 py-3 text-left text-[11px] font-bold uppercase tracking-wide text-ink/55";

export const td = "px-4 py-3 text-[13px] text-ink";

export const tr = "border-t border-border";
