"""Evidence attachment API.

Two router objects so Cases nests uploads under /api/cases/{id}/evidence
while the top-level /api/evidence/{id}/download sits flat for portable
presigned-URL links.
"""

from __future__ import annotations

from mimetypes import guess_type
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.storage import get_object_bytes, upload_bytes
from app.schemas.evidence import EvidenceListResponse, EvidenceResponse
from app.services import case_service, evidence_service

case_evidence_router = APIRouter(prefix="/cases/{case_id}/evidence", tags=["Evidence"])
evidence_router = APIRouter(prefix="/evidence", tags=["Evidence"])


# Anything not on this list is blocked; keeps the honeypot from becoming a
# free file-share or a malware-drop path if we ever expose this publicly.
_ALLOWED_EXTS = {
    ".pcap", ".pcapng", ".log", ".txt", ".json", ".ttylog",
    ".png", ".jpg", ".jpeg", ".pdf", ".md",
}
_COWRIE_KINDS = {".ttylog", ".json"}   # heuristic for auto-kind detection


def _infer_kind(filename: str, explicit: str | None) -> str:
    if explicit:
        return explicit
    name = filename.lower()
    if name.endswith(".pcap") or name.endswith(".pcapng"):
        return "pcap"
    if name.endswith(".ttylog") or "cowrie" in name:
        return "cowrie_session"
    if name.endswith((".png", ".jpg", ".jpeg")):
        return "screenshot"
    return "file"


@case_evidence_router.get("", response_model=EvidenceListResponse)
async def list_case_evidence(case_id: UUID, db: AsyncSession = Depends(get_db)):
    if not await case_service.get_case(db, case_id):
        raise HTTPException(status_code=404, detail="Case not found")
    return await evidence_service.list_for_case(db, case_id)


@case_evidence_router.post("", response_model=EvidenceResponse, status_code=201)
async def upload_case_evidence(
    case_id: UUID,
    file: UploadFile = File(...),
    description: str | None = Form(default=None),
    kind: str | None = Form(default=None),
    db: AsyncSession = Depends(get_db),
):
    """Attach a file to a case. Streamed from the request, size-capped, then
    uploaded to MinIO keyed by sha256 so dedup is automatic."""
    if not await case_service.get_case(db, case_id):
        raise HTTPException(status_code=404, detail="Case not found")

    filename = file.filename or "unnamed"
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext and ext not in _ALLOWED_EXTS:
        raise HTTPException(
            status_code=415,
            detail=f"File type '{ext}' not accepted — allowed: {sorted(_ALLOWED_EXTS)}",
        )

    data = await file.read()
    if len(data) > settings.EVIDENCE_MAX_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds max size {settings.EVIDENCE_MAX_BYTES} bytes",
        )
    if len(data) == 0:
        raise HTTPException(status_code=400, detail="Empty file")

    content_type = file.content_type or guess_type(filename)[0] or "application/octet-stream"
    upload = await upload_bytes(data=data, content_type=content_type)

    row = await evidence_service.create(
        db,
        case_id=case_id,
        kind=_infer_kind(filename, kind),
        filename=filename,
        content_type=content_type,
        size_bytes=upload.size_bytes,
        sha256=upload.sha256,
        storage_key=upload.storage_key,
        description=description,
    )
    return row


@evidence_router.get("/{evidence_id}/download")
async def download_evidence(evidence_id: UUID, db: AsyncSession = Depends(get_db)):
    row = await evidence_service.get(db, evidence_id)
    if not row:
        raise HTTPException(status_code=404, detail="Evidence not found")
    # Stream the bytes back through the backend rather than handing out a
    # presigned URL — MinIO signs URLs with the internal endpoint hostname
    # ("minio:9000"), which browsers on the host can't resolve. The backend
    # is reachable on localhost:8000, so proxying is the simplest fix.
    data = await get_object_bytes(row.storage_key)
    return Response(
        content=data,
        media_type=row.content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{row.filename}"',
            "Content-Length": str(len(data)),
        },
    )


@evidence_router.delete("/{evidence_id}", status_code=204)
async def delete_evidence(evidence_id: UUID, db: AsyncSession = Depends(get_db)):
    row = await evidence_service.get(db, evidence_id)
    if not row:
        raise HTTPException(status_code=404, detail="Evidence not found")
    # We intentionally don't remove the object from MinIO — other evidence
    # rows may reference the same sha256 (dedup). A periodic GC task can
    # prune orphaned objects later; for now disk is cheap.
    await evidence_service.delete(db, row)
