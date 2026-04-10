from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class Observables(BaseModel):
    source_ip: str | None = None
    destination_ip: str | None = None
    source_port: int | None = None
    destination_port: int | None = None
    username: str | None = None
    hostname: str | None = None
    file_hash: str | None = None
    domain: str | None = None
    url: str | None = None
    process_name: str | None = None


class MitreInfo(BaseModel):
    tactic: str | None = None
    technique: str | None = None
    subtechnique: str | None = None


class AlertBase(BaseModel):
    alert_id: str
    timestamp: datetime
    source: str = "wazuh"
    source_rule_id: str | None = None
    severity: str
    category: str | None = None
    title: str
    description: str | None = None
    observables: dict = Field(default_factory=dict)
    mitre: dict | None = None
    raw_log: str | None = None


class AlertResponse(AlertBase):
    id: UUID
    enrichment: dict | None = None
    threat_score: int | None = None
    verdict: str | None = None
    playbook_actions: list = Field(default_factory=list)
    case_id: UUID | None = None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AlertUpdate(BaseModel):
    """Used by Module 2 (enrichment) and Module 3 (playbook actions)."""
    enrichment: dict | None = None
    threat_score: int | None = None
    verdict: str | None = None
    playbook_actions: list | None = None
    status: str | None = None
    case_id: UUID | None = None


class AlertListResponse(BaseModel):
    items: list[AlertResponse]
    total: int
    page: int
    page_size: int
