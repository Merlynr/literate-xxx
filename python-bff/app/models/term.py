from __future__ import annotations
from sqlalchemy import String, Integer, Boolean
from sqlalchemy.dialects.mysql import JSON as MySQLJSON
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import TenantModel


class Term(TenantModel):
    __tablename__ = "terms"

    type: Mapped[str] = mapped_column(String(32))  # positive, negative, prefix, brand
    content: Mapped[str] = mapped_column(String(512))
    weight: Mapped[int] = mapped_column(Integer, default=10)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    scope: Mapped[dict | None] = mapped_column(MySQLJSON, nullable=True)  # {"category_ids": [...], "style_ids": [...]}
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
