"use client";

import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import type { DiseaseCount } from "@/lib/types";

const BAR_COLORS = ["#2E6F40", "#3F8253", "#54A96A", "#7FC191", "#A9D6B6", "#C3D24A"];

function TooltipContent({
  active,
  payload,
}: {
  active?: boolean;
  payload?: { value: number; payload: DiseaseCount }[];
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

export function DiseaseBarChart({ data }: { data: DiseaseCount[] }) {
  const top = [...data].sort((a, b) => b.count - a.count).slice(0, 7);

  return (
    <ResponsiveContainer width="100%" height={Math.max(180, top.length * 34)}>
      <BarChart data={top} layout="vertical" margin={{ top: 0, right: 20, bottom: 0, left: 0 }}>
        <CartesianGrid stroke="#E3EAE0" strokeDasharray="3 3" horizontal={false} />
        <XAxis type="number" allowDecimals={false} tick={{ fontSize: 11, fill: "#12301D99" }} axisLine={false} tickLine={false} />
        <YAxis
          type="category"
          dataKey="name_vi"
          width={130}
          tick={{ fontSize: 12, fill: "#12301D" }}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip content={<TooltipContent />} cursor={{ fill: "#F7F9F6" }} />
        <Bar dataKey="count" radius={[0, 6, 6, 0]} maxBarSize={18}>
          {top.map((row, i) => (
            <Cell key={row.disease_key} fill={BAR_COLORS[i % BAR_COLORS.length]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
