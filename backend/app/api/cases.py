from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.alert import AlertResponse
from app.schemas.case import CaseCreate, CaseListResponse, CaseResponse, CaseUpdate
from app.services import case_service

router = APIRouter(prefix="/cases", tags=["Cases"])


@router.get("", response_model=CaseListResponse)
async def list_cases(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = None,
    severity: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    return await case_service.list_cases(
        db, page=page, page_size=page_size, status=status, severity=severity
    )


@router.post("", response_model=CaseResponse, status_code=201)
async def create_case(
    data: CaseCreate,
    db: AsyncSession = Depends(get_db),
):
    return await case_service.create_case(db, data)


@router.get("/{case_id}", response_model=CaseResponse)
async def get_case(case_id: UUID, db: AsyncSession = Depends(get_db)):
    case = await case_service.get_case(db, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@router.patch("/{case_id}", response_model=CaseResponse)
async def update_case(
    case_id: UUID,
    data: CaseUpdate,
    db: AsyncSession = Depends(get_db),
):
    case = await case_service.update_case(db, case_id, data)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@router.get("/{case_id}/alerts", response_model=list[AlertResponse])
async def list_case_alerts(case_id: UUID, db: AsyncSession = Depends(get_db)):
    """All alerts correlated/attached to a case."""
    if not await case_service.get_case(db, case_id):
        raise HTTPException(status_code=404, detail="Case not found")
    return await case_service.list_alerts_in_case(db, case_id)
