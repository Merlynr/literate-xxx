from __future__ import annotations

import time

from app.workers.celery_app import celery_app
from app.workers.generation import run_generation_job_sync


@celery_app.task(name="ping")
def ping_task(message: str = "pong") -> dict:
    """Simple test task to verify Celery worker connectivity."""
    return {"echo": message, "timestamp": time.time()}


@celery_app.task(name="generation.process")
def process_generation_task(job_id: str) -> dict:
    return run_generation_job_sync(job_id)
