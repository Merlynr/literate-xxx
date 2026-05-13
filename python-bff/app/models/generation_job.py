from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TenantModel


class GenerationJob(TenantModel):
    __tablename__ = "generation_jobs"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "client_request_id",
            name="uq_generation_jobs_tenant_client_request_id",
        ),
    )

    client_request_id: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32), default="queued", index=True)
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("categories.id"),
        nullable=True,
        index=True,
    )
    style_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("styles.id"),
        nullable=True,
        index=True,
    )
    source_asset_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("generation_assets.id"),
        index=True,
    )
    raw_result_asset_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("generation_assets.id"),
        nullable=True,
        index=True,
    )
    watermarked_result_asset_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("generation_assets.id"),
        nullable=True,
        index=True,
    )
    task_id: Mapped[str | None] = mapped_column(String(128), nullable=True, unique=True, index=True)
    provider: Mapped[str] = mapped_column(String(64), default="wanxiang")
    model_name: Mapped[str] = mapped_column(String(64), default="wan2.7-image")
    rule_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    prompt_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    request_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    error_code: Mapped[str] = mapped_column(String(64), default="")
    error_message: Mapped[str] = mapped_column(String(1024), default="")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
