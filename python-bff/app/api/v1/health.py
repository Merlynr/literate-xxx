from __future__ import annotations
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis
from app.api.deps import get_db
from app.core.config import settings
from app.schemas.health import HealthCheck

router = APIRouter()


@router.get("/health/liveness")
async def liveness():
    return {"status": "ok"}


@router.get("/health")
async def health_alias():
    """Backward-compatible alias for deploy scripts and external probes."""
    return {"status": "ok"}


@router.get("/health/readiness", response_model=HealthCheck)
async def readiness(db: AsyncSession = Depends(get_db)):
    checks: dict[str, str] = {}

    # Database check
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {e}"

    # Redis check
    try:
        r = aioredis.from_url(settings.REDIS_URL)
        await r.ping()
        await r.close()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {e}"

    # MinIO/S3 check
    try:
        import boto3
        from botocore.config import Config as BotoConfig
        s3 = boto3.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            config=BotoConfig(signature_version="s3v4"),
        )
        s3.list_buckets()
        checks["minio"] = "ok"
    except Exception as e:
        checks["minio"] = f"error: {e}"

    all_ok = all(v == "ok" for v in checks.values())
    return HealthCheck(status="ok" if all_ok else "degraded", checks=checks)
