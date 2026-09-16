"use client";

import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

import type { SeverityCount } from "@/lib/types";

const SEVERITY_COLORS: Record<string, string> = {
  severe: "#C24A12",
  moderate: "#7A4F00",
  mild: "#2E6F40",
  none: "#A9BBAE",
};

function TooltipContent({
  active,
  payload,
}: {
  active?: boolean;
  payload?: { payload: SeverityCount }[];
}) {
  if (!active || !payload?.length) return null;
  const row = payload[0]!.payload;
  return (
    <div className="rounded-xl border border-border bg-surface px-3 py-2 text-xs shadow-lg">
      <div className="font-bold text-ink">{row.name_vi}</div>
      <div className="text-ink/70">{row.count} ca</div>
    </div>
  );
}

export function SeverityDonutChart({ data }: { data: SeverityCount[] }) {
  const total = data.reduce((sum, row) => sum + row.count, 0);

  return (
    <div className="relative">
      <ResponsiveContainer width="100%" height={220}>
        <PieChart>
          <Pie
            data={data}
            dataKey="count"
            nameKey="name_vi"
            innerRadius={58}
            outerRadius={80}
            paddingAngle={2}
            strokeWidth={0}
          >
            {data.map((row) => (
              <Cell key={row.severity} fill={SEVERITY_COLORS[row.severity] ?? "#A9BBAE"} />
            ))}
          </Pie>
          <Tooltip content={<TooltipContent />} />
          <Legend
            verticalAlign="bottom"
            iconType="circle"
            iconSize={8}
            wrapperStyle={{ fontSize: 12, color: "#12301D" }}
          />
        </PieChart>
      </ResponsiveContainer>
      <div className="pointer-events-none absolute left-1/2 top-[92px] -translate-x-1/2 -translate-y-1/2 text-center">
        <div className="text-2xl font-extrabold text-ink">{total}</div>
        <div className="text-[11px] font-semibold text-ink/60">tổng ca</div>
      </div>
    </div>
  );
}
