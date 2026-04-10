from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class RuleCreate(BaseModel):
    name: str
    description: str | None = None
    rule_type: str = "sigma"
    definition: dict
    severity: str | None = None
    mitre_techniques: list[str] | None = None


class RuleUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    definition: dict | None = None
    severity: str | None = None
    enabled: bool | None = None
    mitre_techniques: list[str] | None = None


class RuleResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    rule_type: str
    definition: dict
    severity: str | None
    enabled: bool
    mitre_techniques: list[str] | None
    created_by: UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}


class RuleListResponse(BaseModel):
    items: list[RuleResponse]
    total: int
