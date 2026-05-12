from __future__ import annotations
import time
from app.workers.celery_app import celery_app


@celery_app.task(name="ping")
def ping_task(message: str = "pong") -> dict:
    """Simple test task to verify Celery worker connectivity."""
    return {"echo": message, "timestamp": time.time()}
