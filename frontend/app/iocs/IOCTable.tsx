"use client";

import { useState, useTransition } from "react";
import { api } from "@/lib/api";
import type { IOC } from "@/lib/types";
import { SeverityBadge } from "@/components/SeverityBadge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Trash2, Plus } from "lucide-react";

const TYPES = ["ip", "domain", "hash", "url"] as const;
const SEVERITIES = ["low", "medium", "high", "critical"] as const;

export function IOCTable({ initial }: { initial: IOC[] }) {
  const [items, setItems] = useState<IOC[]>(initial);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [, startTransition] = useTransition();

  // Add-form fields
  const [value, setValue] = useState("");
  const [iocType, setIocType] = useState<(typeof TYPES)[number]>("ip");
  const [severity, setSeverity] = useState<(typeof SEVERITIES)[number]>("medium");
  const [description, setDescription] = useState("");

  async function refresh() {
    const res = await api.iocs.list({ page_size: 200 });
    setItems(res.items);
  }

  async function add() {
    if (!value.trim()) {
      setError("value is required");
      return;
    }
    setError(null);
    setBusy(true);
    try {
      await api.iocs.create({
        value: value.trim(),
        ioc_type: iocType,
        severity,
        description: description.trim() || undefined,
      });
      setValue("");
      setDescription("");
      startTransition(refresh);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Add failed");
    } finally {
      setBusy(false);
    }
  }

  async function toggle(id: string, enabled: boolean) {
    try {
      await api.iocs.toggle(id, !enabled);
      startTransition(refresh);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Toggle failed");
    }
  }

  async function remove(id: string) {
    if (!confirm("Delete this IOC?")) return;
    try {
      await api.iocs.delete(id);
      startTransition(refresh);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Delete failed");
    }
  }

  return (
    <div className="space-y-3">
      {/* Add form — inline for fast analyst entry rather than a modal. */}
      <div className="flex flex-wrap gap-2 items-center rounded-md border border-border p-2.5 bg-background/40">
        <Input
          placeholder="value (1.2.3.4 / evil.com / sha256...)"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          className="h-8 text-xs flex-1 min-w-[200px]"
        />
        <select
          value={iocType}
          onChange={(e) => setIocType(e.target.value as (typeof TYPES)[number])}
          className="h-8 text-xs rounded border border-border bg-background px-2"
        >
          {TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
        </select>
        <select
          value={severity}
          onChange={(e) => setSeverity(e.target.value as (typeof SEVERITIES)[number])}
          className="h-8 text-xs rounded border border-border bg-background px-2"
        >
          {SEVERITIES.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
        <Input
          placeholder="note (optional)"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          className="h-8 text-xs flex-1 min-w-[150px]"
        />
        <Button onClick={add} disabled={busy} size="sm" className="h-8">
          <Plus className="h-3.5 w-3.5 mr-1" />
          Add
        </Button>
      </div>

      {error && (
        <div className="rounded border border-red-500/40 bg-red-500/10 px-2.5 py-1.5 text-xs text-red-300">
          {error}
        </div>
      )}

      <div className="rounded-lg border border-border overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow className="border-border hover:bg-transparent">
              <TableHead className="text-xs">Value</TableHead>
              <TableHead className="text-xs w-20">Type</TableHead>
              <TableHead className="text-xs w-24">Severity</TableHead>
              <TableHead className="text-xs w-24">Source</TableHead>
              <TableHead className="text-xs">Description</TableHead>
              <TableHead className="text-xs w-24">Added</TableHead>
              <TableHead className="text-xs w-32 text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {items.length ? (
              items.map((i) => (
                <TableRow key={i.id} className="border-border">
                  <TableCell className="py-2 font-mono text-xs break-all">{i.value}</TableCell>
                  <TableCell className="py-2 text-xs uppercase font-mono">{i.ioc_type}</TableCell>
                  <TableCell className="py-2"><SeverityBadge severity={i.severity} /></TableCell>
                  <TableCell className="py-2 text-xs text-muted-foreground">{i.source}</TableCell>
                  <TableCell className="py-2 text-xs text-muted-foreground">{i.description ?? "—"}</TableCell>
                  <TableCell className="py-2 text-[11px] text-muted-foreground font-mono">
                    {new Date(i.created_at).toLocaleDateString()}
                  </TableCell>
                  <TableCell className="py-2 text-right">
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-7 px-2 text-xs"
                      onClick={() => toggle(i.id, i.enabled)}
                    >
                      {i.enabled ? "disable" : "enable"}
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-7 px-2 text-red-400 hover:text-red-300"
                      onClick={() => remove(i.id)}
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={7} className="text-center text-xs text-muted-foreground py-8">
                  No IOCs yet. Add one above to start enriching alerts against it.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
