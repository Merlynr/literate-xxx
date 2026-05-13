from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_tenant_id, get_db
from app.models.generation_asset import GenerationAsset
from app.services.generation_history import list_generation_jobs
from app.services.generation_jobs import generation_asset_download_url

router = APIRouter(prefix="/generation-history", tags=["generation-history"])


class GenerationHistoryItem(BaseModel):
    job_id: uuid.UUID
    status: str
    created_at: datetime
    updated_at: datetime
    source_preview_url: str | None = None
    raw_result_download_url: str | None = None
    watermarked_result_download_url: str | None = None
    error_message: str = ""


@router.get("", response_model=list[GenerationHistoryItem])
async def generation_history(
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    jobs = await list_generation_jobs(db, tenant_id=tenant_id, offset=offset, limit=limit)
    items: list[GenerationHistoryItem] = []
    for job in jobs:
        source_asset = await db.get(GenerationAsset, job.source_asset_id)
        raw_asset = await db.get(GenerationAsset, job.raw_result_asset_id) if job.raw_result_asset_id else None
        watermarked_asset = await db.get(GenerationAsset, job.watermarked_result_asset_id) if job.watermarked_result_asset_id else None
        items.append(
            GenerationHistoryItem(
                job_id=job.id,
                status=job.status,
                created_at=job.created_at,
                updated_at=job.updated_at,
                source_preview_url=generation_asset_download_url(source_asset) if source_asset else None,
                raw_result_download_url=generation_asset_download_url(raw_asset) if raw_asset else None,
                watermarked_result_download_url=generation_asset_download_url(watermarked_asset) if watermarked_asset else None,
                error_message=job.error_message,
            )
        )
    return items
