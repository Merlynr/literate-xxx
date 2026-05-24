from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import uuid
from typing import Any

import httpx
from sqlalchemy import select

from app.core.database import async_session_factory
from app.models.generation_asset import GenerationAsset
from app.models.generation_job import GenerationJob
from app.providers import get_image_generation_provider
from app.services.generation_jobs import generation_asset_download_url, record_job_event
from app.services.oss import generate_presigned_download_url
from app.services.generation_results import persist_generation_result_assets
from app.services.generation_snapshot import freeze_generation_job_context
from app.services.prompt_assembler import assemble_generation_prompt, build_image_role_preamble
from app.services.vision_analysis import analyze_generation_vision
from app.services.watermark import apply_watermark


async def _load_job(db, job_id: uuid.UUID) -> GenerationJob:
    job = await db.scalar(select(GenerationJob).where(GenerationJob.id == job_id))
    if not job:
        raise RuntimeError("Generation job not found")
    return job


def _resolve_style_cover_url(style_snapshot: dict) -> str:
    url = str(style_snapshot.get("cover_image_url") or "").strip()
    if not url:
        return ""
    if url.startswith("http://") or url.startswith("https://"):
        return url
    return generate_presigned_download_url(url)


async def _load_source_asset(db, job: GenerationJob) -> GenerationAsset:
    source_asset = await db.scalar(
        select(GenerationAsset).where(
            GenerationAsset.tenant_id == job.tenant_id,
            GenerationAsset.id == job.source_asset_id,
        )
    )
    if not source_asset:
        raise RuntimeError("Source asset not found for generation job")
    return source_asset


async def _download_image_bytes(url: str) -> tuple[bytes, str]:
    async with httpx.AsyncClient(timeout=120.0, follow_redirects=True, trust_env=False) as client:
        response = await client.get(url)
        response.raise_for_status()
        content_type = response.headers.get("content-type", "image/png").split(";", 1)[0].strip()
        return response.content, content_type


