from __future__ import annotations

import hashlib
import uuid
from datetime import datetime
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.category import Category
from app.models.generation_asset import GenerationAsset
from app.models.generation_job import GenerationJob
from app.models.generation_job_event import GenerationJobEvent
from app.models.promo_rule import PromoRule
from app.models.style import Style
from app.services.privacy_service import has_generation_privacy_agreement
from app.services.quota_service import freeze_quota, release_quota, release_quota
from app.services.oss import generate_presigned_download_url
from app.workers.celery_app import celery_app

MAX_SOURCE_ASSETS = 6


def dispatch_generation_job(job: GenerationJob) -> str:
    result = celery_app.send_task("generation.process", kwargs={"job_id": str(job.id)})
    job.task_id = result.id
    return result.id


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def _oss_key_digest(oss_key: str) -> str:
    return hashlib.sha256(oss_key.encode("utf-8")).hexdigest()


def _asset_snapshot(asset: GenerationAsset) -> dict[str, Any]:
    return {
        "id": str(asset.id),
        "tenant_id": str(asset.tenant_id),
        "asset_role": asset.asset_role,
        "oss_bucket": asset.oss_bucket,
        "oss_key": asset.oss_key,
        "original_filename": asset.original_filename,
        "content_type": asset.content_type,
        "size_bytes": asset.size_bytes,
        "sha256": asset.sha256,
        "etag": asset.etag,
        "width": asset.width,
        "height": asset.height,
        "extra_metadata": _json_safe(asset.extra_metadata) if asset.extra_metadata is not None else None,
    }


def _category_snapshot(category: Category | None) -> dict[str, Any] | None:
    if not category:
        return None
    return {
        "id": str(category.id),
        "tenant_id": str(category.tenant_id),
        "category_code": category.category_code,
        "name": category.name,
        "sort_order": category.sort_order,
        "is_active": category.is_active,
    }


def _style_snapshot(style: Style | None) -> dict[str, Any] | None:
    if not style:
        return None
    return {
        "id": str(style.id),
        "tenant_id": str(style.tenant_id),
        "name": style.name,
        "cover_image_url": style.cover_image_url,
        "rule_version": style.rule_version,
        "sort_order": style.sort_order,
        "is_active": style.is_active,
    }


def _promo_rule_snapshot(rule: PromoRule | None) -> dict[str, Any]:
    if not rule:
        return {
            "id": None,
            "version": 0,
            "is_active": True,
            "slot_template": None,
            "term_selection_strategy": "weighted_random",
            "aspect_ratio": "1:1",
            "watermark_config": None,
        }
    return {
        "id": str(rule.id),
        "tenant_id": str(rule.tenant_id),
        "name": rule.name,
        "slot_template": _json_safe(rule.slot_template) if rule.slot_template is not None else None,
        "term_selection_strategy": rule.term_selection_strategy,
        "aspect_ratio": rule.aspect_ratio,
        "watermark_config": _json_safe(rule.watermark_config) if rule.watermark_config is not None else None,
        "version": rule.version,
        "is_active": rule.is_active,
    }


async def record_job_event(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    job_id: uuid.UUID,
    event_type: str,
    message: str = "",
    payload: dict[str, Any] | None = None,
) -> GenerationJobEvent:
    event = GenerationJobEvent(
        tenant_id=tenant_id,
        job_id=job_id,
        event_type=event_type,
        message=message,
        payload=_json_safe(payload) if payload is not None else None,
    )
    db.add(event)
    await db.flush()
    return event


async def confirm_generation_asset(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    oss_key: str,
    filename: str,
    content_type: str,
    size_bytes: int | None = None,
    sha256: str = "",
    asset_role: str = "source",
    oss_bucket: str | None = None,
    width: int | None = None,
    height: int | None = None,
    extra_metadata: dict[str, Any] | None = None,
) -> GenerationAsset:
    oss_key_digest = _oss_key_digest(oss_key)
    existing = await db.scalar(
        select(GenerationAsset).where(
            GenerationAsset.tenant_id == tenant_id,
            GenerationAsset.oss_key_digest == oss_key_digest,
        )
    )
    if existing:
        return existing

    asset = GenerationAsset(
        tenant_id=tenant_id,
        asset_role=asset_role,
        oss_bucket=oss_bucket or settings.S3_BUCKET,
        oss_key=oss_key,
        oss_key_digest=oss_key_digest,
        original_filename=filename,
        content_type=content_type,
        size_bytes=size_bytes,
        sha256=sha256,
        width=width,
        height=height,
        extra_metadata=_json_safe(extra_metadata) if extra_metadata is not None else None,
    )
    db.add(asset)
    await db.flush()
    await db.refresh(asset)
    return asset


