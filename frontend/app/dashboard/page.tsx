import { api } from "@/lib/api";
import { SeverityBadge } from "@/components/SeverityBadge";
import { StatusBadge } from "@/components/StatusBadge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  AlertTriangle,
  FolderOpen,
  Cpu,
  TrendingUp,
  ShieldX,
  ShieldCheck,
  Clock,
} from "lucide-react";
import Link from "next/link";
import { AlertTrendChart } from "./AlertTrendChart";
import { MttrTrendChart } from "./MttrTrendChart";

export const dynamic = "force-dynamic";

// Seconds → compact "3m", "1.5h", "2.1d" for dashboard stat cards.
function fmtDuration(seconds: number | null | undefined): string {
  if (seconds === null || seconds === undefined) return "—";
  if (seconds < 60) return `${Math.round(seconds)}s`;
  if (seconds < 3600) return `${Math.round(seconds / 60)}m`;
  if (seconds < 86400) return `${(seconds / 3600).toFixed(1)}h`;
  return `${(seconds / 86400).toFixed(1)}d`;
}

export default async function DashboardPage() {
  const [stats, alertsRes, casesRes, mttr] = await Promise.all([
    api.stats.get().catch(() => null),
    api.alerts.list({ page: 1, page_size: 5 }).catch(() => null),
    api.cases.list({ page: 1, page_size: 5 }).catch(() => null),
    api.stats.mttr().catch(() => null),
  ]);

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-lg font-semibold text-foreground">Dashboard</h1>

      {/* Stat cards */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard
          label="Total Alerts"
          value={stats?.total_alerts ?? "—"}
          icon={<AlertTriangle className="h-4 w-4 text-yellow-400" />}
          sub={`${stats?.severity_breakdown.critical ?? 0} critical`}
          subColor="text-red-400"
        />
        <StatCard
          label="Active Cases"
          value={stats?.active_cases ?? "—"}
          icon={<FolderOpen className="h-4 w-4 text-cyan-400" />}
          sub="open incidents"
        />
        <StatCard
          label="Agents Online"
          value={stats?.total_agents ?? "—"}
          icon={<Cpu className="h-4 w-4 text-green-400" />}
          sub="Wazuh agents"
        />
        <StatCard
          label="Threat Score"
          value={`${stats?.verdict_breakdown.malicious ?? 0}`}
          icon={<ShieldX className="h-4 w-4 text-red-400" />}
          sub="malicious verdicts"
          subColor="text-red-400"
        />
      </div>

      {/* Severity breakdown */}
      {stats && (
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          {(["critical", "high", "medium", "low"] as const).map((s) => (
            <SeverityCard
              key={s}
              severity={s}
              count={stats.severity_breakdown[s]}
              total={stats.total_alerts}
            />
          ))}
        </div>
      )}

      {/* SLA row: MTTA + MTTR + trend. Three-up on wide, stacks on mobile. */}
      {mttr && (
        <div className="grid gap-4 lg:grid-cols-3">
          <StatCard
            label="MTTA (median)"
            value={fmtDuration(mttr.mtta_median_seconds)}
            icon={<Clock className="h-4 w-4 text-cyan-400" />}
            sub={`p95: ${fmtDuration(mttr.mtta_p95_seconds)}`}
          />
          <StatCard
            label="MTTR (median)"
            value={fmtDuration(mttr.mttr_median_seconds)}
            icon={<ShieldCheck className="h-4 w-4 text-primary" />}
            sub={`p95: ${fmtDuration(mttr.mttr_p95_seconds)}`}
          />
          <Card className="bg-card border-border">
            <CardHeader className="pb-1">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <TrendingUp className="h-4 w-4 text-primary" />
                SLA Trend — 14d
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-0">
              {mttr.trend.some(
                (p) => p.mtta_median_seconds !== null || p.mttr_median_seconds !== null,
              ) ? (
                <MttrTrendChart data={mttr.trend} />
              ) : (
                <p className="text-[11px] text-muted-foreground py-8 text-center">
                  No resolved cases yet — trend appears once analysts start closing cases.
                </p>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* Trend chart + verdict breakdown */}
      <div className="grid gap-4 lg:grid-cols-3">
        {stats?.alerts_trend_24h && (
          <Card className="lg:col-span-2 bg-card border-border">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <TrendingUp className="h-4 w-4 text-primary" />
                Alerts — Last 24h
              </CardTitle>
            </CardHeader>
            <CardContent>
              <AlertTrendChart data={stats.alerts_trend_24h} />
            </CardContent>
          </Card>
        )}

        {stats && (
          <Card className="bg-card border-border">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <ShieldCheck className="h-4 w-4 text-primary" />
                Verdict Breakdown
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 pt-1">
              {(["malicious", "suspicious", "benign", "pending"] as const).map((v) => (
                <VerdictRow
                  key={v}
                  verdict={v}
                  count={stats.verdict_breakdown[v]}
                  total={stats.total_alerts}
                />
              ))}
            </CardContent>
          </Card>
        )}
      </div>

      {/* Recent alerts + recent cases */}
      <div className="grid gap-4 lg:grid-cols-2">
        <Card className="bg-card border-border">
          <CardHeader className="pb-2 flex flex-row items-center justify-between">
            <CardTitle className="text-sm font-medium">Recent Alerts</CardTitle>
            <Link href="/alerts" className="text-xs text-primary hover:underline">
              View all
            </Link>
          </CardHeader>
          <CardContent className="space-y-2 pt-0">
            {alertsRes?.items.length ? (
              alertsRes.items.map((a) => (
                <Link
                  key={a.id}
                  href={`/alerts/${a.alert_id}`}
                  className="flex items-start justify-between rounded-md px-2 py-2 hover:bg-accent transition-colors"
                >
                  <div className="space-y-0.5 min-w-0">
                    <p className="text-xs font-medium truncate pr-2">{a.title}</p>
                    <p className="text-[11px] text-muted-foreground">
                      {new Date(a.timestamp).toLocaleString()}
                    </p>
                  </div>
                  <SeverityBadge severity={a.severity} />
                </Link>
              ))
            ) : (
              <p className="text-xs text-muted-foreground py-2">No alerts yet.</p>
            )}
          </CardContent>
        </Card>

        <Card className="bg-card border-border">
          <CardHeader className="pb-2 flex flex-row items-center justify-between">
            <CardTitle className="text-sm font-medium">Recent Cases</CardTitle>
            <Link href="/cases" className="text-xs text-primary hover:underline">
              View all
            </Link>
          </CardHeader>
          <CardContent className="space-y-2 pt-0">
            {casesRes?.items.length ? (
              casesRes.items.map((c) => (
                <Link
                  key={c.id}
                  href={`/cases/${c.id}`}
                  className="flex items-start justify-between rounded-md px-2 py-2 hover:bg-accent transition-colors"
                >
                  <div className="space-y-0.5 min-w-0">
                    <p className="text-xs font-medium truncate pr-2">{c.title}</p>
                    <p className="text-[11px] text-muted-foreground">{c.case_number}</p>
                  </div>
                  <StatusBadge status={c.status} />
                </Link>
              ))
            ) : (
              <p className="text-xs text-muted-foreground py-2">No cases yet.</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Top categories */}
      {stats?.top_categories?.length ? (
        <Card className="bg-card border-border">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Clock className="h-4 w-4 text-primary" />
              Top Alert Categories
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {stats.top_categories.map(({ category, count }) => (
                <span
                  key={category}
                  className="rounded-md border border-border bg-secondary px-2.5 py-1 text-xs"
                >
                  {category}{" "}
                  <span className="text-muted-foreground">({count})</span>
                </span>
              ))}
            </div>
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}

function StatCard({
  label,
  value,
  icon,
  sub,
  subColor = "text-muted-foreground",
}: {
  label: string;
  value: string | number;
  icon: React.ReactNode;
  sub?: string;
  subColor?: string;
}) {
  return (
    <Card className="bg-card border-border">
      <CardContent className="pt-4 pb-4">
        <div className="flex items-center justify-between mb-1">
          <span className="text-xs text-muted-foreground">{label}</span>
          {icon}
        </div>
        <p className="text-2xl font-bold">{value}</p>
        {sub && <p className={`text-[11px] mt-0.5 ${subColor}`}>{sub}</p>}
      </CardContent>
    </Card>
  );
}

const severityColors: Record<string, string> = {
  critical: "bg-red-500",
  high: "bg-orange-500",
  medium: "bg-yellow-500",
  low: "bg-cyan-500",
};

function SeverityCard({
  severity,
  count,
  total,
}: {
  severity: string;
  count: number;
  total: number;
}) {
  const pct = total > 0 ? Math.round((count / total) * 100) : 0;
  return (
    <Card className="bg-card border-border">
      <CardContent className="pt-3 pb-3">
        <div className="flex justify-between items-center mb-2">
          <span className="capitalize text-xs text-muted-foreground">{severity}</span>
          <span className="text-sm font-semibold">{count}</span>
        </div>
        <div className="h-1.5 rounded-full bg-secondary overflow-hidden">
          <div
            className={`h-full rounded-full ${severityColors[severity] ?? "bg-primary"}`}
            style={{ width: `${pct}%` }}
          />
        </div>
        <p className="text-[10px] text-muted-foreground mt-1">{pct}% of total</p>
      </CardContent>
    </Card>
  );
}

const verdictColors: Record<string, string> = {
  malicious: "bg-red-500",
  suspicious: "bg-orange-500",
  benign: "bg-green-500",
  pending: "bg-zinc-500",
};

function VerdictRow({
  verdict,
  count,
  total,
}: {
  verdict: string;
  count: number;
  total: number;
}) {
  const pct = total > 0 ? Math.round((count / total) * 100) : 0;
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs">
        <span className="capitalize text-muted-foreground">{verdict}</span>
        <span className="font-medium">{count}</span>
      </div>
      <div className="h-1.5 rounded-full bg-secondary overflow-hidden">
        <div
          className={`h-full rounded-full ${verdictColors[verdict] ?? "bg-primary"}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
