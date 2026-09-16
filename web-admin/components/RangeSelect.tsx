"use client";

import { useRouter } from "next/navigation";

export function RangeSelect({ options, value }: { options: number[]; value: number }) {
  const router = useRouter();

  return (
    <select
      defaultValue={value}
      onChange={(e) => router.push(`?days=${e.target.value}`)}
      className="rounded-lg border border-border bg-canvas px-2.5 py-1.5 text-xs font-semibold text-ink"
    >
      {options.map((d) => (
        <option key={d} value={d}>
          {d} ngày
        </option>
      ))}
    </select>
  );
}
