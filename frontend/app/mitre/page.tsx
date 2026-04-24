import { api } from "@/lib/api";
import {
  MITRE_TACTICS,
  heatColor,
  techniqueName,
} from "@/lib/mitre";
import { Card, CardContent } from "@/components/ui/card";
import Link from "next/link";
import type { MitreTacticGroup } from "@/lib/types";

export const dynamic = "force-dynamic";

export default async function MitrePage() {
  const stats = await api.stats.mitre().catch(() => null);

  const byTactic: Record<string, MitreTacticGroup | undefined> = {};
  if (stats) for (const g of stats.tactics) byTactic[g.tactic] = g;

  // For coloring: use the max technique count across the whole matrix
  // so hot cells stay hot relative to the busiest tactic.
  const maxCount = stats
    ? Math.max(
        1,
        ...stats.tactics.flatMap((t) => t.techniques.map((x) => x.count)),
      )
    : 1;

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-baseline justify-between flex-wrap gap-2">
        <div>
          <h1 className="text-lg font-semibold">MITRE ATT&amp;CK Coverage</h1>
          <p className="text-xs text-muted-foreground">
            Techniques observed across alerts, grouped by kill-chain tactic.
          </p>
        </div>
        {stats && (
          <div className="flex gap-3 text-xs">
            <span className="rounded-md border border-border px-2.5 py-1">
              <span className="text-muted-foreground">Mapped</span>{" "}
              <span className="font-mono font-semibold text-primary">
                {stats.total_mapped}
              </span>
            </span>
            <span className="rounded-md border border-border px-2.5 py-1">
              <span className="text-muted-foreground">Unmapped</span>{" "}
              <span className="font-mono font-semibold text-muted-foreground">
                {stats.total_unmapped}
              </span>
            </span>
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="flex items-center gap-2 text-[11px] text-muted-foreground">
        <span>Heat:</span>
        <span className="rounded px-2 py-0.5 bg-muted/30">0</span>
        <span className="rounded px-2 py-0.5 bg-primary/30">low</span>
        <span className="rounded px-2 py-0.5 bg-yellow-500/60 text-foreground">
          medium
        </span>
        <span className="rounded px-2 py-0.5 bg-orange-500/70 text-white">
          high
        </span>
        <span className="rounded px-2 py-0.5 bg-red-500/80 text-white">
          critical
        </span>
      </div>

      {/* Matrix: one column per tactic */}
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-7 gap-2">
        {MITRE_TACTICS.map((tactic) => {
          const g = byTactic[tactic];
          const total = g?.total ?? 0;
          return (
            <Card
              key={tactic}
              className="bg-card border-border flex flex-col min-h-[180px]"
            >
              <div className="border-b border-border px-2 py-1.5">
                <div className="text-[11px] font-semibold text-foreground leading-tight">
                  {tactic}
                </div>
                <div className="text-[10px] text-muted-foreground font-mono">
                  {total} alert{total === 1 ? "" : "s"}
                </div>
              </div>
              <CardContent className="p-1.5 space-y-1 flex-1">
                {g?.techniques.length ? (
                  g.techniques.map((t) => {
                    const id = t.subtechnique ?? t.technique;
                    return (
                      <Link
                        key={`${t.technique}-${t.subtechnique ?? ""}`}
                        href={`/alerts?technique=${id}`}
                        title={`${id} — ${techniqueName(t.technique)} (${t.count} alerts)`}
                        className={`block rounded px-1.5 py-1 text-[10px] font-mono leading-tight hover:ring-1 hover:ring-primary transition ${heatColor(
                          t.count,
                          maxCount,
                        )}`}
                      >
                        <div className="flex items-center justify-between gap-1">
                          <span className="truncate">{id}</span>
                          <span className="shrink-0 font-semibold">
                            {t.count}
                          </span>
                        </div>
                        <div className="truncate opacity-80 text-[9px]">
                          {techniqueName(t.technique)}
                        </div>
                      </Link>
                    );
                  })
                ) : (
                  <div className="text-[10px] text-muted-foreground/60 italic py-1 text-center">
                    none
                  </div>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>

      {stats && stats.total_mapped === 0 && (
        <Card className="bg-card border-border">
          <CardContent className="p-6 text-center text-sm text-muted-foreground">
            No MITRE-tagged alerts yet. Ensure Wazuh rules include{" "}
            <code className="font-mono text-xs">&lt;mitre&gt;</code> tags —
            alerts ingested from those rules will populate this view.
          </CardContent>
        </Card>
      )}
    </div>
  );
}
