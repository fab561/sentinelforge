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
