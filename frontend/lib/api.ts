import type {
  AlertListResponse,
  Alert,
  AuditLogListResponse,
  CaseListResponse,
  Case,
  EvidenceListResponse,
  MitreStatsResponse,
  MttrStatsResponse,
  PlaybookDryRunResponse,
  PlaybookSummary,
  RuleListResponse,
  Rule,
  StatsResponse,
  WazuhAgent,
} from "./types";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function get<T>(path: string, params?: Record<string, string | number>): Promise<T> {
  const url = new URL(`${BASE}${path}`);
  if (params) {
    Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, String(v)));
  }
  const res = await fetch(url.toString(), { cache: "no-store" });
  if (!res.ok) throw new Error(`GET ${path} → ${res.status}`);
  return res.json();
}

async function patch<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`PATCH ${path} → ${res.status}`);
  return res.json();
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`POST ${path} → ${res.status}`);
  return res.json();
}

async function del(path: string): Promise<void> {
  const res = await fetch(`${BASE}${path}`, { method: "DELETE" });
  if (!res.ok) throw new Error(`DELETE ${path} → ${res.status}`);
}

// ── Alerts ────────────────────────────────────────────────
export const api = {
  alerts: {
    list: (params?: { page?: number; page_size?: number; severity?: string; status?: string }) =>
      get<AlertListResponse>("/api/alerts", params as Record<string, string | number>),
    get: (id: string) => get<Alert>(`/api/alerts/${id}`),
    update: (id: string, body: Partial<Alert>) => patch<Alert>(`/api/alerts/${id}`, body),
  },
  cases: {
    list: (params?: { page?: number; page_size?: number }) =>
      get<CaseListResponse>("/api/cases", params as Record<string, string | number>),
    get: (id: string) => get<Case>(`/api/cases/${id}`),
    create: (body: { title: string; description?: string; severity?: string }) =>
      post<Case>("/api/cases", body),
    update: (id: string, body: Partial<Case>) => patch<Case>(`/api/cases/${id}`, body),
    evidence: (id: string) =>
      get<EvidenceListResponse>(`/api/cases/${id}/evidence`),
    alerts: (id: string) => get<Alert[]>(`/api/cases/${id}/alerts`),
  },
  evidence: {
    // Stream-through; backend proxies MinIO so the browser never needs to
    // hit the internal endpoint directly.
    downloadUrl: (id: string) => {
      const base =
        (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "");
      return `${base}/api/evidence/${id}/download`;
    },
    async upload(
      caseId: string,
      file: File,
      description?: string,
    ): Promise<void> {
      const form = new FormData();
      form.append("file", file);
      if (description) form.append("description", description);
      const res = await fetch(`${BASE}/api/cases/${caseId}/evidence`, {
        method: "POST",
        body: form,
      });
      if (!res.ok) {
        const detail = await res.text();
        throw new Error(`Upload failed (${res.status}): ${detail}`);
      }
    },
    delete: (id: string) => del(`/api/evidence/${id}`),
  },
  rules: {
    list: () => get<RuleListResponse>("/api/rules"),
    create: (body: {
      name: string;
      description?: string;
      rule_type?: string;
      definition: Record<string, unknown>;
      severity?: string;
    }) => post<Rule>("/api/rules", body),
    update: (id: string, body: Partial<Rule>) => patch<Rule>(`/api/rules/${id}`, body),
    delete: (id: string) => del(`/api/rules/${id}`),
  },
  stats: {
    get: () => get<StatsResponse>("/api/stats"),
    mitre: () => get<MitreStatsResponse>("/api/stats/mitre"),
    mttr: () => get<MttrStatsResponse>("/api/stats/mttr"),
  },
  wazuh: {
    agents: () =>
      get<{ agents: WazuhAgent[]; total: number }>("/api/wazuh/agents"),
  },
  playbooks: {
    list: () => get<PlaybookSummary[]>("/api/playbooks"),
    reload: () =>
      fetch(`${BASE}/api/playbooks/reload`, { method: "POST" }).then((r) => {
        if (!r.ok) throw new Error(`reload failed (${r.status})`);
      }),
    dryRun: (alert: Record<string, unknown>) =>
      post<PlaybookDryRunResponse>("/api/playbooks/dry-run", { alert }),
  },
  audit: {
    list: (params?: {
      limit?: number;
      action?: string;
      entity_type?: string;
      entity_id?: string;
    }) =>
      get<AuditLogListResponse>(
        "/api/audit",
        params as Record<string, string | number>,
      ),
  },
};
