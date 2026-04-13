import { api } from "@/lib/api";
import { StatusBadge } from "@/components/StatusBadge";
import { Card, CardContent } from "@/components/ui/card";
import { Cpu } from "lucide-react";

export const dynamic = "force-dynamic";

export default async function AgentsPage() {
  const data = await api.wazuh.agents().catch(() => null);

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-semibold">Wazuh Agents</h1>
        {data && (
          <span className="text-xs text-muted-foreground">{data.total} agents</span>
        )}
      </div>

      {!data && (
        <div className="rounded-lg border border-border p-8 text-center">
          <p className="text-sm text-muted-foreground">
            Wazuh Manager unreachable. Start the stack with{" "}
            <code className="text-xs font-mono bg-secondary px-1 rounded">
              docker compose up -d
            </code>
          </p>
        </div>
      )}

      {data?.agents?.length === 0 && (
        <p className="text-xs text-muted-foreground">No agents connected yet.</p>
      )}

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {data?.agents?.map((agent) => (
          <Card key={agent.id} className="bg-card border-border">
            <CardContent className="pt-4 pb-4 space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Cpu className="h-4 w-4 text-primary shrink-0" />
                  <span className="text-sm font-medium">{agent.name}</span>
                </div>
                <StatusBadge status={agent.status} />
              </div>
              <div className="space-y-1 text-xs text-muted-foreground">
                <p>
                  <span className="text-foreground/50">ID:</span>{" "}
                  <span className="font-mono">{agent.id}</span>
                </p>
                <p>
                  <span className="text-foreground/50">IP:</span>{" "}
                  <span className="font-mono">{agent.ip}</span>
                </p>
                {agent.os?.name && (
                  <p>
                    <span className="text-foreground/50">OS:</span> {agent.os.name}
                  </p>
                )}
                {agent.version && (
                  <p>
                    <span className="text-foreground/50">Version:</span> {agent.version}
                  </p>
                )}
                {agent.lastKeepAlive && (
                  <p>
                    <span className="text-foreground/50">Last seen:</span>{" "}
                    {new Date(agent.lastKeepAlive).toLocaleString()}
                  </p>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
