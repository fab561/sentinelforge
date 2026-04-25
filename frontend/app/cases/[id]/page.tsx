import { api } from "@/lib/api";
import { SeverityBadge } from "@/components/SeverityBadge";
import { StatusBadge } from "@/components/StatusBadge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EvidencePanel } from "@/components/EvidencePanel";
import { notFound } from "next/navigation";
import Link from "next/link";
import { ChevronLeft, Layers } from "lucide-react";

export const dynamic = "force-dynamic";

export default async function CaseDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const [c, alerts] = await Promise.all([
    api.cases.get(id).catch(() => null),
    api.cases.alerts(id).catch(() => [] as Awaited<ReturnType<typeof api.cases.alerts>>),
  ]);
  if (!c) notFound();

  return (
    <div className="p-6 space-y-4 max-w-3xl">
      <Link
        href="/cases"
        className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
      >
        <ChevronLeft className="h-3 w-3" /> Back to Cases
      </Link>

      <div className="space-y-1">
        <div className="flex items-start gap-3 flex-wrap">
          <h1 className="text-base font-semibold">{c.title}</h1>
          {c.severity && <SeverityBadge severity={c.severity} />}
          <StatusBadge status={c.status} />
        </div>
        <p className="text-xs text-muted-foreground font-mono">{c.case_number}</p>
        {c.description && (
          <p className="text-sm text-muted-foreground pt-1">{c.description}</p>
        )}
      </div>

      <Card className="bg-card border-border">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">Case Details</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-xs">
          <KV label="Status" value={<StatusBadge status={c.status} />} />
          {c.severity && <KV label="Severity" value={<SeverityBadge severity={c.severity} />} />}
          <KV label="Created" value={new Date(c.created_at).toLocaleString()} />
          <KV label="Updated" value={new Date(c.updated_at).toLocaleString()} />
          {c.assigned_to && <KV label="Assigned To" value={c.assigned_to} />}
        </CardContent>
      </Card>

      <Card className="bg-card border-border">
        <CardHeader className="pb-2 flex flex-row items-center justify-between">
          <CardTitle className="text-sm flex items-center gap-2">
            <Layers className="h-4 w-4 text-primary" />
            Correlated Alerts ({alerts.length})
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-1.5 pt-0">
          {alerts.length === 0 ? (
            <p className="text-xs text-muted-foreground py-2">
              No alerts attached to this case yet.
            </p>
          ) : (
            alerts.map((a) => (
              <Link
                key={a.id}
                href={`/alerts/${a.alert_id}`}
                className="flex items-center gap-2 rounded-md border border-border px-2.5 py-2 text-xs hover:bg-accent"
              >
                <span className="font-mono text-[11px] text-muted-foreground w-32 shrink-0">
                  {new Date(a.timestamp).toLocaleString()}
                </span>
                <span className="font-medium truncate flex-1">{a.title}</span>
                <SeverityBadge severity={a.severity} />
                {a.verdict && <StatusBadge status={a.verdict} />}
                <span className="text-[11px] font-mono text-muted-foreground">
                  {a.threat_score ?? "—"}
                </span>
              </Link>
            ))
          )}
        </CardContent>
      </Card>

      <EvidencePanel caseId={c.id} />
    </div>
  );
}

function KV({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex gap-2 items-center">
      <span className="text-muted-foreground capitalize w-28 shrink-0">{label}</span>
      <span className="font-mono text-foreground">{value}</span>
    </div>
  );
}
