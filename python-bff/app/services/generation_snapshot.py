from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping
import uuid

from app.models.category import Category
from app.models.generation_asset import GenerationAsset
from app.models.generation_job import GenerationJob
from app.models.style import Style
from app.services.generation_jobs import generation_asset_download_url
from app.services.oss import generate_presigned_download_url


def freeze_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): freeze_json(item) for key, item in value.items()}
    if isinstance(value, list):
        return [freeze_json(item) for item in value]
    if isinstance(value, tuple):
        return [freeze_json(item) for item in value]
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if hasattr(value, "isoformat") and callable(getattr(value, "isoformat")):
        try:
            return value.isoformat()
        except Exception:
            pass
    return value


def snapshot_mapping(value: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if value is None:
        return None
    return freeze_json(dict(value))


@dataclass(frozen=True)
class FrozenGenerationJobSnapshot:
    job: dict[str, Any]
    source_asset: dict[str, Any]


@dataclass(frozen=True)
class GenerationContext:
    job_id: uuid.UUID
    tenant_id: uuid.UUID
    client_request_id: str
    source_asset_id: uuid.UUID
    source_image_url: str
    style_id: uuid.UUID | None
    style_image_url: str | None
    category_id: uuid.UUID | None
    category_name: str | None
    style_name: str | None
    rule_snapshot: dict[str, Any]
    prompt_snapshot: dict[str, Any]
    watermark_text: str


def build_job_snapshot(job: Any) -> dict[str, Any]:
    return {
        "id": str(job.id),
        "tenant_id": str(job.tenant_id),
        "client_request_id": job.client_request_id,
        "status": job.status,
        "category_id": str(job.category_id) if getattr(job, "category_id", None) else None,
        "style_id": str(job.style_id) if getattr(job, "style_id", None) else None,
        "source_asset_id": str(job.source_asset_id),
        "raw_result_asset_id": str(job.raw_result_asset_id) if getattr(job, "raw_result_asset_id", None) else None,
        "watermarked_result_asset_id": (
            str(job.watermarked_result_asset_id) if getattr(job, "watermarked_result_asset_id", None) else None
        ),
        "task_id": job.task_id,
        "provider": job.provider,
        "model_name": job.model_name,
        "rule_snapshot": snapshot_mapping(job.rule_snapshot) or {},
        "prompt_snapshot": snapshot_mapping(job.prompt_snapshot) or {},
        "request_snapshot": snapshot_mapping(job.request_snapshot) or {},
        "error_code": job.error_code,
        "error_message": job.error_message,
        "started_at": freeze_json(job.started_at),
        "finished_at": freeze_json(job.finished_at),
        "created_at": freeze_json(job.created_at),
        "updated_at": freeze_json(job.updated_at),
    }


def build_asset_snapshot(asset: Any) -> dict[str, Any]:
    return {
        "id": str(asset.id),
        "tenant_id": str(asset.tenant_id),
        "job_id": str(asset.job_id) if getattr(asset, "job_id", None) else None,
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
        "extra_metadata": snapshot_mapping(asset.extra_metadata),
        "created_at": freeze_json(asset.created_at),
        "updated_at": freeze_json(asset.updated_at),
    }


def _category_snapshot(category: Any | None) -> dict[str, Any] | None:
    if category is None:
        return None
    return {
        "id": str(getattr(category, "id", "")),
        "tenant_id": str(getattr(category, "tenant_id", "")),
        "category_code": getattr(category, "category_code", ""),
        "name": getattr(category, "name", ""),
        "sort_order": getattr(category, "sort_order", 0),
        "is_active": getattr(category, "is_active", True),
    }


def _style_snapshot(style: Any | None) -> dict[str, Any] | None:
    if style is None:
        return None
    return {
        "id": str(getattr(style, "id", "")),
        "tenant_id": str(getattr(style, "tenant_id", "")),
        "name": getattr(style, "name", ""),
        "cover_image_url": getattr(style, "cover_image_url", ""),
        "rule_version": getattr(style, "rule_version", 1),
        "sort_order": getattr(style, "sort_order", 0),
        "is_active": getattr(style, "is_active", True),
    }


def freeze_generation_job_context(job: Any, source_asset: Any) -> FrozenGenerationJobSnapshot:
    return FrozenGenerationJobSnapshot(job=build_job_snapshot(job), source_asset=build_asset_snapshot(source_asset))


def build_generation_context(
    job: GenerationJob,
    source_asset: GenerationAsset,
    *,
    category: Category | None = None,
    style: Style | None = None,
) -> GenerationContext:
    rule_snapshot = snapshot_mapping(job.rule_snapshot) or {}
    prompt_snapshot = snapshot_mapping(job.prompt_snapshot) or {}
    watermark_config = rule_snapshot.get("watermark_config") or {}
    watermark_text = str(watermark_config.get("text") or watermark_config.get("label") or "XXZX")
    style_image_url: str | None = None
    if style and style.cover_image_url:
        style_image_url = style.cover_image_url
        if not style_image_url.startswith("http://") and not style_image_url.startswith("https://"):
            style_image_url = generate_presigned_download_url(style_image_url)
    return GenerationContext(
        job_id=job.id,
        tenant_id=job.tenant_id,
        client_request_id=job.client_request_id,
        source_asset_id=source_asset.id,
        source_image_url=generation_asset_download_url(source_asset),
        style_id=style.id if style else None,
        style_image_url=style_image_url,
        category_id=category.id if category else None,
        category_name=category.name if category else None,
        style_name=style.name if style else None,
        rule_snapshot=rule_snapshot,
        prompt_snapshot=prompt_snapshot,
        watermark_text=watermark_text,
    )
