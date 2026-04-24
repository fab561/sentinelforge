from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.stats import MitreStatsResponse, StatsResponse
from app.services.stats_service import get_dashboard_stats, get_mitre_stats

router = APIRouter(prefix="/stats", tags=["Stats"])


@router.get("", response_model=StatsResponse)
async def dashboard_stats(db: AsyncSession = Depends(get_db)):
    return await get_dashboard_stats(db)


@router.get("/mitre", response_model=MitreStatsResponse)
async def mitre_stats(db: AsyncSession = Depends(get_db)):
    """MITRE ATT&CK heatmap data — techniques grouped by tactic, sorted by volume."""
    return await get_mitre_stats(db)
