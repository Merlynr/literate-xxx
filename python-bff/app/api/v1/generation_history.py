from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_tenant_id, get_db
from app.models.category import Category
from app.models.generation_asset import GenerationAsset
from app.models.generation_job import GenerationJob
from app.models.style import Style
from app.services.generation_history import list_generation_jobs
from app.services.generation_jobs import generation_asset_download_url

router = APIRouter(prefix="/generation-history", tags=["generation-history"])


class GenerationHistoryItem(BaseModel):
    job_id: uuid.UUID
    status: str
    created_at: datetime
    updated_at: datetime
    category_id: uuid.UUID | None = None
    category_name: str = ""
    style_id: uuid.UUID | None = None
    style_name: str = ""
    prompt_hint: str = ""
    source_preview_url: str | None = None
    raw_result_download_url: str | None = None
    watermarked_result_download_url: str | None = None
    error_message: str = ""


def _snapshot_names(job: GenerationJob) -> tuple[str, str, str]:
    category = job.prompt_snapshot.get("category") if isinstance(job.prompt_snapshot, dict) else None
    style = job.prompt_snapshot.get("style") if isinstance(job.prompt_snapshot, dict) else None
    category_name = category.get("name", "") if isinstance(category, dict) else ""
    style_name = style.get("name", "") if isinstance(style, dict) else ""
    prompt_hint = ""
    if isinstance(job.request_snapshot, dict):
        prompt_hint = str(job.request_snapshot.get("prompt_hint") or "").strip()
    if not prompt_hint and isinstance(job.prompt_snapshot, dict):
        prompt_hint = str(job.prompt_snapshot.get("prompt_hint") or "").strip()
    return category_name, style_name, prompt_hint


async def _resolve_job_meta(
    db: AsyncSession,
    job: GenerationJob,
) -> tuple[str, str, str]:
    """Read category/style/hint from snapshot, fall back to related rows."""
    category_name, style_name, prompt_hint = _snapshot_names(job)
    if not category_name and job.category_id:
        category = await db.get(Category, job.category_id)
        if category and category.tenant_id == job.tenant_id:
            category_name = category.name
    if not style_name and job.style_id:
        style = await db.get(Style, job.style_id)
        if style and style.tenant_id == job.tenant_id:
            style_name = style.name
    return category_name, style_name, prompt_hint


@router.get("", response_model=list[GenerationHistoryItem])
async def generation_history(
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: str | None = Query(default=None, description="Filter by job status, e.g. succeeded"),
    db: AsyncSession = Depends(get_db),
):
    jobs = await list_generation_jobs(
        db, tenant_id=tenant_id, offset=offset, limit=limit, status=status
    )
    items: list[GenerationHistoryItem] = []
    for job in jobs:
        source_asset = await db.get(GenerationAsset, job.source_asset_id)
        raw_asset = await db.get(GenerationAsset, job.raw_result_asset_id) if job.raw_result_asset_id else None
        watermarked_asset = await db.get(GenerationAsset, job.watermarked_result_asset_id) if job.watermarked_result_asset_id else None
        category_name, style_name, prompt_hint = await _resolve_job_meta(db, job)
        items.append(
            GenerationHistoryItem(
                job_id=job.id,
                status=job.status,
                created_at=job.created_at,
                updated_at=job.updated_at,
                category_id=job.category_id,
                category_name=category_name,
                style_id=job.style_id,
                style_name=style_name,
                prompt_hint=prompt_hint,
                source_preview_url=generation_asset_download_url(source_asset) if source_asset else None,
                raw_result_download_url=generation_asset_download_url(raw_asset) if raw_asset else None,
                watermarked_result_download_url=generation_asset_download_url(watermarked_asset) if watermarked_asset else None,
                error_message=job.error_message,
            )
        )
    return items
