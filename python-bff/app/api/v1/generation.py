from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, model_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_tenant_id, get_current_user, get_db
from app.models.generation_asset import GenerationAsset
from app.models.generation_job import GenerationJob
from app.models.user import User
from app.services.generation_jobs import (
    MAX_SOURCE_ASSETS,
    confirm_generation_asset,
    create_generation_job,
    delete_generation_job,
    dispatch_generation_job,
    generation_asset_download_url,
    get_generation_job,
    record_job_event,
)
from app.services.job_reconciliation import maybe_recover_job

router = APIRouter()


class GenerationAssetConfirmRequest(BaseModel):
    oss_key: str = Field(..., description="Uploaded OSS object key")
    filename: str = Field(default="", description="Original filename")
    content_type: str = Field(default="application/octet-stream")
    size_bytes: int | None = Field(default=None, ge=0)
    sha256: str = Field(default="")
    asset_role: str = Field(default="source", description="source / raw / watermarked")
    oss_bucket: str | None = Field(default=None)
    width: int | None = Field(default=None, ge=1)
    height: int | None = Field(default=None, ge=1)
    extra_metadata: dict | None = Field(default=None)


class GenerationAssetResponse(BaseModel):
    asset_id: uuid.UUID
    tenant_id: uuid.UUID
    job_id: uuid.UUID | None
    asset_role: str
    oss_bucket: str
    oss_key: str
    original_filename: str
    content_type: str
    size_bytes: int | None
    sha256: str
    width: int | None
    height: int | None
    download_url: str
    download_expires_in: int = 3600
    created_at: datetime
    updated_at: datetime


class GenerationJobCreateRequest(BaseModel):
    client_request_id: str = Field(..., min_length=1, max_length=64)
    source_asset_id: uuid.UUID | None = None
    source_asset_ids: list[uuid.UUID] | None = Field(default=None, min_length=1, max_length=MAX_SOURCE_ASSETS)
    category_id: uuid.UUID | None = None
    style_id: uuid.UUID | None = None
    prompt_hint: str = Field(default="", max_length=1000)

    @model_validator(mode="after")
    def normalize_source_assets(self) -> "GenerationJobCreateRequest":
        if self.source_asset_ids:
            return self
        if self.source_asset_id:
            object.__setattr__(self, "source_asset_ids", [self.source_asset_id])
            return self
        raise ValueError("source_asset_id or source_asset_ids is required")


class GenerationJobResponse(BaseModel):
    job_id: uuid.UUID
    tenant_id: uuid.UUID
    client_request_id: str
    status: str
    provider: str
    model_name: str
    source_asset_id: uuid.UUID
    raw_result_asset_id: uuid.UUID | None
    watermarked_result_asset_id: uuid.UUID | None
    task_id: str | None
    rule_snapshot: dict
    prompt_snapshot: dict
    request_snapshot: dict
    error_code: str
    error_message: str
    raw_result_download_url: str | None = None
    watermarked_result_download_url: str | None = None
    source_preview_url: str | None = None
    source_preview_urls: list[str] | None = None
    created_at: datetime
    updated_at: datetime


def _asset_response(asset: GenerationAsset) -> GenerationAssetResponse:
    return GenerationAssetResponse(
        asset_id=asset.id,
        tenant_id=asset.tenant_id,
        job_id=asset.job_id,
        asset_role=asset.asset_role,
        oss_bucket=asset.oss_bucket,
        oss_key=asset.oss_key,
        original_filename=asset.original_filename,
        content_type=asset.content_type,
        size_bytes=asset.size_bytes,
        sha256=asset.sha256,
        width=asset.width,
        height=asset.height,
        download_url=generation_asset_download_url(asset),
        created_at=asset.created_at,
        updated_at=asset.updated_at,
    )


