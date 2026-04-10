from datetime import datetime, timedelta, timezone

from sqlalchemy import case, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.wazuh_client import WazuhManagerClient
from app.models.alert import Alert
from app.models.case import Case
from app.schemas.stats import (
    CategoryCount,
    SeverityCount,
    StatsResponse,
    TrendPoint,
    VerdictCount,
)


async def get_dashboard_stats(db: AsyncSession) -> StatsResponse:
    # Total alerts
    total = (await db.execute(select(func.count(Alert.id)))).scalar_one()

    # Severity breakdown
    sev_result = await db.execute(
        select(Alert.severity, func.count(Alert.id)).group_by(Alert.severity)
    )
    sev_map = dict(sev_result.all())
    severity_breakdown = SeverityCount(
        low=sev_map.get("low", 0),
        medium=sev_map.get("medium", 0),
        high=sev_map.get("high", 0),
        critical=sev_map.get("critical", 0),
    )

    # Verdict breakdown
    ver_result = await db.execute(
        select(Alert.verdict, func.count(Alert.id)).group_by(Alert.verdict)
    )
    ver_map = dict(ver_result.all())
    verdict_breakdown = VerdictCount(
        benign=ver_map.get("benign", 0),
        suspicious=ver_map.get("suspicious", 0),
        malicious=ver_map.get("malicious", 0),
        pending=ver_map.get(None, 0),
    )

    # Top categories
    cat_result = await db.execute(
        select(Alert.category, func.count(Alert.id))
        .where(Alert.category.isnot(None))
        .group_by(Alert.category)
        .order_by(func.count(Alert.id).desc())
        .limit(10)
    )
    top_categories = [CategoryCount(category=c, count=n) for c, n in cat_result.all()]

    # Active cases
    active_cases = (
        await db.execute(
            select(func.count(Case.id)).where(Case.status.in_(["open", "investigating"]))
        )
    ).scalar_one()

    # Agent count (try Wazuh, fallback to 0)
    total_agents = 0
    try:
        wazuh = WazuhManagerClient()
        agents = await wazuh.get_agents()
        total_agents = len(agents)
        await wazuh.close()
    except Exception:
        pass

    # 24h trend (hourly buckets)
    now = datetime.now(timezone.utc)
    since = now - timedelta(hours=24)
    trend_result = await db.execute(
        select(
            func.date_trunc("hour", Alert.timestamp).label("hour"),
            func.count(Alert.id),
        )
        .where(Alert.timestamp >= since)
        .group_by(text("1"))
        .order_by(text("1"))
    )
    alerts_trend = [
        TrendPoint(hour=h.isoformat(), count=c) for h, c in trend_result.all()
    ]

    return StatsResponse(
        total_alerts=total,
        severity_breakdown=severity_breakdown,
        verdict_breakdown=verdict_breakdown,
        top_categories=top_categories,
        active_cases=active_cases,
        total_agents=total_agents,
        alerts_trend_24h=alerts_trend,
    )
