from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert
from app.schemas.alert import AlertListResponse, AlertResponse, AlertUpdate


async def list_alerts(
    db: AsyncSession,
    *,
    page: int = 1,
    page_size: int = 20,
    severity: str | None = None,
    category: str | None = None,
    verdict: str | None = None,
    status: str | None = None,
) -> AlertListResponse:
    query = select(Alert)
    count_query = select(func.count(Alert.id))

    if severity:
        query = query.where(Alert.severity == severity)
        count_query = count_query.where(Alert.severity == severity)
    if category:
        query = query.where(Alert.category == category)
        count_query = count_query.where(Alert.category == category)
    if verdict:
        query = query.where(Alert.verdict == verdict)
        count_query = count_query.where(Alert.verdict == verdict)
    if status:
        query = query.where(Alert.status == status)
        count_query = count_query.where(Alert.status == status)

    total = (await db.execute(count_query)).scalar_one()

    query = query.order_by(Alert.timestamp.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    alerts = result.scalars().all()

    return AlertListResponse(
        items=[AlertResponse.model_validate(a) for a in alerts],
        total=total,
        page=page,
        page_size=page_size,
    )


async def get_alert(db: AsyncSession, alert_id: str) -> Alert | None:
    result = await db.execute(select(Alert).where(Alert.alert_id == alert_id))
    return result.scalar_one_or_none()


async def get_alert_by_uuid(db: AsyncSession, uuid: UUID) -> Alert | None:
    result = await db.execute(select(Alert).where(Alert.id == uuid))
    return result.scalar_one_or_none()


async def update_alert(
    db: AsyncSession, alert_id: str, data: AlertUpdate
) -> Alert | None:
    alert = await get_alert(db, alert_id)
    if not alert:
        return None

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(alert, key, value)

    alert.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(alert)
    return alert


async def create_alert(db: AsyncSession, **kwargs) -> Alert:
    alert = Alert(**kwargs)
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    return alert