async def _run_generation_job(db, job_id: uuid.UUID) -> dict[str, Any]:
    job = await _load_job(db, job_id)
    source_asset = await _load_source_asset(db, job)
    context = freeze_generation_job_context(job, source_asset)
    now = datetime.now(timezone.utc)

    job.status = "running"
    if not job.started_at:
        job.started_at = now
    await record_job_event(
        db,
        tenant_id=job.tenant_id,
        job_id=job.id,
        event_type="job.running",
        message="Generation job running",
        payload={
            "source_asset_id": str(job.source_asset_id),
            "style_id": str(job.style_id) if job.style_id else None,
            "category_id": str(job.category_id) if job.category_id else None,
        },
    )
    await db.flush()

    try:
        prompt_snapshot = context.job.get("prompt_snapshot", {})
        rule_snapshot = context.job.get("rule_snapshot", {})
        style_snapshot = prompt_snapshot.get("style") or {}
        category_snapshot = prompt_snapshot.get("category") or {}
        source_download_url = generation_asset_download_url(source_asset)
        style_download_url = _resolve_style_cover_url(style_snapshot)
        prompt_hint = str(prompt_snapshot.get("prompt_hint") or "")
        vision_hint_parts = []
        if category_snapshot.get("name"):
            vision_hint_parts.append(f"类目：{category_snapshot['name']}")
        if style_snapshot.get("name"):
            vision_hint_parts.append(f"风格：{style_snapshot['name']}")
        if prompt_hint:
            vision_hint_parts.append(prompt_hint)
        vision_hint = "；".join(vision_hint_parts)

        # Vision：分别分析实拍主体 + 风格模板；出图：实拍第1张（主体）+ 模板第2张（学版式）
        vision_analysis = await analyze_generation_vision(
            source_image_url=source_download_url,
            style_image_url=style_download_url or None,
            prompt_hint=vision_hint,
            provider_name=context.job.get("provider"),
            model_name=context.job.get("model_name"),
        )
        prompt_bundle = assemble_generation_prompt(
            prompt_snapshot=prompt_snapshot,
            rule_snapshot=rule_snapshot,
            vision_analysis=vision_analysis,
        )
        generation_image_urls = [source_download_url]
        if style_download_url:
            generation_image_urls.append(style_download_url)
        image_preamble = build_image_role_preamble(has_style_template=bool(style_download_url))
        prompt_text = f"{image_preamble}\n\n{prompt_bundle.generation_prompt}"
        image_provider = get_image_generation_provider(context.job.get("provider"))
        generated = await image_provider.generate(
            prompt=prompt_text,
            image_urls=generation_image_urls,
            source_image_url=source_download_url,
            style_image_url=style_download_url or None,
            size=str(rule_snapshot.get("image_size") or "2K"),
            watermark=False,
            n=1,
        )
        raw_image_bytes, raw_content_type = await _download_image_bytes(generated.image_url)
        watermarked_image = apply_watermark(
            raw_image_bytes,
            watermark_config=rule_snapshot.get("watermark_config"),
        )
        result_assets = await persist_generation_result_assets(
            db,
            tenant_id=job.tenant_id,
            job_id=job.id,
            raw_content=raw_image_bytes,
            raw_content_type=raw_content_type,
            watermarked_content=watermarked_image.content,
            watermarked_content_type=watermarked_image.content_type,
            raw_metadata={
                "provider": generated.provider,
                "model_name": generated.model_name,
                "task_id": generated.task_id,
                "request_id": generated.request_id,
                "prompt_hash": prompt_bundle.prompt_snapshot["prompt_hash"],
                "source_url": generated.image_url,
            },
            watermarked_metadata={
                "provider": generated.provider,
                "model_name": generated.model_name,
                "task_id": generated.task_id,
                "request_id": generated.request_id,
                "prompt_hash": prompt_bundle.prompt_snapshot["prompt_hash"],
                "source_url": generated.image_url,
                "watermark_applied": True,
            },
        )
        raw_asset = result_assets.raw_asset
        watermarked_asset = result_assets.watermarked_asset
        job.raw_result_asset_id = raw_asset.id
        job.watermarked_result_asset_id = watermarked_asset.id
        job.status = "succeeded"
        job.error_code = ""
        job.error_message = ""
        job.finished_at = datetime.now(timezone.utc)
        await record_job_event(
            db,
            tenant_id=job.tenant_id,
            job_id=job.id,
            event_type="job.succeeded",
            message="Generation job succeeded",
            payload={
                "raw_asset_id": str(raw_asset.id),
                "watermarked_asset_id": str(watermarked_asset.id),
                "image_url": generated.image_url,
                "prompt_hash": prompt_bundle.prompt_snapshot["prompt_hash"],
            },
        )
        await db.flush()
        await db.commit()
        return {
            "job_id": str(job.id),
            "status": job.status,
            "raw_asset_id": str(raw_asset.id),
            "watermarked_asset_id": str(watermarked_asset.id),
            "prompt_hash": prompt_bundle.prompt_snapshot["prompt_hash"],
        }
    except Exception as exc:
        job.status = "failed"
        job.error_code = exc.__class__.__name__
        job.error_message = str(exc)
        job.finished_at = datetime.now(timezone.utc)
        await record_job_event(
            db,
            tenant_id=job.tenant_id,
            job_id=job.id,
            event_type="job.failed",
            message="Generation job failed",
            payload={"error_code": job.error_code, "error_message": job.error_message},
        )
        await db.flush()
        await db.commit()
        raise


async def run_generation_job(job_id: uuid.UUID | str) -> dict[str, Any]:
    target_id = uuid.UUID(str(job_id))
    async with async_session_factory() as db:
        return await _run_generation_job(db, target_id)


def run_generation_job_sync(job_id: str) -> dict[str, Any]:
    return asyncio.run(run_generation_job(job_id))
