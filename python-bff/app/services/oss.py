from __future__ import annotations
import oss2
from loguru import logger
from app.core.config import settings


def _get_auth() -> oss2.Auth:
    """Create OSS authentication."""
    return oss2.Auth(settings.S3_ACCESS_KEY, settings.S3_SECRET_KEY)


def _get_bucket() -> oss2.Bucket:
    """Get OSS bucket instance."""
    auth = _get_auth()
    return oss2.Bucket(auth, settings.S3_ENDPOINT, settings.S3_BUCKET)


def ensure_bucket(bucket_name: str | None = None) -> None:
    """Create bucket if it does not exist. Idempotent."""
    auth = _get_auth()
    target = bucket_name or settings.S3_BUCKET
    try:
        bucket = oss2.Bucket(auth, settings.S3_ENDPOINT, target)
        # Check if bucket exists by listing objects (max 1)
        list(oss2.ObjectIterator(bucket, max_keys=1))
        logger.info("Bucket '{}' already exists", target)
    except oss2.exceptions.NoSuchBucket:
        logger.info("Creating bucket '{}'", target)
        oss2.Bucket(auth, settings.S3_ENDPOINT, target).create_bucket(
            oss2.models.BucketCreateConfig(oss2.BUCKET_ACL_PRIVATE)
        )
    except Exception as e:
        logger.warning("Bucket check failed: {}", e)


def generate_presigned_upload_url(
    key: str,
    content_type: str = "image/jpeg",
    expires_in: int = 300,
) -> str:
    """Generate a presigned PUT URL for client-side upload."""
    bucket = _get_bucket()
    url = bucket.sign_url("PUT", key, expires_in)
    return url


def generate_presigned_download_url(
    key: str,
    expires_in: int = 3600,
) -> str:
    """Generate a presigned GET URL for client-side download."""
    bucket = _get_bucket()
    url = bucket.sign_url("GET", key, expires_in)
    return url


def upload_bytes(data: bytes, key: str, content_type: str = "image/jpeg") -> str:
    """Upload bytes directly (server-side, used by Celery workers)."""
    bucket = _get_bucket()
    headers = {"Content-Type": content_type}
    bucket.put_object(key, data, headers=headers)
    return key
