"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import type { PlaybookDryRunResponse } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { PlayCircle } from "lucide-react";

const DEFAULTS = {
  malicious: {
    alert_id: "dry-run-malicious",
    severity: "critical",
    category: "brute_force",
    title: "SSH brute force from 1.2.3.4",
    threat_score: 90,
    verdict: "malicious",
    observables: { source_ip: "1.2.3.4", destination_port: 22 },
    enrichment: {
      summary: { tags: ["gn:malicious", "vt:malicious", "abuse:high"] },
    },
  },
  suspicious: {
    alert_id: "dry-run-suspicious",
    severity: "medium",
    category: "web_attack",
    title: "Suspicious request",
    threat_score: 55,
    verdict: "suspicious",
    observables: { source_ip: "9.9.9.9" },
    enrichment: { summary: { tags: ["gn:noise"] } },
  },
  benign: {
    alert_id: "dry-run-benign",
    severity: "low",
    category: "system",
    title: "Routine update",
    threat_score: 5,
    verdict: "benign",
    observables: {},
    enrichment: { summary: { tags: [] } },
  },
};

export function DryRunPanel() {
  const [json, setJson] = useState<string>(JSON.stringify(DEFAULTS.malicious, null, 2));
  const [result, setResult] = useState<PlaybookDryRunResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  function loadPreset(key: keyof typeof DEFAULTS) {
    setJson(JSON.stringify(DEFAULTS[key], null, 2));
    setError(null);
    setResult(null);
  }

  async function run() {
    setError(null);
    setBusy(true);
    try {
      const alert = JSON.parse(json);
      const res = await api.playbooks.dryRun(alert);
      setResult(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Dry-run failed");
      setResult(null);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card className="bg-card border-border">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm flex items-center gap-2">
          <PlayCircle className="h-4 w-4 text-primary" />
          Dry Run
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3 pt-0">
        <p className="text-xs text-muted-foreground">
          Paste an alert payload (or pick a preset) and see which playbooks would
          fire without touching the database, Cloudflare, or Wazuh.
        </p>

        <div className="flex flex-wrap gap-2">
          <Preset label="Malicious" onClick={() => loadPreset("malicious")} />
          <Preset label="Suspicious" onClick={() => loadPreset("suspicious")} />
          <Preset label="Benign" onClick={() => loadPreset("benign")} />
        </div>

        <Textarea
          value={json}
          onChange={(e) => setJson(e.target.value)}
          className="font-mono text-[11px] min-h-[200px]"
        />

        <div className="flex items-center gap-2">
          <Button onClick={run} disabled={busy} size="sm">
            {busy ? "Running..." : "Run"}
          </Button>
          {error && <span className="text-xs text-red-300">{error}</span>}
        </div>

        {result && (
          <div className="space-y-3 pt-2">
            <div className="text-xs">
              <span className="text-muted-foreground">Matched: </span>
              {result.matched_playbooks.length === 0 ? (
                <span className="text-muted-foreground italic">none</span>
              ) : (
                result.matched_playbooks.map((n) => (
                  <span
                    key={n}
                    className="rounded border border-primary/40 bg-primary/15 text-primary px-2 py-0.5 mr-1 font-mono text-[10px]"
                  >
                    {n}
                  </span>
                ))
              )}
            </div>

            {result.planned_actions.length > 0 && (
              <div className="space-y-1">
                <div className="text-[11px] text-muted-foreground">
                  Planned actions ({result.planned_actions.length}):
                </div>
                {result.planned_actions.map((a, i) => (
                  <div
                    key={i}
                    className="rounded border border-border px-2.5 py-1.5 text-[11px]"
                  >
                    <span className="font-mono text-muted-foreground">
                      {a.playbook}
                    </span>{" "}
                    →{" "}
                    <span className="font-mono text-primary">{a.action_type}</span>
                    {a.target && (
                      <span className="text-muted-foreground"> · target: {a.target}</span>
                    )}
                    {Object.keys(a.params).length > 0 && (
                      <pre className="text-[10px] text-muted-foreground mt-1 whitespace-pre-wrap font-mono">
                        {JSON.stringify(a.params, null, 2)}
                      </pre>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function Preset({ label, onClick }: { label: string; onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="rounded-md border border-border px-2.5 py-1 text-xs hover:bg-accent"
    >
      {label}
    </button>
  );
}
