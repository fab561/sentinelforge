import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class IOC(Base):
    __tablename__ = "iocs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # value is exact-match — case folded to lowercase on write so lookups
    # don't need a functional index. ip / hash / domain / url all behave
    # the same way at this layer.
    value: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    ioc_type: Mapped[str] = mapped_column(String(20), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="medium")

    # Where it came from — "manual", or a feed name. Lets us filter the
    # /iocs UI between analyst-curated and feed-imported entries.
    source: Mapped[str] = mapped_column(String(60), nullable=False, default="manual")
    description: Mapped[str | None] = mapped_column(Text)

    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Optional auto-expiry — Wazuh enrichment skips entries past their TTL,
    # which is how feeds avoid stale-IP false positives at scale.
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
