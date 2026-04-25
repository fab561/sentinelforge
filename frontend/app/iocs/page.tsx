import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Eye } from "lucide-react";
import { IOCTable } from "./IOCTable";

export const dynamic = "force-dynamic";

export default async function IOCsPage() {
  const data = await api.iocs.list({ page_size: 200 }).catch(() => null);

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div>
          <h1 className="text-lg font-semibold flex items-center gap-2">
            <Eye className="h-4 w-4 text-primary" />
            IOC Watchlist
          </h1>
          <p className="text-xs text-muted-foreground">
            Analyst-curated indicators. Every alert observable is checked against
            this list during enrichment — matches inject a watchlist provider
            result so playbooks fire on locally-known-bad infrastructure even
            when external feeds are quiet.
          </p>
        </div>
        {data && (
          <span className="text-xs text-muted-foreground">{data.total} entries</span>
        )}
      </div>

      <Card className="bg-card border-border">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">Indicators</CardTitle>
        </CardHeader>
        <CardContent className="pt-0">
          <IOCTable initial={data?.items ?? []} />
        </CardContent>
      </Card>
    </div>
  );
}
