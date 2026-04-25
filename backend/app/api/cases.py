from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from fastapi.responses import Response

from app.schemas.alert import AlertResponse
from app.schemas.case import CaseCreate, CaseListResponse, CaseResponse, CaseUpdate
from app.services import audit_service, case_service, evidence_service, pdf_service

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


@router.get("/{case_id}/export.pdf")
async def export_case_pdf(case_id: UUID, db: AsyncSession = Depends(get_db)):
    """Render a case as a portable PDF report (header + alerts + evidence
    + audit). Suitable for attaching to a ticket or emailing to IR."""
    case = await case_service.get_case(db, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    alerts = await case_service.list_alerts_in_case(db, case_id)
    evidence = (await evidence_service.list_for_case(db, case_id)).items
    audit = (
        await audit_service.list_recent(db, limit=50, entity_id=str(case_id))
    ).items

    case_dict = {
        "case_number": case.case_number,
        "title": case.title,
        "description": case.description,
        "severity": case.severity,
        "status": case.status,
        "created_at": case.created_at,
        "acknowledged_at": case.acknowledged_at,
        "resolved_at": case.resolved_at,
        "closed_at": case.closed_at,
    }
    pdf_bytes = await pdf_service.render_case_pdf(
        case_dict,
        [a.__dict__ for a in alerts],
        [e.model_dump() for e in evidence],
        [r.model_dump() for r in audit],
    )

    filename = f"{case.case_number}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(pdf_bytes)),
        },
    )
