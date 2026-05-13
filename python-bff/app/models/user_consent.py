from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, JSON, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TenantModel


class UserConsent(TenantModel):
    __tablename__ = "user_consents"
    __table_args__ = (
        UniqueConstraint("tenant_id", "user_id", "consent_type", name="uq_user_consents_tenant_user_type"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    consent_type: Mapped[str] = mapped_column(String(64), default="generation")
    consented_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    source: Mapped[str] = mapped_column(String(64), default="generation")
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
