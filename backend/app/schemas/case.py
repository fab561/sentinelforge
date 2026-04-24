from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class CaseCreate(BaseModel):
    title: str
    description: str | None = None
    severity: str | None = None
    assigned_to: UUID | None = None
    alert_ids: list[str] = []  # alert_ids to link


class CaseUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    severity: str | None = None
    status: str | None = None
    assigned_to: UUID | None = None


class CaseResponse(BaseModel):
    id: UUID
    case_number: str
    title: str
    description: str | None
    severity: str | None
    status: str
    assigned_to: UUID | None
    created_by: UUID | None
    created_at: datetime
    updated_at: datetime
    acknowledged_at: datetime | None = None
    resolved_at: datetime | None = None
    closed_at: datetime | None = None

    model_config = {"from_attributes": True}


class CaseListResponse(BaseModel):
    items: list[CaseResponse]
    total: int
    page: int
    page_size: int
