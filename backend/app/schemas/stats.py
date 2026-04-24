from pydantic import BaseModel


class SeverityCount(BaseModel):
    low: int = 0
    medium: int = 0
    high: int = 0
    critical: int = 0


class VerdictCount(BaseModel):
    benign: int = 0
    suspicious: int = 0
    malicious: int = 0
    pending: int = 0  # not yet enriched


class CategoryCount(BaseModel):
    category: str
    count: int


class TrendPoint(BaseModel):
    hour: str  # ISO timestamp (hourly bucket)
    count: int


class StatsResponse(BaseModel):
    total_alerts: int
    severity_breakdown: SeverityCount
    verdict_breakdown: VerdictCount
    top_categories: list[CategoryCount]
    active_cases: int
    total_agents: int
    alerts_trend_24h: list[TrendPoint]


class MitreTechniqueCount(BaseModel):
    technique: str           # e.g. "T1110"
    subtechnique: str | None  # e.g. "T1110.003"
    count: int


class MitreTacticGroup(BaseModel):
    tactic: str                       # e.g. "Credential Access"
    total: int                        # sum of technique counts
    techniques: list[MitreTechniqueCount]


class MitreStatsResponse(BaseModel):
    total_mapped: int                 # alerts with any mitre data
    total_unmapped: int               # alerts missing mitre
    tactics: list[MitreTacticGroup]


class MttrTrendPoint(BaseModel):
    day: str                          # ISO date
    mtta_median_seconds: float | None
    mttr_median_seconds: float | None
    resolved_count: int


class MttrStatsResponse(BaseModel):
    # Overall medians over the full history (and p95 for tail visibility)
    mtta_median_seconds: float | None
    mtta_p95_seconds: float | None
    mttr_median_seconds: float | None
    mttr_p95_seconds: float | None

    # Case counts in each lifecycle stage (snapshots, not durations)
    open_cases: int
    acknowledged_cases: int     # investigating but not resolved
    resolved_cases: int
    closed_cases: int

    # 14-day rolling trend (one point per calendar day)
    trend: list[MttrTrendPoint]
