import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Workflow } from "lucide-react";
import { DryRunPanel } from "./DryRunPanel";

export const dynamic = "force-dynamic";

export default async function PlaybooksPage() {
  const playbooks = await api.playbooks.list().catch(() => []);

  return (
    <div className="p-6 space-y-4">
      <div>
        <h1 className="text-lg font-semibold flex items-center gap-2">
          <Workflow className="h-4 w-4 text-primary" />
          Playbooks
        </h1>
        <p className="text-xs text-muted-foreground">
          Automated response definitions evaluated by Module 3 against every
          enriched alert. Use Dry Run to preview a playbook against a sample
          alert before flipping anything destructive.
        </p>
      </div>

      <div className="grid gap-3 md:grid-cols-2">
        {playbooks.map((pb) => (
          <Card key={pb.name} className="bg-card border-border">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm flex items-center justify-between gap-2">
                <span className="font-mono">{pb.name}</span>
                <span
                  className={`rounded px-2 py-0.5 text-[10px] border ${
                    pb.enabled
                      ? "bg-emerald-500/15 text-emerald-300 border-emerald-500/40"
                      : "bg-secondary text-muted-foreground border-border"
                  }`}
                >
                  {pb.enabled ? "enabled" : "disabled"}
                </span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-xs pt-0">
              <p className="text-muted-foreground">{pb.description || <i>No description.</i>}</p>
              <div className="flex flex-wrap gap-1.5">
                {pb.action_types.map((a, i) => (
                  <span
                    key={`${a}-${i}`}
                    className="rounded border border-border bg-secondary px-2 py-0.5 text-[10px] font-mono"
                  >
                    {a}
                  </span>
                ))}
              </div>
              <div className="flex justify-between text-[11px] text-muted-foreground font-mono pt-1">
                <span>match: {pb.match}</span>
                <span>priority: {pb.priority}</span>
                <span>conditions: {pb.conditions.length}</span>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <DryRunPanel />
    </div>
  );
}
