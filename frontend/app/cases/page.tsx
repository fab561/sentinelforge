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

export default async function CasesPage({
  searchParams,
}: {
  searchParams: Promise<{ page?: string }>;
}) {
  const sp = await searchParams;
  const page = Number(sp.page ?? 1);
  const data = await api.cases.list({ page, page_size: 25 }).catch(() => null);
  const totalPages = data ? Math.ceil(data.total / 25) : 1;

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-semibold">Cases</h1>
        {data && (
          <span className="text-xs text-muted-foreground">{data.total} total</span>
        )}
      </div>

      <div className="rounded-lg border border-border overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow className="border-border hover:bg-transparent">
              <TableHead className="text-xs w-32">Case #</TableHead>
              <TableHead className="text-xs">Title</TableHead>
              <TableHead className="text-xs w-24">Severity</TableHead>
              <TableHead className="text-xs w-28">Status</TableHead>
              <TableHead className="text-xs w-44">Created</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data?.items.length ? (
              data.items.map((c) => (
                <TableRow key={c.id} className="border-border hover:bg-accent/50 cursor-pointer">
                  <TableCell className="py-2.5 text-xs font-mono text-muted-foreground">
                    {c.case_number}
                  </TableCell>
                  <TableCell className="py-2.5">
                    <Link
                      href={`/cases/${c.id}`}
                      className="text-xs font-medium hover:text-primary hover:underline"
                    >
                      {c.title}
                    </Link>
                  </TableCell>
                  <TableCell className="py-2.5">
                    {c.severity ? (
                      <SeverityBadge severity={c.severity} />
                    ) : (
                      <span className="text-xs text-muted-foreground">—</span>
                    )}
                  </TableCell>
                  <TableCell className="py-2.5">
                    <StatusBadge status={c.status} />
                  </TableCell>
                  <TableCell className="py-2.5 text-xs text-muted-foreground font-mono">
                    {new Date(c.created_at).toLocaleString()}
                  </TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={5} className="text-center text-xs text-muted-foreground py-8">
                  No cases found.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>

      {totalPages > 1 && (
        <div className="flex gap-1 justify-end">
          {Array.from({ length: totalPages }, (_, i) => i + 1).map((p) => (
            <Link
              key={p}
              href={`/cases?page=${p}`}
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