async def _load_category(db: AsyncSession, tenant_id: uuid.UUID, category_id: uuid.UUID | None) -> Category | None:
    if not category_id:
        return None
    return await db.scalar(
        select(Category).where(Category.tenant_id == tenant_id, Category.id == category_id)
    )


async def _load_style(db: AsyncSession, tenant_id: uuid.UUID, style_id: uuid.UUID | None) -> Style | None:
    if not style_id:
        return None
    return await db.scalar(
        select(Style).where(Style.tenant_id == tenant_id, Style.id == style_id)
    )


async def _load_source_asset(db: AsyncSession, tenant_id: uuid.UUID, source_asset_id: uuid.UUID) -> GenerationAsset:
    asset = await db.scalar(
        select(GenerationAsset).where(
            GenerationAsset.tenant_id == tenant_id,
            GenerationAsset.id == source_asset_id,
        )
    )
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source asset not found")
    return asset


def _dedupe_source_asset_ids(source_asset_ids: list[uuid.UUID]) -> list[uuid.UUID]:
    seen: set[uuid.UUID] = set()
    ordered: list[uuid.UUID] = []
    for asset_id in source_asset_ids:
        if asset_id in seen:
            continue
        seen.add(asset_id)
        ordered.append(asset_id)
    return ordered


async def _load_source_assets(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    source_asset_ids: list[uuid.UUID],
) -> list[GenerationAsset]:
    assets: list[GenerationAsset] = []
    for asset_id in source_asset_ids:
        assets.append(await _load_source_asset(db, tenant_id, asset_id))
    return assets


async def _load_active_rule(db: AsyncSession, tenant_id: uuid.UUID) -> PromoRule | None:
    return await db.scalar(
        select(PromoRule)
        .where(PromoRule.tenant_id == tenant_id, PromoRule.is_active.is_(True))
        .order_by(PromoRule.version.desc(), PromoRule.created_at.desc())
    )


