"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import type { MttrTrendPoint } from "@/lib/types";

// Seconds → compact "8m", "1.5h", "2.1d" so axis labels stay tight.
function fmtDuration(seconds: number | null): string {
  if (seconds === null) return "—";
  if (seconds < 60) return `${Math.round(seconds)}s`;
  if (seconds < 3600) return `${Math.round(seconds / 60)}m`;
  if (seconds < 86400) return `${(seconds / 3600).toFixed(1)}h`;
  return `${(seconds / 86400).toFixed(1)}d`;
}

export function MttrTrendChart({ data }: { data: MttrTrendPoint[] }) {
  // Convert seconds → minutes so both MTTA and MTTR plot on the same axis;
  // at SOC timescales raw seconds make the scale unreadable.
  const formatted = data.map((d) => ({
    label: new Date(d.day).toLocaleDateString([], {
      month: "short",
      day: "numeric",
    }),
    mtta: d.mtta_median_seconds !== null ? d.mtta_median_seconds / 60 : null,
    mttr: d.mttr_median_seconds !== null ? d.mttr_median_seconds / 60 : null,
    rawMtta: d.mtta_median_seconds,
    rawMttr: d.mttr_median_seconds,
  }));

  return (
    <ResponsiveContainer width="100%" height={180}>
      <LineChart data={formatted} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
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
          tickFormatter={(v: number) => (v >= 60 ? `${(v / 60).toFixed(1)}h` : `${v}m`)}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: "oklch(0.14 0.02 250)",
            border: "1px solid oklch(1 0 0 / 8%)",
            borderRadius: 6,
            fontSize: 11,
          }}
          labelStyle={{ color: "oklch(0.92 0.01 250)" }}
          formatter={(_value, name, entry) => {
            const payload = (entry as { payload?: { rawMtta: number | null; rawMttr: number | null } })?.payload;
            const raw = name === "MTTA" ? payload?.rawMtta : payload?.rawMttr;
            return [fmtDuration(raw ?? null), name as string];
          }}
        />
        <Legend
          wrapperStyle={{ fontSize: 11, paddingTop: 4 }}
          iconType="line"
          iconSize={10}
        />
        <Line
          type="monotone"
          dataKey="mtta"
          name="MTTA"
          stroke="oklch(0.70 0.18 200)"
          strokeWidth={1.5}
          dot={{ r: 2 }}
          connectNulls
        />
        <Line
          type="monotone"
          dataKey="mttr"
          name="MTTR"
          stroke="oklch(0.65 0.22 30)"
          strokeWidth={1.5}
          dot={{ r: 2 }}
          connectNulls
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
