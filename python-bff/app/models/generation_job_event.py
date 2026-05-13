from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TenantModel


class GenerationJobEvent(TenantModel):
    __tablename__ = "generation_job_events"

    job_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("generation_jobs.id"),
        index=True,
    )
    event_type: Mapped[str] = mapped_column(String(64), index=True)
    message: Mapped[str] = mapped_column(String(512), default="")
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
