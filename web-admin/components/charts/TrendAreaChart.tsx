"use client";

import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { TimeseriesPoint } from "@/lib/types";

function formatAxisDate(iso: string): string {
  const d = new Date(iso);
  return `${String(d.getDate()).padStart(2, "0")}/${String(d.getMonth() + 1).padStart(2, "0")}`;
}

function TooltipContent({
  active,
  payload,
}: {
  active?: boolean;
  payload?: { value: number; payload: TimeseriesPoint }[];
}) {
  if (!active || !payload?.length) return null;
  const point = payload[0]!.payload;
  return (
    <div className="rounded-xl border border-border bg-surface px-3 py-2 text-xs shadow-lg">
      <div className="font-bold text-ink">{formatAxisDate(point.day)}</div>
      <div className="text-ink/70">{point.count} lượt chẩn đoán</div>
    </div>
  );
}

export function TrendAreaChart({ data }: { data: TimeseriesPoint[] }) {
  return (
    <ResponsiveContainer width="100%" height={260}>
      <AreaChart data={data} margin={{ top: 8, right: 12, bottom: 0, left: -18 }}>
        <defs>
          <linearGradient id="trendFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#54A96A" stopOpacity={0.35} />
            <stop offset="100%" stopColor="#54A96A" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid stroke="#E3EAE0" strokeDasharray="3 3" vertical={false} />
        <XAxis
          dataKey="day"
          tickFormatter={formatAxisDate}
          tick={{ fontSize: 11, fill: "#12301D99" }}
          axisLine={{ stroke: "#E3EAE0" }}
          tickLine={false}
          minTickGap={24}
        />
        <YAxis
          allowDecimals={false}
          tick={{ fontSize: 11, fill: "#12301D99" }}
          axisLine={false}
          tickLine={false}
          width={28}
        />
        <Tooltip content={<TooltipContent />} />
        <Area
          type="monotone"
          dataKey="count"
          stroke="#2E6F40"
          strokeWidth={2.5}
          fill="url(#trendFill)"
          dot={false}
          activeDot={{ r: 4, fill: "#2E6F40" }}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
