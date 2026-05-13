from __future__ import annotations

import uuid

from sqlalchemy import Integer, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TenantModel


class GenerationAsset(TenantModel):
    __tablename__ = "generation_assets"
    __table_args__ = (
        UniqueConstraint("tenant_id", "oss_key_digest", name="uq_generation_assets_tenant_oss_key_digest"),
    )

    job_id: Mapped[uuid.UUID | None] = mapped_column(index=True, nullable=True)
    asset_role: Mapped[str] = mapped_column(String(32), default="source")
    oss_bucket: Mapped[str] = mapped_column(String(128))
    oss_key: Mapped[str] = mapped_column(String(1024))
    oss_key_digest: Mapped[str] = mapped_column(String(64))
    original_filename: Mapped[str] = mapped_column(String(256), default="")
    content_type: Mapped[str] = mapped_column(String(128), default="application/octet-stream")
    size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sha256: Mapped[str] = mapped_column(String(64), default="")
    etag: Mapped[str] = mapped_column(String(128), default="")
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    extra_metadata: Mapped[dict | None] = mapped_column("extra_metadata", JSON, nullable=True)
