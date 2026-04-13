import { api } from "@/lib/api";
import { SeverityBadge } from "@/components/SeverityBadge";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

export const dynamic = "force-dynamic";

export default async function RulesPage() {
  const data = await api.rules.list().catch(() => null);

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-semibold">Detection Rules</h1>
        {data && (
          <span className="text-xs text-muted-foreground">{data.total} rules</span>
        )}
      </div>

      <div className="rounded-lg border border-border overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow className="border-border hover:bg-transparent">
              <TableHead className="text-xs">Name</TableHead>
              <TableHead className="text-xs w-20">Type</TableHead>
              <TableHead className="text-xs w-24">Severity</TableHead>
              <TableHead className="text-xs w-20">Status</TableHead>
              <TableHead className="text-xs">MITRE</TableHead>
              <TableHead className="text-xs w-44">Created</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data?.items.length ? (
              data.items.map((rule) => (
                <TableRow key={rule.id} className="border-border hover:bg-accent/50">
                  <TableCell className="py-2.5">
                    <p className="text-xs font-medium">{rule.name}</p>
                    {rule.description && (
                      <p className="text-[11px] text-muted-foreground mt-0.5 line-clamp-1">
                        {rule.description}
                      </p>
                    )}
                  </TableCell>
                  <TableCell className="py-2.5">
                    <span className="text-[10px] font-mono text-muted-foreground uppercase">
                      {rule.rule_type}
                    </span>
                  </TableCell>
                  <TableCell className="py-2.5">
                    {rule.severity ? (
                      <SeverityBadge severity={rule.severity} />
                    ) : (
                      <span className="text-xs text-muted-foreground">—</span>
                    )}
                  </TableCell>
                  <TableCell className="py-2.5">
                    <Badge
                      variant="outline"
                      className={
                        rule.enabled
                          ? "bg-green-500/15 text-green-400 border-green-500/30 text-[10px]"
                          : "bg-zinc-500/15 text-zinc-400 border-zinc-500/30 text-[10px]"
                      }
                    >
                      {rule.enabled ? "Enabled" : "Disabled"}
                    </Badge>
                  </TableCell>
                  <TableCell className="py-2.5">
                    {rule.mitre_techniques?.length ? (
                      <div className="flex flex-wrap gap-1">
                        {rule.mitre_techniques.map((t) => (
                          <span
                            key={t}
                            className="text-[10px] font-mono text-primary bg-primary/10 rounded px-1"
                          >
                            {t}
                          </span>
                        ))}
                      </div>
                    ) : (
                      <span className="text-xs text-muted-foreground">—</span>
                    )}
                  </TableCell>
                  <TableCell className="py-2.5 text-xs text-muted-foreground font-mono">
                    {new Date(rule.created_at).toLocaleDateString()}
                  </TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={6} className="text-center text-xs text-muted-foreground py-8">
                  No rules configured.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
