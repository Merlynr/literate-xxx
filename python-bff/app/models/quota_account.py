from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TenantModel


class QuotaAccount(TenantModel):
    __tablename__ = "quota_accounts"

    total_units: Mapped[int] = mapped_column(Integer, default=0)
    available_units: Mapped[int] = mapped_column(Integer, default=0)
    frozen_units: Mapped[int] = mapped_column(Integer, default=0)
    active_plan_id: Mapped[int | None] = mapped_column(
        ForeignKey("pricing_plans.id"),
        nullable=True,
        index=True,
    )
