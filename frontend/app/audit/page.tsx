import { api } from "@/lib/api";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { ScrollText } from "lucide-react";
import Link from "next/link";

export const dynamic = "force-dynamic";

// Tag actions by domain so the table is scannable at a glance.
function actionTone(action: string): string {
  if (action.startsWith("case.alert.correlated")) return "bg-cyan-500/15 text-cyan-300 border-cyan-500/40";
  if (action.startsWith("case.status.")) return "bg-primary/15 text-primary border-primary/40";
  if (action.startsWith("case.")) return "bg-violet-500/15 text-violet-300 border-violet-500/40";
  if (action.startsWith("evidence.uploaded")) return "bg-emerald-500/15 text-emerald-300 border-emerald-500/40";
  if (action.startsWith("evidence.deleted")) return "bg-red-500/15 text-red-300 border-red-500/40";
  return "bg-secondary text-muted-foreground border-border";
}

function entityLink(entity_type: string | null, entity_id: string | null): React.ReactNode {
  if (!entity_id) return <span className="text-muted-foreground">—</span>;
  const short = entity_id.slice(0, 8);
  if (entity_type === "case") {
    return (
      <Link href={`/cases/${entity_id}`} className="text-primary hover:underline font-mono text-[11px]">
        {short}…
      </Link>
    );
  }
  return <span className="font-mono text-[11px]">{short}…</span>;
}

export default async function AuditPage({
  searchParams,
}: {
  searchParams: Promise<{ action?: string; entity_type?: string }>;
}) {
  const sp = await searchParams;
  const data = await api.audit
    .list({
      limit: 200,
      ...(sp.action && { action: sp.action }),
      ...(sp.entity_type && { entity_type: sp.entity_type }),
    })
    .catch(() => null);

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div>
          <h1 className="text-lg font-semibold flex items-center gap-2">
            <ScrollText className="h-4 w-4 text-primary" />
            Audit Log
          </h1>
          <p className="text-xs text-muted-foreground">
            Tamper-evident trail of mutations on cases and evidence.
          </p>
        </div>
        {data && (
          <span className="text-xs text-muted-foreground">{data.total} entries</span>
        )}
      </div>

      {/* Quick filter chips — entity_type filter is the most useful drill-down. */}
      <div className="flex flex-wrap gap-2">
        <FilterLink label="All" href="/audit" active={!sp.entity_type} />
        <FilterLink label="Cases" href="/audit?entity_type=case" active={sp.entity_type === "case"} />
        <span className="w-px bg-border mx-1" />
        <FilterLink label="Status changes" href="/audit?action=case.status.investigating" active={sp.action?.startsWith("case.status.")} />
        <FilterLink label="Correlations" href="/audit?action=case.alert.correlated" active={sp.action === "case.alert.correlated"} />
        <FilterLink label="Evidence uploads" href="/audit?action=evidence.uploaded" active={sp.action === "evidence.uploaded"} />
      </div>

      <Card className="bg-card border-border">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">Recent activity</CardTitle>
        </CardHeader>
        <CardContent className="pt-0">
          <div className="rounded-lg border border-border overflow-hidden">
            <Table>
              <TableHeader>
                <TableRow className="border-border hover:bg-transparent">
                  <TableHead className="text-xs w-44">Time</TableHead>
                  <TableHead className="text-xs w-56">Action</TableHead>
                  <TableHead className="text-xs w-24">Entity</TableHead>
                  <TableHead className="text-xs w-28">ID</TableHead>
                  <TableHead className="text-xs">Details</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data?.items.length ? (
                  data.items.map((row) => (
                    <TableRow key={row.id} className="border-border">
                      <TableCell className="text-xs text-muted-foreground py-2 font-mono">
                        {new Date(row.created_at).toLocaleString()}
                      </TableCell>
                      <TableCell className="py-2">
                        <span
                          className={`inline-block rounded border px-2 py-0.5 text-[10px] font-mono ${actionTone(row.action)}`}
                        >
                          {row.action}
                        </span>
                      </TableCell>
                      <TableCell className="py-2 text-xs text-muted-foreground capitalize">
                        {row.entity_type ?? "—"}
                      </TableCell>
                      <TableCell className="py-2">
                        {entityLink(row.entity_type, row.entity_id)}
                      </TableCell>
                      <TableCell className="py-2 text-[11px] font-mono text-muted-foreground truncate max-w-md">
                        {row.details ? JSON.stringify(row.details) : "—"}
                      </TableCell>
                    </TableRow>
                  ))
                ) : (
                  <TableRow>
                    <TableCell colSpan={5} className="text-center text-xs text-muted-foreground py-8">
                      No audit entries match these filters.
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
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
  active: boolean | undefined;
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
