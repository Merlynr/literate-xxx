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
    from loguru import logger

    logger.info("generation.process received job_id={}", job_id)
    try:
        return run_generation_job_sync(job_id)
    except Exception:
        logger.exception("generation.process failed job_id={}", job_id)
        from app.workers.generation import mark_generation_job_failed_sync

        mark_generation_job_failed_sync(job_id)
        raise


@celery_app.task(name="generation.reconcile")
def reconcile_stale_generation_jobs() -> dict:
    from loguru import logger

    from app.services.job_reconciliation import recover_stale_jobs_sync

    stats = recover_stale_jobs_sync(trigger="watchdog")
    if stats.get("requeued") or stats.get("failed") or stats.get("scanned", 0) > 0:
        logger.info("generation.reconcile finished: {}", stats)
    return stats


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
