import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Alert(TimestampMixin, Base):
    __tablename__ = "alerts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    alert_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source: Mapped[str] = mapped_column(String(50), default="wazuh")
    source_rule_id: Mapped[str | None] = mapped_column(String(50))
    severity: Mapped[str] = mapped_column(String(20), nullable=False)  # low, medium, high, critical
    category: Mapped[str | None] = mapped_column(String(50))
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    # Flexible JSONB fields
    observables: Mapped[dict] = mapped_column(JSONB, default=dict)
    enrichment: Mapped[dict | None] = mapped_column(JSONB)
    threat_score: Mapped[int | None] = mapped_column(Integer)
    verdict: Mapped[str | None] = mapped_column(String(20))  # benign, suspicious, malicious
    playbook_actions: Mapped[list] = mapped_column(JSONB, default=list)
    mitre: Mapped[dict | None] = mapped_column(JSONB)
    raw_log: Mapped[str | None] = mapped_column(Text)

    # Status tracking
    status: Mapped[str] = mapped_column(String(20), default="new")  # new, enriched, closed, escalated

    # Case link
    case_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id"), nullable=True
    )
