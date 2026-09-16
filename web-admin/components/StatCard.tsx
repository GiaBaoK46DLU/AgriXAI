import type { ReactNode } from "react";

export function StatCard({
  label,
  value,
  icon,
  accent,
}: {
  label: string;
  value: string | number;
  icon?: ReactNode;
  accent?: boolean;
}) {
  return (
    <div className="rounded-2xl border border-border bg-surface p-[18px] shadow-[0_4px_14px_rgba(46,111,64,0.06)]">
      <div className="mb-3 flex items-center justify-between">
        <div className="text-xs font-semibold text-ink/65">{label}</div>
        {icon && (
          <div
            className={`flex h-8 w-8 items-center justify-center rounded-lg ${
              accent ? "bg-severe/12 text-severe" : "bg-primary/12 text-primary-dark"
            }`}
          >
            {icon}
          </div>
        )}
      </div>
      <div className={`text-[28px] font-extrabold ${accent ? "text-severe" : "text-ink"}`}>{value}</div>
    </div>
  );
}
