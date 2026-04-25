from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class IOCCreate(BaseModel):
    value: str = Field(min_length=1, max_length=500)
    ioc_type: str = Field(pattern="^(ip|domain|hash|url)$")
    severity: str = Field(default="medium", pattern="^(low|medium|high|critical)$")
    source: str = Field(default="manual", max_length=60)
    description: str | None = None
    enabled: bool = True
    expires_at: datetime | None = None


class IOCUpdate(BaseModel):
    severity: str | None = Field(default=None, pattern="^(low|medium|high|critical)$")
    source: str | None = None
    description: str | None = None
    enabled: bool | None = None
    expires_at: datetime | None = None


class IOCResponse(BaseModel):
    id: UUID
    value: str
    ioc_type: str
    severity: str
    source: str
    description: str | None
    enabled: bool
    expires_at: datetime | None
    created_by: UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}


class IOCListResponse(BaseModel):
    items: list[IOCResponse]
    total: int
