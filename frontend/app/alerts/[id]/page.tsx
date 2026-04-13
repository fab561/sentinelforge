import { api } from "@/lib/api";
import { SeverityBadge } from "@/components/SeverityBadge";
import { StatusBadge } from "@/components/StatusBadge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { notFound } from "next/navigation";
import Link from "next/link";
import { ChevronLeft } from "lucide-react";

export const dynamic = "force-dynamic";

export default async function AlertDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const alert = await api.alerts.get(id).catch(() => null);
  if (!alert) notFound();

  return (
    <div className="p-6 space-y-4 max-w-4xl">
      <Link
        href="/alerts"
        className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
      >
        <ChevronLeft className="h-3 w-3" /> Back to Alerts
      </Link>

      {/* Header */}
      <div className="space-y-1">
        <div className="flex items-start gap-3 flex-wrap">
          <h1 className="text-base font-semibold">{alert.title}</h1>
          <SeverityBadge severity={alert.severity} />
          <StatusBadge status={alert.status} />
          {alert.verdict && <StatusBadge status={alert.verdict} />}
        </div>
        <p className="text-xs text-muted-foreground font-mono">{alert.alert_id}</p>
        {alert.description && (
          <p className="text-sm text-muted-foreground pt-1">{alert.description}</p>
        )}
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        {/* Metadata */}
        <Card className="bg-card border-border">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Details</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-xs">
            <KV label="Time" value={new Date(alert.timestamp).toLocaleString()} />
            <KV label="Source" value={alert.source} />
            {alert.source_rule_id && <KV label="Rule ID" value={alert.source_rule_id} />}
            {alert.category && <KV label="Category" value={alert.category} />}
            {alert.threat_score !== null && (
              <KV label="Threat Score" value={String(alert.threat_score)} />
            )}
            {alert.case_id && (
              <KV
                label="Case"
                value={
                  <Link href={`/cases/${alert.case_id}`} className="text-primary hover:underline">
                    {alert.case_id}
                  </Link>
                }
              />
            )}
          </CardContent>
        </Card>

        {/* MITRE ATT&CK */}
        {alert.mitre && (alert.mitre.tactic || alert.mitre.technique) && (
          <Card className="bg-card border-border">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">MITRE ATT&CK</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-xs">
              {alert.mitre.tactic && <KV label="Tactic" value={alert.mitre.tactic} />}
              {alert.mitre.technique && <KV label="Technique" value={alert.mitre.technique} />}
              {alert.mitre.subtechnique && (
                <KV label="Sub-technique" value={alert.mitre.subtechnique} />
              )}
            </CardContent>
          </Card>
        )}

        {/* Observables */}
        {Object.keys(alert.observables ?? {}).length > 0 && (
          <Card className="bg-card border-border">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Observables</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-xs">
              {Object.entries(alert.observables).map(([k, v]) =>
                v ? <KV key={k} label={k.replace(/_/g, " ")} value={String(v)} /> : null
              )}
            </CardContent>
          </Card>
        )}

        {/* Enrichment */}
        {alert.enrichment && Object.keys(alert.enrichment).length > 0 && (
          <Card className="bg-card border-border">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Enrichment (M2)</CardTitle>
            </CardHeader>
            <CardContent className="text-xs">
              <pre className="text-muted-foreground overflow-auto max-h-48 text-[11px] font-mono whitespace-pre-wrap">
                {JSON.stringify(alert.enrichment, null, 2)}
              </pre>
            </CardContent>
          </Card>
        )}

        {/* Playbook actions */}
        {alert.playbook_actions?.length > 0 && (
          <Card className="bg-card border-border">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Playbook Actions (M3)</CardTitle>
            </CardHeader>
            <CardContent className="text-xs">
              <pre className="text-muted-foreground overflow-auto max-h-48 text-[11px] font-mono whitespace-pre-wrap">
                {JSON.stringify(alert.playbook_actions, null, 2)}
              </pre>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Raw log */}
      {alert.raw_log && (
        <Card className="bg-card border-border">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Raw Log</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="text-[11px] font-mono text-muted-foreground overflow-auto max-h-64 whitespace-pre-wrap">
              {alert.raw_log}
            </pre>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function KV({
  label,
  value,
}: {
  label: string;
  value: React.ReactNode;
}) {
  return (
    <div className="flex gap-2">
      <span className="text-muted-foreground capitalize w-28 shrink-0">{label}</span>
      <span className="font-mono text-foreground break-all">{value}</span>
    </div>
  );
}
