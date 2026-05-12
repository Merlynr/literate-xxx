from __future__ import annotations
import uuid
from datetime import datetime
from sqlalchemy import DateTime, String, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    openid: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    nickname: Mapped[str] = mapped_column(String(128), default="")
    avatar_url: Mapped[str] = mapped_column(String(512), default="")
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    tenant = relationship("Tenant", lazy="joined")
