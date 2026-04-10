from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.alert import AlertListResponse, AlertResponse, AlertUpdate
from app.services import alert_service

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("", response_model=AlertListResponse)
async def list_alerts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    severity: str | None = None,
    category: str | None = None,
    verdict: str | None = None,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    return await alert_service.list_alerts(
        db,
        page=page,
        page_size=page_size,
        severity=severity,
        category=category,
        verdict=verdict,
        status=status,
    )


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(alert_id: str, db: AsyncSession = Depends(get_db)):
    alert = await alert_service.get_alert(db, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.patch("/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: str,
    data: AlertUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update alert enrichment, verdict, or playbook actions.
    Used by Module 2 (enrichment) and Module 3 (playbook engine).
    """
    alert = await alert_service.update_alert(db, alert_id, data)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.get("/queue/next")
async def get_next_from_queue(
    db: AsyncSession = Depends(get_db),
):
    """Pop the next un-enriched alert from Redis queue.
    Used by Module 2 enrichment pipeline.
    """
    from app.core.redis import get_redis

    redis = await get_redis()
    result = await redis.rpop("alerts:pending_enrichment")
    if not result:
        return {"alert": None, "message": "Queue empty"}

    import json
    return {"alert": json.loads(result)}
