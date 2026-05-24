from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory
from app.models.generation_job import GenerationJob
from app.models.generation_job_event import GenerationJobEvent
from app.services.generation_jobs import dispatch_generation_job, record_job_event
from app.services.quota_service import release_quota

QUEUED_STALE_SECONDS = 180
RUNNING_STALE_SECONDS = 300
MAX_REQUEUE_ATTEMPTS = 3
RECOVER_BATCH_LIMIT = 100


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


async def count_requeue_events(db: AsyncSession, job_id: uuid.UUID) -> int:
    count = await db.scalar(
        select(func.count())
        .select_from(GenerationJobEvent)
        .where(
            GenerationJobEvent.job_id == job_id,
            GenerationJobEvent.event_type == "job.requeued",
        )
    )
    return int(count or 0)


async def _try_release_job_quota(db: AsyncSession, job: GenerationJob, *, reason: str) -> None:
    try:
        await release_quota(
            db,
            tenant_id=job.tenant_id,
            job_id=job.id,
            units=1,
            reason=reason,
        )
    except HTTPException:
        pass


async def mark_job_failed(
    db: AsyncSession,
    job: GenerationJob,
    *,
    error_code: str,
    error_message: str,
    trigger: str,
    release_quota_reason: str = "generation.job.failed",
) -> None:
    if job.status in ("succeeded", "failed"):
        return
    job.status = "failed"
    job.error_code = error_code
    job.error_message = error_message
    job.finished_at = utcnow()
    await _try_release_job_quota(db, job, reason=release_quota_reason)
    await record_job_event(
        db,
        tenant_id=job.tenant_id,
        job_id=job.id,
        event_type="job.failed",
        message="Generation job marked failed during recovery",
        payload={
            "error_code": error_code,
            "error_message": error_message,
            "trigger": trigger,
        },
    )
    await db.flush()


async def requeue_generation_job(
    db: AsyncSession,
    job: GenerationJob,
    *,
    trigger: str,
) -> bool:
    if job.status != "queued":
        return False

    requeue_count = await count_requeue_events(db, job.id)
    if requeue_count >= MAX_REQUEUE_ATTEMPTS:
        await mark_job_failed(
            db,
            job,
            error_code="RequeueLimitExceeded",
            error_message="Generation job exceeded automatic requeue attempts",
            trigger=trigger,
        )
        return False

    task_id = dispatch_generation_job(job)
    await record_job_event(
        db,
        tenant_id=job.tenant_id,
        job_id=job.id,
        event_type="job.requeued",
        message="Generation job re-queued",
        payload={
            "trigger": trigger,
            "task_id": task_id,
            "requeue_count": requeue_count + 1,
        },
    )
    await db.flush()
    return True


async def fail_stale_running_job(
    db: AsyncSession,
    job: GenerationJob,
    *,
    trigger: str,
) -> None:
    await mark_job_failed(
        db,
        job,
        error_code="JobStaleRunning",
        error_message="Generation timed out or worker restarted while running",
        trigger=trigger,
    )


def is_queued_stale(job: GenerationJob, *, now: datetime | None = None) -> bool:
    if job.status != "queued":
        return False
    reference = as_utc(job.updated_at or job.created_at)
    if reference is None:
        return False
    current = now or utcnow()
    return (current - reference).total_seconds() >= QUEUED_STALE_SECONDS


def is_running_stale(job: GenerationJob, *, now: datetime | None = None) -> bool:
    if job.status != "running":
        return False
    reference = as_utc(job.started_at or job.updated_at or job.created_at)
    if reference is None:
        return False
    current = now or utcnow()
    return (current - reference).total_seconds() >= RUNNING_STALE_SECONDS


async def maybe_recover_job(
    db: AsyncSession,
    job: GenerationJob,
    *,
    trigger: str,
) -> str | None:
    if is_queued_stale(job):
        if await requeue_generation_job(db, job, trigger=trigger):
            return "requeued"
        if job.status == "failed":
            return "failed"
    elif is_running_stale(job):
        await fail_stale_running_job(db, job, trigger=trigger)
        return "failed"
    return None


async def recover_stale_jobs(
    db: AsyncSession,
    *,
    trigger: str,
    limit: int = RECOVER_BATCH_LIMIT,
) -> dict[str, Any]:
    jobs = list(
        await db.scalars(
            select(GenerationJob)
            .where(GenerationJob.status.in_(("queued", "running")))
            .order_by(GenerationJob.updated_at.asc())
            .limit(limit)
        )
    )
    stats = {"scanned": 0, "requeued": 0, "failed": 0, "trigger": trigger}
    for job in jobs:
        stats["scanned"] += 1
        action = await maybe_recover_job(db, job, trigger=trigger)
        if action == "requeued":
            stats["requeued"] += 1
        elif action == "failed":
            stats["failed"] += 1
    if stats["requeued"] or stats["failed"]:
        await db.commit()
    return stats


async def recover_stale_jobs_session(*, trigger: str) -> dict[str, Any]:
    async with async_session_factory() as db:
        return await recover_stale_jobs(db, trigger=trigger)


def recover_stale_jobs_sync(*, trigger: str) -> dict[str, Any]:
    return asyncio.run(recover_stale_jobs_session(trigger=trigger))
