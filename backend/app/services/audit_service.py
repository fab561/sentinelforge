"""Audit log helper.

Records security-relevant actions so analysts and compliance reviewers
have a tamper-evident trail of "who did what to which entity when".

Writes are deliberately fire-and-forget — a failed audit insert must
not break the underlying mutation. Anything important enough to roll
back belongs in the application's main transaction, not here.
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session
from app.models.audit_log import AuditLog
from app.schemas.audit import AuditLogListResponse, AuditLogResponse

logger = logging.getLogger(__name__)


async def log(
    *,
    action: str,
    entity_type: str | None = None,
    entity_id: str | UUID | None = None,
    details: dict[str, Any] | None = None,
    performed_by: UUID | None = None,
    db: AsyncSession | None = None,
) -> None:
    """Insert an audit row. Best-effort — exceptions are logged and swallowed."""
    try:
        row = AuditLog(
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id is not None else None,
            details=details,
            performed_by=performed_by,
        )
        if db is not None:
            db.add(row)
            await db.flush()
        else:
            async with async_session() as fresh:
                fresh.add(row)
                await fresh.commit()
    except Exception as exc:
        logger.warning("audit log failed for action=%s: %s", action, exc)


async def list_recent(
    db: AsyncSession,
    *,
    limit: int = 100,
    action: str | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
) -> AuditLogListResponse:
    query = select(AuditLog).order_by(desc(AuditLog.created_at))
    count_query = select(func.count(AuditLog.id))
    if action:
        query = query.where(AuditLog.action == action)
        count_query = count_query.where(AuditLog.action == action)
    if entity_type:
        query = query.where(AuditLog.entity_type == entity_type)
        count_query = count_query.where(AuditLog.entity_type == entity_type)
    if entity_id:
        query = query.where(AuditLog.entity_id == entity_id)
        count_query = count_query.where(AuditLog.entity_id == entity_id)

    total = (await db.execute(count_query)).scalar_one()
    rows = (await db.execute(query.limit(limit))).scalars().all()
    return AuditLogListResponse(
        items=[AuditLogResponse.model_validate(r) for r in rows],
        total=total,
    )
