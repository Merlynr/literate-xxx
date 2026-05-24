from __future__ import annotations

import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.generation_asset import GenerationAsset
from app.models.generation_job import GenerationJob


async def list_generation_jobs(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    offset: int = 0,
    limit: int = 20,
    status: str | None = None,
) -> list[GenerationJob]:
    stmt = (
        select(GenerationJob)
        .where(GenerationJob.tenant_id == tenant_id)
        .order_by(GenerationJob.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    if status:
        stmt = stmt.where(GenerationJob.status == status)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def load_asset_map(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    asset_ids: list[uuid.UUID],
) -> dict[uuid.UUID, GenerationAsset]:
    if not asset_ids:
        return {}
    result = await db.execute(
        select(GenerationAsset).where(
            GenerationAsset.tenant_id == tenant_id,
            GenerationAsset.id.in_(asset_ids),
        )
    )
    return {asset.id: asset for asset in result.scalars().all()}
