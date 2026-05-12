from __future__ import annotations
from sqlalchemy import String, Integer, Boolean
from sqlalchemy.dialects.mysql import JSON as MySQLJSON
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import TenantModel


class PromoRule(TenantModel):
    __tablename__ = "promo_rules"

    name: Mapped[str] = mapped_column(String(128))
    slot_template: Mapped[dict | None] = mapped_column(MySQLJSON, nullable=True)
    term_selection_strategy: Mapped[str] = mapped_column(String(64), default="weighted_random")
    aspect_ratio: Mapped[str] = mapped_column(String(16), default="1:1")
    watermark_config: Mapped[dict | None] = mapped_column(MySQLJSON, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
