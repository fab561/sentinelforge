import { api } from "@/lib/api";
import { SeverityBadge } from "@/components/SeverityBadge";
import { StatusBadge } from "@/components/StatusBadge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import Link from "next/link";

export const dynamic = "force-dynamic";

export default async function AlertsPage({
  searchParams,
}: {
  searchParams: Promise<{ page?: string; severity?: string; status?: string }>;
}) {
  const sp = await searchParams;
  const page = Number(sp.page ?? 1);
  const severity = sp.severity;
  const status = sp.status;

  const data = await api.alerts
    .list({ page, page_size: 25, ...(severity && { severity }), ...(status && { status }) })
    .catch(() => null);

  const totalPages = data ? Math.ceil(data.total / 25) : 1;

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-semibold">Alerts</h1>
        {data && (
          <span className="text-xs text-muted-foreground">{data.total} total</span>
        )}
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-2">
        <FilterLink label="All" href="/alerts" active={!severity && !status} />
        <FilterLink label="Critical" href="/alerts?severity=critical" active={severity === "critical"} />
        <FilterLink label="High" href="/alerts?severity=high" active={severity === "high"} />
        <FilterLink label="Medium" href="/alerts?severity=medium" active={severity === "medium"} />
        <FilterLink label="Low" href="/alerts?severity=low" active={severity === "low"} />
        <span className="w-px bg-border mx-1" />
        <FilterLink label="New" href="/alerts?status=new" active={status === "new"} />
        <FilterLink label="In Progress" href="/alerts?status=in_progress" active={status === "in_progress"} />
        <FilterLink label="Resolved" href="/alerts?status=resolved" active={status === "resolved"} />
      </div>

      <div className="rounded-lg border border-border overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow className="border-border hover:bg-transparent">
              <TableHead className="text-xs w-48">Time</TableHead>
              <TableHead className="text-xs">Title</TableHead>
              <TableHead className="text-xs w-24">Severity</TableHead>
              <TableHead className="text-xs w-28">Status</TableHead>
              <TableHead className="text-xs w-28">Verdict</TableHead>
              <TableHead className="text-xs w-16 text-right">Score</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data?.items.length ? (
              data.items.map((alert) => (
                <TableRow
                  key={alert.id}
                  className="border-border hover:bg-accent/50 cursor-pointer"
                >
                  <TableCell className="text-xs text-muted-foreground py-2.5 font-mono">
                    {new Date(alert.timestamp).toLocaleString()}
                  </TableCell>
                  <TableCell className="py-2.5">
                    <Link
                      href={`/alerts/${alert.alert_id}`}
                      className="text-xs font-medium hover:text-primary hover:underline"
                    >
                      {alert.title}
                    </Link>
                    {alert.category && (
                      <span className="ml-2 text-[10px] text-muted-foreground">
                        {alert.category}
                      </span>
                    )}
                  </TableCell>
                  <TableCell className="py-2.5">
                    <SeverityBadge severity={alert.severity} />
                  </TableCell>
                  <TableCell className="py-2.5">
                    <StatusBadge status={alert.status} />
                  </TableCell>
                  <TableCell className="py-2.5">
                    {alert.verdict ? (
                      <StatusBadge status={alert.verdict} />
                    ) : (
                      <span className="text-[11px] text-muted-foreground">—</span>
                    )}
                  </TableCell>
                  <TableCell className="py-2.5 text-right text-xs font-mono">
                    {alert.threat_score ?? "—"}
                  </TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={6} className="text-center text-xs text-muted-foreground py-8">
                  No alerts found.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex gap-1 justify-end">
          {Array.from({ length: totalPages }, (_, i) => i + 1).map((p) => (
            <Link
              key={p}
              href={`/alerts?page=${p}${severity ? `&severity=${severity}` : ""}${status ? `&status=${status}` : ""}`}
              className={`px-2.5 py-1 rounded text-xs border ${
                p === page
                  ? "bg-primary text-primary-foreground border-primary"
                  : "border-border hover:bg-accent"
              }`}
            >
              {p}
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

function FilterLink({
  label,
  href,
  active,
}: {
  label: string;
  href: string;
  active: boolean;
}) {
  return (
    <Link
      href={href}
      className={`rounded-md px-2.5 py-1 text-xs border transition-colors ${
        active
          ? "bg-primary/15 text-primary border-primary/30"
          : "border-border text-muted-foreground hover:bg-accent hover:text-foreground"
      }`}
    >
      {label}
    </Link>
  );
}
