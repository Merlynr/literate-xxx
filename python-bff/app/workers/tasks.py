from __future__ import annotations

import time

from celery.signals import worker_ready

from app.workers.celery_app import celery_app
from app.workers.generation import run_generation_job_sync


@celery_app.task(name="ping")
def ping_task(message: str = "pong") -> dict:
    """Simple test task to verify Celery worker connectivity."""
    return {"echo": message, "timestamp": time.time()}


@celery_app.task(name="generation.process")
def process_generation_task(job_id: str) -> dict:
    return run_generation_job_sync(job_id)


@celery_app.task(name="generation.reconcile")
def reconcile_stale_generation_jobs() -> dict:
    from app.services.job_reconciliation import recover_stale_jobs_sync

    return recover_stale_jobs_sync(trigger="watchdog")


@worker_ready.connect
def recover_stale_jobs_on_worker_ready(**kwargs) -> None:
    from loguru import logger

    from app.services.job_reconciliation import recover_stale_jobs_sync

    try:
        stats = recover_stale_jobs_sync(trigger="worker_startup")
        if stats.get("requeued") or stats.get("failed"):
            logger.info("Recovered stale generation jobs on worker startup: {}", stats)
    except Exception as exc:
        logger.warning("Generation job worker startup recovery skipped: {}", exc)
