from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.evidence import Evidence
from app.schemas.evidence import EvidenceListResponse, EvidenceResponse


async def list_for_case(db: AsyncSession, case_id: UUID) -> EvidenceListResponse:
    count = (
        await db.execute(select(func.count(Evidence.id)).where(Evidence.case_id == case_id))
    ).scalar_one()
    rows = (
        await db.execute(
            select(Evidence)
            .where(Evidence.case_id == case_id)
            .order_by(Evidence.created_at.desc())
        )
    ).scalars().all()
    return EvidenceListResponse(
        items=[EvidenceResponse.model_validate(e) for e in rows],
        total=count,
    )


async def get(db: AsyncSession, evidence_id: UUID) -> Evidence | None:
    return (
        await db.execute(select(Evidence).where(Evidence.id == evidence_id))
    ).scalar_one_or_none()


async def create(
    db: AsyncSession,
    *,
    case_id: UUID,
    kind: str,
    filename: str,
    content_type: str,
    size_bytes: int,
    sha256: str,
    storage_key: str,
    description: str | None = None,
    uploaded_by: UUID | None = None,
) -> Evidence:
    row = Evidence(
        case_id=case_id,
        kind=kind,
        filename=filename,
        content_type=content_type,
        size_bytes=size_bytes,
        sha256=sha256,
        storage_key=storage_key,
        description=description,
        uploaded_by=uploaded_by,
    )
    db.add(row)
    await db.flush()
    from app.services import audit_service
    await audit_service.log(
        db=db,
        action="evidence.uploaded",
        entity_type="case",
        entity_id=case_id,
        details={
            "evidence_id": str(row.id),
            "filename": filename,
            "kind": kind,
            "size_bytes": size_bytes,
            "sha256": sha256,
        },
        performed_by=uploaded_by,
    )
    await db.commit()
    await db.refresh(row)
    return row


async def delete(db: AsyncSession, row: Evidence) -> None:
    case_id = row.case_id
    evidence_id = row.id
    filename = row.filename
    await db.delete(row)
    from app.services import audit_service
    await audit_service.log(
        db=db,
        action="evidence.deleted",
        entity_type="case",
        entity_id=case_id,
        details={"evidence_id": str(evidence_id), "filename": filename},
    )
    await db.commit()
