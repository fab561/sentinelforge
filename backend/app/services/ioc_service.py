"""IOC watchlist — analyst-curated indicators.

The enrichment engine consults this list every run; matches inject a
synthetic provider result so the existing scoring + tag pipeline picks
them up without special-casing.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session
from app.models.ioc import IOC
from app.schemas.ioc import IOCCreate, IOCListResponse, IOCResponse, IOCUpdate


def _normalise(value: str, ioc_type: str) -> str:
    # IPs + domains + hashes are case-insensitive; URLs we keep as-is so
    # query-string casing isn't lost on a partial match.
    if ioc_type in {"ip", "domain", "hash"}:
        return value.strip().lower()
    return value.strip()


async def list_iocs(
    db: AsyncSession,
    *,
    page: int = 1,
    page_size: int = 50,
    ioc_type: str | None = None,
    enabled: bool | None = None,
) -> IOCListResponse:
    query = select(IOC)
    count_query = select(func.count(IOC.id))
    if ioc_type:
        query = query.where(IOC.ioc_type == ioc_type)
        count_query = count_query.where(IOC.ioc_type == ioc_type)
    if enabled is not None:
        query = query.where(IOC.enabled == enabled)
        count_query = count_query.where(IOC.enabled == enabled)
    total = (await db.execute(count_query)).scalar_one()
    rows = (
        await db.execute(
            query.order_by(IOC.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).scalars().all()
    return IOCListResponse(
        items=[IOCResponse.model_validate(r) for r in rows],
        total=total,
    )


async def create_ioc(db: AsyncSession, data: IOCCreate, created_by: UUID | None = None) -> IOC:
    row = IOC(
        value=_normalise(data.value, data.ioc_type),
        ioc_type=data.ioc_type,
        severity=data.severity,
        source=data.source,
        description=data.description,
        enabled=data.enabled,
        expires_at=data.expires_at,
        created_by=created_by,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def update_ioc(db: AsyncSession, ioc_id: UUID, data: IOCUpdate) -> IOC | None:
    row = (await db.execute(select(IOC).where(IOC.id == ioc_id))).scalar_one_or_none()
    if row is None:
        return None
    update = data.model_dump(exclude_unset=True)
    for k, v in update.items():
        setattr(row, k, v)
    await db.commit()
    await db.refresh(row)
    return row


async def delete_ioc(db: AsyncSession, ioc_id: UUID) -> bool:
    row = (await db.execute(select(IOC).where(IOC.id == ioc_id))).scalar_one_or_none()
    if row is None:
        return False
    await db.delete(row)
    await db.commit()
    return True


async def lookup_matches(values_by_type: dict[str, list[str]]) -> list[dict]:
    """Find watchlist hits for a batch of observables.

    Used by the enrichment engine — wants a single round-trip per alert.
    Returns dicts shaped like {value, ioc_type, severity, source} — a
    list because one alert can hit several IOCs (e.g. source_ip and
    destination_ip both flagged).
    """
    if not any(values_by_type.values()):
        return []

    now = datetime.now(timezone.utc)
    async with async_session() as db:
        all_hits: list[dict] = []
        for ioc_type, raw_values in values_by_type.items():
            if not raw_values:
                continue
            normalised = [_normalise(v, ioc_type) for v in raw_values]
            rows = (
                await db.execute(
                    select(IOC).where(
                        IOC.ioc_type == ioc_type,
                        IOC.enabled.is_(True),
                        IOC.value.in_(normalised),
                    )
                )
            ).scalars().all()
            for r in rows:
                # Treat past-due TTL as disabled — we honour it here so
                # we don't have to chase a sweeper job to flip enabled.
                if r.expires_at is not None and r.expires_at < now:
                    continue
                all_hits.append(
                    {
                        "value": r.value,
                        "ioc_type": r.ioc_type,
                        "severity": r.severity,
                        "source": r.source,
                        "description": r.description,
                    }
                )
        return all_hits
