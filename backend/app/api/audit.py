from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.audit import AuditLogListResponse
from app.services import audit_service

router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get("", response_model=AuditLogListResponse)
async def list_audit(
    limit: int = Query(100, ge=1, le=500),
    action: str | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    return await audit_service.list_recent(
        db, limit=limit, action=action, entity_type=entity_type, entity_id=entity_id
    )
