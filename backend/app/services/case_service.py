from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert
from app.models.case import Case
from app.schemas.case import CaseCreate, CaseListResponse, CaseResponse, CaseUpdate


def _next_case_number(count: int) -> str:
    year = datetime.now(timezone.utc).year
    return f"CASE-{year}-{count + 1:04d}"


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


async def create_case(db: AsyncSession, data: CaseCreate) -> Case:
    # Generate sequential case number
    count_result = await db.execute(select(func.count(Case.id)))
    count = count_result.scalar_one()

    case = Case(
        case_number=_next_case_number(count),
        title=data.title,
        description=data.description,
        severity=data.severity,
        assigned_to=data.assigned_to,
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


async def update_case(db: AsyncSession, case_id: UUID, data: CaseUpdate) -> Case | None:
    case = await get_case(db, case_id)
    if not case:
        return None

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(case, key, value)

    case.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(case)
    return case
