from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import mimetypes
from typing import Any, Mapping
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.generation_asset import GenerationAsset
from app.services.oss import upload_bytes
import httpx


@dataclass(frozen=True)
class GenerationResultAssets:
    raw_asset: GenerationAsset
    watermarked_asset: GenerationAsset


def download_image_bytes(url: str, *, timeout: float = 120.0) -> bytes:
    response = httpx.get(url, timeout=timeout, follow_redirects=True)
    response.raise_for_status()
    return response.content


def _extension_for_content_type(content_type: str) -> str:
    ext = mimetypes.guess_extension(content_type.split(";", 1)[0].strip())
    return ext or ".png"


def build_result_oss_key(
    *,
    tenant_id: uuid.UUID,
    job_id: uuid.UUID,
    asset_role: str,
    content_type: str,
) -> str:
    ext = _extension_for_content_type(content_type)
    return f"generation/{tenant_id}/{job_id}/{asset_role}{ext}"


def hash_bytes(content: bytes) -> str:
    return sha256(content).hexdigest()


def hash_oss_key(oss_key: str) -> str:
    return sha256(oss_key.encode("utf-8")).hexdigest()


async def persist_generation_result_asset(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    job_id: uuid.UUID,
    asset_role: str,
    content: bytes,
    content_type: str,
    original_filename: str,
    extra_metadata: Mapping[str, Any] | None = None,
    width: int | None = None,
    height: int | None = None,
) -> GenerationAsset:
    oss_key = build_result_oss_key(
        tenant_id=tenant_id,
        job_id=job_id,
        asset_role=asset_role,
        content_type=content_type,
    )
    upload_bytes(content, oss_key, content_type=content_type)
    asset = GenerationAsset(
        tenant_id=tenant_id,
        job_id=job_id,
        asset_role=asset_role,
        oss_bucket=settings.S3_BUCKET,
        oss_key=oss_key,
        oss_key_digest=hash_oss_key(oss_key),
        original_filename=original_filename,
        content_type=content_type,
        size_bytes=len(content),
        sha256=hash_bytes(content),
        etag="",
        width=width,
        height=height,
        extra_metadata=dict(extra_metadata) if extra_metadata is not None else None,
    )
    db.add(asset)
    await db.flush()
    await db.refresh(asset)
    return asset


async def persist_generation_result_assets(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    job_id: uuid.UUID,
    raw_content: bytes,
    raw_content_type: str,
    watermarked_content: bytes,
    watermarked_content_type: str,
    raw_metadata: Mapping[str, Any] | None = None,
    watermarked_metadata: Mapping[str, Any] | None = None,
    width: int | None = None,
    height: int | None = None,
) -> GenerationResultAssets:
    raw_asset = await persist_generation_result_asset(
        db,
        tenant_id=tenant_id,
        job_id=job_id,
        asset_role="raw",
        content=raw_content,
        content_type=raw_content_type,
        original_filename="raw" + _extension_for_content_type(raw_content_type),
        extra_metadata=raw_metadata,
        width=width,
        height=height,
    )
    watermarked_asset = await persist_generation_result_asset(
        db,
        tenant_id=tenant_id,
        job_id=job_id,
        asset_role="watermarked",
        content=watermarked_content,
        content_type=watermarked_content_type,
        original_filename="watermarked" + _extension_for_content_type(watermarked_content_type),
        extra_metadata=watermarked_metadata,
        width=width,
        height=height,
    )
    return GenerationResultAssets(raw_asset=raw_asset, watermarked_asset=watermarked_asset)


async def persist_generation_results(
    db: AsyncSession,
    *,
    job: Any,
    raw_image_bytes: bytes,
    watermarked_image_bytes: bytes,
    raw_content_type: str = "image/png",
    watermarked_content_type: str = "image/png",
) -> tuple[GenerationAsset, GenerationAsset]:
    assets = await persist_generation_result_assets(
        db,
        tenant_id=job.tenant_id,
        job_id=job.id,
        raw_content=raw_image_bytes,
        raw_content_type=raw_content_type,
        watermarked_content=watermarked_image_bytes,
        watermarked_content_type=watermarked_content_type,
    )
    return assets.raw_asset, assets.watermarked_asset


async def persist_generation_results(
    db: AsyncSession,
    *,
    job: Any,
    raw_image_bytes: bytes,
    watermarked_image_bytes: bytes,
    raw_content_type: str = "image/jpeg",
    watermarked_content_type: str = "image/jpeg",
    raw_metadata: Mapping[str, Any] | None = None,
    watermarked_metadata: Mapping[str, Any] | None = None,
) -> tuple[GenerationAsset, GenerationAsset]:
    assets = await persist_generation_result_assets(
        db,
        tenant_id=job.tenant_id,
        job_id=job.id,
        raw_content=raw_image_bytes,
        raw_content_type=raw_content_type,
        watermarked_content=watermarked_image_bytes,
        watermarked_content_type=watermarked_content_type,
        raw_metadata=raw_metadata,
        watermarked_metadata=watermarked_metadata,
    )
    return assets.raw_asset, assets.watermarked_asset
