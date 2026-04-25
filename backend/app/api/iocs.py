from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.ioc import IOCCreate, IOCListResponse, IOCResponse, IOCUpdate
from app.services import ioc_service

router = APIRouter(prefix="/iocs", tags=["IOCs"])


@router.get("", response_model=IOCListResponse)
async def list_iocs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    ioc_type: str | None = None,
    enabled: bool | None = None,
    db: AsyncSession = Depends(get_db),
):
    return await ioc_service.list_iocs(
        db, page=page, page_size=page_size, ioc_type=ioc_type, enabled=enabled
    )


@router.post("", response_model=IOCResponse, status_code=201)
async def create_ioc(data: IOCCreate, db: AsyncSession = Depends(get_db)):
    return await ioc_service.create_ioc(db, data)


@router.patch("/{ioc_id}", response_model=IOCResponse)
async def update_ioc(ioc_id: UUID, data: IOCUpdate, db: AsyncSession = Depends(get_db)):
    row = await ioc_service.update_ioc(db, ioc_id, data)
    if row is None:
        raise HTTPException(status_code=404, detail="IOC not found")
    return row


@router.delete("/{ioc_id}", status_code=204)
async def delete_ioc(ioc_id: UUID, db: AsyncSession = Depends(get_db)):
    ok = await ioc_service.delete_ioc(db, ioc_id)
    if not ok:
        raise HTTPException(status_code=404, detail="IOC not found")
