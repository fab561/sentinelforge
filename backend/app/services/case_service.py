import re
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert
from app.models.case import Case
from app.schemas.case import CaseCreate, CaseListResponse, CaseResponse, CaseUpdate


async def _next_case_number(db: AsyncSession) -> str:
    """Return the next sequential case number for the current year.

    Uses MAX(...) over existing numbers so it stays correct even after
    deletions, and takes a transaction-scoped advisory lock to serialize
    concurrent creators (prevents duplicate case_number on race).
    """
    year = datetime.now(timezone.utc).year
    # pg_advisory_xact_lock keyed on the year — released at COMMIT/ROLLBACK
    await db.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": year})
    pattern = f"CASE-{year}-%"
    result = await db.execute(
        select(func.max(Case.case_number)).where(Case.case_number.like(pattern))
    )
    latest = result.scalar_one_or_none()
    next_num = 1
    if latest:
        m = re.search(r"(\d+)$", latest)
        if m:
            next_num = int(m.group(1)) + 1
    return f"CASE-{year}-{next_num:04d}"


async def list_cases(
    db: AsyncSession,
    *,
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
    severity: str | None = None,
) -> CaseListResponse:
    query = select(Case)
    count_query = select(func.count(Case.id))

    if status:
        query = query.where(Case.status == status)
        count_query = count_query.where(Case.status == status)
    if severity:
        query = query.where(Case.severity == severity)
        count_query = count_query.where(Case.severity == severity)

    total = (await db.execute(count_query)).scalar_one()
    query = query.order_by(Case.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    cases = result.scalars().all()

    return CaseListResponse(
        items=[CaseResponse.model_validate(c) for c in cases],
        total=total,
        page=page,
        page_size=page_size,
    )


async def get_case(db: AsyncSession, case_id: UUID) -> Case | None:
    result = await db.execute(select(Case).where(Case.id == case_id))
    return result.scalar_one_or_none()


async def create_case(
    db: AsyncSession,
    data: CaseCreate,
    created_by: UUID | None = None,
) -> Case:
    case_number = await _next_case_number(db)

    case = Case(
        case_number=case_number,
        title=data.title,
        description=data.description,
        severity=data.severity,
        assigned_to=data.assigned_to,
        created_by=created_by,
    )
    db.add(case)
    await db.flush()

    # Link alerts to this case
    if data.alert_ids:
        for alert_id in data.alert_ids:
            result = await db.execute(select(Alert).where(Alert.alert_id == alert_id))
            alert = result.scalar_one_or_none()
            if alert:
                alert.case_id = case.id

    await db.commit()
    await db.refresh(case)
    return case


_ACK_STATUSES = {"investigating", "resolved", "closed"}
_RESOLVED_STATUSES = {"resolved", "closed"}


async def update_case(db: AsyncSession, case_id: UUID, data: CaseUpdate) -> Case | None:
    case = await get_case(db, case_id)
    if not case:
        return None

    update_data = data.model_dump(exclude_unset=True)
    new_status = update_data.get("status")

    for key, value in update_data.items():
        setattr(case, key, value)

    # Stamp lifecycle timestamps on first transition into each stage. Never
    # overwrite — if a case is re-opened and re-resolved, MTTR keeps the
    # first-resolution duration (which is the meaningful SLA figure).
    now = datetime.now(timezone.utc)
    if new_status in _ACK_STATUSES and case.acknowledged_at is None:
        case.acknowledged_at = now
    if new_status in _RESOLVED_STATUSES and case.resolved_at is None:
        case.resolved_at = now
    if new_status == "closed" and case.closed_at is None:
        case.closed_at = now

    case.updated_at = now
    await db.commit()
    await db.refresh(case)
    return case
