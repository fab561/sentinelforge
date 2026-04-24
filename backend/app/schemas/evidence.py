from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class EvidenceResponse(BaseModel):
    id: UUID
    case_id: UUID
    kind: str
    filename: str
    content_type: str
    size_bytes: int
    sha256: str
    description: str | None
    uploaded_by: UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}


class EvidenceListResponse(BaseModel):
    items: list[EvidenceResponse]
    total: int