def _job_response(
    job: GenerationJob,
    *,
    source_preview_url: str | None = None,
    source_preview_urls: list[str] | None = None,
) -> GenerationJobResponse:
    raw_result_download_url = None
    watermarked_result_download_url = None
    return GenerationJobResponse(
        job_id=job.id,
        tenant_id=job.tenant_id,
        client_request_id=job.client_request_id,
        status=job.status,
        provider=job.provider,
        model_name=job.model_name,
        source_asset_id=job.source_asset_id,
        raw_result_asset_id=job.raw_result_asset_id,
        watermarked_result_asset_id=job.watermarked_result_asset_id,
        task_id=job.task_id,
        rule_snapshot=job.rule_snapshot,
        prompt_snapshot=job.prompt_snapshot,
        request_snapshot=job.request_snapshot,
        error_code=job.error_code,
        error_message=job.error_message,
        raw_result_download_url=raw_result_download_url,
        watermarked_result_download_url=watermarked_result_download_url,
        source_preview_url=source_preview_url,
        source_preview_urls=source_preview_urls,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


async def _source_preview_urls(db: AsyncSession, job: GenerationJob, tenant_id: uuid.UUID) -> list[str]:
    prompt_snapshot = job.prompt_snapshot or {}
    source_assets = prompt_snapshot.get("source_assets")
    if isinstance(source_assets, list) and source_assets:
        urls: list[str] = []
        for snapshot in source_assets:
            asset_id = snapshot.get("id")
            if not asset_id:
                continue
            asset = await db.get(GenerationAsset, uuid.UUID(str(asset_id)))
            if asset and asset.tenant_id == tenant_id:
                urls.append(generation_asset_download_url(asset))
        if urls:
            return urls
    source_asset = await db.get(GenerationAsset, job.source_asset_id)
    if source_asset and source_asset.tenant_id == tenant_id:
        return [generation_asset_download_url(source_asset)]
    return []


@router.post("/generation-assets/confirm", response_model=GenerationAssetResponse)
async def confirm_asset(
    req: GenerationAssetConfirmRequest,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    asset = await confirm_generation_asset(
        db,
        tenant_id=tenant_id,
        oss_key=req.oss_key,
        filename=req.filename,
        content_type=req.content_type,
        size_bytes=req.size_bytes,
        sha256=req.sha256,
        asset_role=req.asset_role,
        oss_bucket=req.oss_bucket,
        width=req.width,
        height=req.height,
        extra_metadata=req.extra_metadata,
    )
    return _asset_response(asset)


@router.post("/generation-jobs", response_model=GenerationJobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    req: GenerationJobCreateRequest,
    current_user: User = Depends(get_current_user),
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    try:
        job = await create_generation_job(
            db,
            tenant_id=tenant_id,
            user_id=current_user.id,
            client_request_id=req.client_request_id,
            source_asset_ids=req.source_asset_ids,
            category_id=req.category_id,
            style_id=req.style_id,
            prompt_hint=req.prompt_hint,
            schedule_task=False,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    await db.commit()
    dispatch_generation_job(job)
    db.add(job)
    await record_job_event(
        db,
        tenant_id=tenant_id,
        job_id=job.id,
        event_type="job.queued",
        message="Generation job queued",
        payload={
            "client_request_id": req.client_request_id,
            "source_asset_id": str(job.source_asset_id),
            "source_asset_ids": (job.request_snapshot or {}).get("source_asset_ids") or [str(job.source_asset_id)],
            "category_id": str(job.category_id) if job.category_id else None,
            "style_id": str(job.style_id) if job.style_id else None,
            "task_id": job.task_id,
        },
    )
    await db.commit()
    await db.refresh(job)
    preview_urls = await _source_preview_urls(db, job, tenant_id)
    response = _job_response(
        job,
        source_preview_url=preview_urls[0] if preview_urls else None,
        source_preview_urls=preview_urls or None,
    )
    return response


@router.get("/generation-jobs/{job_id}", response_model=GenerationJobResponse)
async def read_job(
    job_id: uuid.UUID,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    job = await get_generation_job(db, tenant_id=tenant_id, job_id=job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Generation job not found")

    recovery_action = await maybe_recover_job(db, job, trigger="poll")
    if recovery_action:
        await db.commit()
        await db.refresh(job)

    if job.raw_result_asset_id:
        raw_asset = await db.get(GenerationAsset, job.raw_result_asset_id)
        if raw_asset and raw_asset.tenant_id == tenant_id:
            job.__dict__["raw_result_asset"] = raw_asset
    if job.watermarked_result_asset_id:
        watermarked_asset = await db.get(GenerationAsset, job.watermarked_result_asset_id)
        if watermarked_asset and watermarked_asset.tenant_id == tenant_id:
            job.__dict__["watermarked_result_asset"] = watermarked_asset
    raw_result_download_url = None
    watermarked_result_download_url = None
    if job.__dict__.get("raw_result_asset"):
        raw_result_download_url = generation_asset_download_url(job.__dict__["raw_result_asset"])
    if job.__dict__.get("watermarked_result_asset"):
        watermarked_result_download_url = generation_asset_download_url(job.__dict__["watermarked_result_asset"])
    preview_urls = await _source_preview_urls(db, job, tenant_id)
    response = _job_response(
        job,
        source_preview_url=preview_urls[0] if preview_urls else None,
        source_preview_urls=preview_urls or None,
    )
    response.raw_result_download_url = raw_result_download_url
    response.watermarked_result_download_url = watermarked_result_download_url
    return response


@router.delete("/generation-jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_job(
    job_id: uuid.UUID,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    await delete_generation_job(db, tenant_id=tenant_id, job_id=job_id)
    await db.commit()