async def create_generation_job(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID | None = None,
    client_request_id: str,
    source_asset_id: uuid.UUID | None = None,
    source_asset_ids: list[uuid.UUID] | None = None,
    category_id: uuid.UUID | None = None,
    style_id: uuid.UUID | None = None,
    prompt_hint: str = "",
    schedule_task: bool = True,
) -> GenerationJob:
    normalized_source_asset_ids = _dedupe_source_asset_ids(
        source_asset_ids or ([source_asset_id] if source_asset_id else [])
    )
    if not normalized_source_asset_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one source asset is required",
        )
    if len(normalized_source_asset_ids) > MAX_SOURCE_ASSETS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"At most {MAX_SOURCE_ASSETS} source images are allowed",
        )
    primary_source_asset_id = normalized_source_asset_ids[0]
    request_snapshot = {
        "client_request_id": client_request_id,
        "source_asset_id": str(primary_source_asset_id),
        "source_asset_ids": [str(asset_id) for asset_id in normalized_source_asset_ids],
        "category_id": str(category_id) if category_id else None,
        "style_id": str(style_id) if style_id else None,
        "prompt_hint": prompt_hint,
    }
    existing = await db.scalar(
        select(GenerationJob).where(
            GenerationJob.tenant_id == tenant_id,
            GenerationJob.client_request_id == client_request_id,
        )
    )
    if existing:
        if existing.request_snapshot != request_snapshot:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="client_request_id already exists with different payload",
            )
        if schedule_task and not existing.task_id:
            dispatch_generation_job(existing)
            await record_job_event(
                db,
                tenant_id=tenant_id,
                job_id=existing.id,
                event_type="job.queued",
                message="Generation job re-queued",
                payload={
                    "client_request_id": client_request_id,
                    "source_asset_id": str(existing.source_asset_id),
                    "category_id": str(existing.category_id) if existing.category_id else None,
                    "style_id": str(existing.style_id) if existing.style_id else None,
                    "task_id": existing.task_id,
                },
            )
        await db.refresh(existing)
        return existing

    source_assets = await _load_source_assets(db, tenant_id, normalized_source_asset_ids)
    category = await _load_category(db, tenant_id, category_id)
    style = await _load_style(db, tenant_id, style_id)
    active_rule = await _load_active_rule(db, tenant_id)
    if user_id and not await has_generation_privacy_agreement(db, tenant_id=tenant_id, user_id=user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please accept the generation privacy agreement first",
        )

    source_asset_snapshots = [_asset_snapshot(asset) for asset in source_assets]
    prompt_snapshot = {
        "source_assets": source_asset_snapshots,
        "source_asset": source_asset_snapshots[0],
        "category": _category_snapshot(category),
        "style": _style_snapshot(style),
        "prompt_hint": prompt_hint,
    }
    rule_snapshot = _promo_rule_snapshot(active_rule)
    from app.services.term_selection import resolve_terms_for_generation

    resolved_terms = await resolve_terms_for_generation(
        db,
        tenant_id=tenant_id,
        category_id=category.id if category else None,
        style_id=style.id if style else None,
        strategy=str(rule_snapshot.get("term_selection_strategy") or "weighted_random"),
        seed=client_request_id,
    )
    prompt_snapshot["resolved_terms"] = resolved_terms
    rule_snapshot["provider"] = "alibaba-dashscope"
    rule_snapshot["model_name"] = "wan2.7-image"
    rule_snapshot["watermark_policy"] = "separate_oss_assets"
    job_id = uuid.uuid4()
    await freeze_quota(
        db,
        tenant_id=tenant_id,
        job_id=job_id,
        units=1,
        reason="generation.job.create",
    )

    job = GenerationJob(
        id=job_id,
        tenant_id=tenant_id,
        client_request_id=client_request_id,
        status="queued",
        category_id=category.id if category else None,
        style_id=style.id if style else None,
        source_asset_id=primary_source_asset_id,
        provider="alibaba-dashscope",
        model_name="wan2.7-image",
        rule_snapshot=rule_snapshot,
        prompt_snapshot=prompt_snapshot,
        request_snapshot=request_snapshot,
    )
    db.add(job)
    await db.flush()
    await db.refresh(job)

    if schedule_task:
        dispatch_generation_job(job)

    await record_job_event(
        db,
        tenant_id=tenant_id,
        job_id=job.id,
        event_type="job.queued",
        message="Generation job queued",
        payload={
            "client_request_id": client_request_id,
            "source_asset_id": str(primary_source_asset_id),
            "source_asset_ids": [str(asset_id) for asset_id in normalized_source_asset_ids],
            "category_id": str(category.id) if category else None,
            "style_id": str(style.id) if style else None,
            "task_id": job.task_id,
        },
    )
    await db.refresh(job)
    return job


async def get_generation_job(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    job_id: uuid.UUID,
) -> GenerationJob | None:
    return await db.scalar(
        select(GenerationJob).where(
            GenerationJob.tenant_id == tenant_id,
            GenerationJob.id == job_id,
        )
    )


_DELETABLE_JOB_STATUSES = frozenset({"queued", "failed", "succeeded"})


async def delete_generation_job(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    job_id: uuid.UUID,
) -> None:
    job = await get_generation_job(db, tenant_id=tenant_id, job_id=job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Generation job not found")
    if job.status == "running":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="任务正在生成中，请稍后再删除",
        )
    if job.status not in _DELETABLE_JOB_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"当前状态无法删除: {job.status}",
        )

    if job.status in ("queued", "failed", "succeeded"):
        try:
            await release_quota(
                db,
                tenant_id=tenant_id,
                job_id=job.id,
                units=1,
                reason="generation.job.deleted",
            )
        except HTTPException:
            pass

    await db.execute(
        delete(GenerationJobEvent).where(
            GenerationJobEvent.job_id == job.id,
            GenerationJobEvent.tenant_id == tenant_id,
        )
    )
    await db.delete(job)
    await db.flush()


def generation_asset_download_url(asset: GenerationAsset) -> str:
    return generate_presigned_download_url(asset.oss_key)
