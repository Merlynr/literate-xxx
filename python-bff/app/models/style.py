from __future__ import annotations
from sqlalchemy import String, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import TenantModel


class Style(TenantModel):
    __tablename__ = "styles"

    name: Mapped[str] = mapped_column(String(128))
    cover_image_url: Mapped[str] = mapped_column(String(512), default="")
    rule_version: Mapped[int] = mapped_column(Integer, default=1)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
