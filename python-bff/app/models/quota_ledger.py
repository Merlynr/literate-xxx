from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Integer, String, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TenantModel


class QuotaLedgerEntry(TenantModel):
    __tablename__ = "quota_ledger_entries"

    job_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True, index=True)
    plan_id: Mapped[int | None] = mapped_column(
        ForeignKey("pricing_plans.id"),
        nullable=True,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(String(32), index=True)
    delta_units: Mapped[int] = mapped_column(Integer, default=0)
    available_before: Mapped[int] = mapped_column(Integer, default=0)
    available_after: Mapped[int] = mapped_column(Integer, default=0)
    frozen_before: Mapped[int] = mapped_column(Integer, default=0)
    frozen_after: Mapped[int] = mapped_column(Integer, default=0)
    reason: Mapped[str] = mapped_column(String(256), default="")
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
