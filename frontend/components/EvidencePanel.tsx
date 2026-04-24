"use client";

import { useEffect, useState, useTransition } from "react";
import { api } from "@/lib/api";
import type { Evidence } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Paperclip, Download, Trash2, UploadCloud } from "lucide-react";

function humanSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
}

function kindLabel(kind: string): string {
  const map: Record<string, string> = {
    cowrie_session: "SSH session",
    pcap: "Packet capture",
    screenshot: "Screenshot",
    file: "File",
    note: "Note",
  };
  return map[kind] ?? kind;
}

export function EvidencePanel({ caseId }: { caseId: string }) {
  const [items, setItems] = useState<Evidence[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [, startTransition] = useTransition();

  async function refresh() {
    setLoading(true);
    try {
      const res = await api.cases.evidence(caseId);
      setItems(res.items);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh();
    // caseId is stable within this page render; no deps edge cases worth
    // worrying about here.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [caseId]);

  async function handleFile(file: File, description?: string) {
    setError(null);
    setUploading(true);
    try {
      await api.evidence.upload(caseId, file, description);
      startTransition(refresh);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  }

  async function handleDelete(id: string) {
    if (!confirm("Delete this evidence?")) return;
    try {
      await api.evidence.delete(id);
      startTransition(refresh);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Delete failed");
    }
  }

  return (
    <Card className="bg-card border-border">
      <CardHeader className="pb-2 flex flex-row items-center justify-between">
        <CardTitle className="text-sm flex items-center gap-2">
          <Paperclip className="h-4 w-4 text-primary" />
          Evidence ({items.length})
        </CardTitle>
        <label
          className={`inline-flex items-center gap-1.5 cursor-pointer rounded-md border border-border px-2.5 py-1 text-xs hover:bg-accent ${
            uploading ? "opacity-60 pointer-events-none" : ""
          }`}
        >
          <UploadCloud className="h-3.5 w-3.5" />
          {uploading ? "Uploading..." : "Attach"}
          <input
            type="file"
            className="hidden"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) handleFile(f);
              e.target.value = "";
            }}
          />
        </label>
      </CardHeader>
      <CardContent className="space-y-2 pt-0">
        {error && (
          <div className="rounded border border-red-500/40 bg-red-500/10 px-2.5 py-1.5 text-xs text-red-300">
            {error}
          </div>
        )}

        {loading ? (
          <p className="text-xs text-muted-foreground py-2">Loading...</p>
        ) : items.length === 0 ? (
          <p className="text-xs text-muted-foreground py-2">
            No evidence attached yet. Drop PCAPs, Cowrie session logs, or screenshots here.
          </p>
        ) : (
          items.map((e) => (
            <div
              key={e.id}
              className="flex items-center gap-2 rounded-md border border-border px-2.5 py-2 text-xs"
            >
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <span className="font-medium truncate">{e.filename}</span>
                  <span className="rounded bg-secondary px-1.5 py-0.5 text-[10px] text-muted-foreground">
                    {kindLabel(e.kind)}
                  </span>
                </div>
                <div className="text-[11px] text-muted-foreground font-mono">
                  {humanSize(e.size_bytes)} · sha256:{e.sha256.slice(0, 12)}…
                </div>
                {e.description && (
                  <p className="text-[11px] text-muted-foreground mt-0.5">{e.description}</p>
                )}
              </div>
              <a
                href={api.evidence.downloadUrl(e.id)}
                className="inline-flex items-center gap-1 rounded border border-border px-2 py-1 text-[11px] hover:bg-accent"
              >
                <Download className="h-3 w-3" />
                Download
              </a>
              <Button
                variant="ghost"
                size="sm"
                className="h-7 px-2 text-red-400 hover:text-red-300"
                onClick={() => handleDelete(e.id)}
              >
                <Trash2 className="h-3.5 w-3.5" />
              </Button>
            </div>
          ))
        )}
      </CardContent>
    </Card>
  );
}
