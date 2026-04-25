// Types mirroring the FastAPI Pydantic schemas

export type Severity = "low" | "medium" | "high" | "critical";
export type AlertStatus = "new" | "in_progress" | "resolved" | "closed";
export type Verdict = "benign" | "suspicious" | "malicious" | "pending";
export type CaseStatus = "open" | "in_progress" | "resolved" | "closed";

export interface Alert {
  id: string;
  alert_id: string;
  timestamp: string;
  source: string;
  source_rule_id: string | null;
  severity: Severity;
  category: string | null;
  title: string;
  description: string | null;
  observables: Record<string, unknown>;
  mitre: {
    tactic?: string;
    technique?: string;
    subtechnique?: string;
  } | null;
  raw_log: string | null;
  enrichment: Record<string, unknown> | null;
  threat_score: number | null;
  verdict: Verdict | null;
  playbook_actions: unknown[];
  case_id: string | null;
  status: AlertStatus;
  created_at: string;
  updated_at: string;
}

export interface AlertListResponse {
  items: Alert[];
  total: number;
  page: number;
  page_size: number;
}

export interface Case {
  id: string;
  case_number: string;
  title: string;
  description: string | null;
  severity: Severity | null;
  status: CaseStatus;
  assigned_to: string | null;
  created_by: string | null;
  created_at: string;
  updated_at: string;
}

export interface CaseListResponse {
  items: Case[];
  total: number;
  page: number;
  page_size: number;
}

export interface Rule {
  id: string;
  name: string;
  description: string | null;
  rule_type: string;
  definition: Record<string, unknown>;
  severity: Severity | null;
  enabled: boolean;
  mitre_techniques: string[] | null;
  created_by: string | null;
  created_at: string;
}

export interface RuleListResponse {
  items: Rule[];
  total: number;
}

export interface StatsResponse {
  total_alerts: number;
  severity_breakdown: {
    low: number;
    medium: number;
    high: number;
    critical: number;
  };
  verdict_breakdown: {
    benign: number;
    suspicious: number;
    malicious: number;
    pending: number;
  };
  top_categories: { category: string; count: number }[];
  active_cases: number;
  total_agents: number;
  alerts_trend_24h: { hour: string; count: number }[];
}

export interface MitreTechniqueCount {
  technique: string;
  subtechnique: string | null;
  count: number;
}

export interface MitreTacticGroup {
  tactic: string;
  total: number;
  techniques: MitreTechniqueCount[];
}

export interface MitreStatsResponse {
  total_mapped: number;
  total_unmapped: number;
  tactics: MitreTacticGroup[];
}

export interface MttrTrendPoint {
  day: string;
  mtta_median_seconds: number | null;
  mttr_median_seconds: number | null;
  resolved_count: number;
}

export interface AuditLogEntry {
  id: string;
  action: string;
  entity_type: string | null;
  entity_id: string | null;
  details: Record<string, unknown> | null;
  performed_by: string | null;
  created_at: string;
}

export interface AuditLogListResponse {
  items: AuditLogEntry[];
  total: number;
}

export interface Evidence {
  id: string;
  case_id: string;
  kind: string;           // file | cowrie_session | pcap | screenshot | note
  filename: string;
  content_type: string;
  size_bytes: number;
  sha256: string;
  description: string | null;
  uploaded_by: string | null;
  created_at: string;
}

export interface EvidenceListResponse {
  items: Evidence[];
  total: number;
}

export interface MttrStatsResponse {
  mtta_median_seconds: number | null;
  mtta_p95_seconds: number | null;
  mttr_median_seconds: number | null;
  mttr_p95_seconds: number | null;
  open_cases: number;
  acknowledged_cases: number;
  resolved_cases: number;
  closed_cases: number;
  trend: MttrTrendPoint[];
}

export interface WazuhAgent {
  id: string;
  name: string;
  ip: string;
  status: string;
  os?: { name?: string; platform?: string };
  version?: string;
  lastKeepAlive?: string;
}
