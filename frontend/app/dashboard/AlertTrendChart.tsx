"use client";

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

interface TrendPoint {
  hour: string;
  count: number;
}

export function AlertTrendChart({ data }: { data: TrendPoint[] }) {
  const formatted = data.map((d) => ({
    label: new Date(d.hour).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    count: d.count,
  }));

  return (
    <ResponsiveContainer width="100%" height={180}>
      <AreaChart data={formatted} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
        <defs>
          <linearGradient id="alertGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="oklch(0.70 0.18 200)" stopOpacity={0.3} />
            <stop offset="95%" stopColor="oklch(0.70 0.18 200)" stopOpacity={0} />
          </linearGradient>
        </defs>
        <XAxis
          dataKey="label"
          tick={{ fontSize: 10, fill: "oklch(0.55 0.02 250)" }}
          tickLine={false}
          axisLine={false}
          interval="preserveStartEnd"
        />
        <YAxis
          tick={{ fontSize: 10, fill: "oklch(0.55 0.02 250)" }}
          tickLine={false}
          axisLine={false}
          allowDecimals={false}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: "oklch(0.14 0.02 250)",
            border: "1px solid oklch(1 0 0 / 8%)",
            borderRadius: 6,
            fontSize: 11,
          }}
          labelStyle={{ color: "oklch(0.92 0.01 250)" }}
          itemStyle={{ color: "oklch(0.70 0.18 200)" }}
        />
        <Area
          type="monotone"
          dataKey="count"
          stroke="oklch(0.70 0.18 200)"
          strokeWidth={1.5}
          fill="url(#alertGrad)"
          dot={false}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
