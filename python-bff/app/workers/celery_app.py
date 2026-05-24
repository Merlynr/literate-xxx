from __future__ import annotations
from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "xxzx_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=False,
    task_track_started=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_soft_time_limit=90,
    task_time_limit=120,
    task_default_retry_delay=10,
    task_max_retries=3,
    broker_transport_options={"visibility_timeout": 3600},
    worker_prefetch_multiplier=1,
    beat_schedule={
        "generation-reconcile-stale-jobs": {
            "task": "generation.reconcile",
            "schedule": 300.0,
        },
    },
)

celery_app.autodiscover_tasks(["app.workers"])
