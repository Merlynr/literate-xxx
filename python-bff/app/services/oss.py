from __future__ import annotations
import boto3
from botocore.config import Config as BotoConfig
from loguru import logger
from app.core.config import settings


def get_s3_client():
    """Create an S3-compatible client. Works with MinIO, Aliyun OSS, Qiniu, AWS S3 (D-06)."""
    return boto3.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT,
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY,
        region_name=settings.S3_REGION or None,
        config=BotoConfig(signature_version="s3v4"),
    )


def ensure_bucket(bucket_name: str | None = None) -> None:
    """Create bucket if it does not exist. Idempotent."""
    s3 = get_s3_client()
    target = bucket_name or settings.S3_BUCKET
    try:
        s3.head_bucket(Bucket=target)
        logger.info("Bucket '{}' already exists", target)
    except Exception:
        logger.info("Creating bucket '{}'", target)
        s3.create_bucket(Bucket=target)


def generate_presigned_upload_url(
    key: str,
    content_type: str = "image/jpeg",
    expires_in: int = 300,
) -> str:
    """Generate a presigned PUT URL for client-side upload."""
    s3 = get_s3_client()
    url = s3.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": settings.S3_BUCKET,
            "Key": key,
            "ContentType": content_type,
        },
        ExpiresIn=expires_in,
    )
    return url


def generate_presigned_download_url(
    key: str,
    expires_in: int = 3600,
) -> str:
    """Generate a presigned GET URL for client-side download."""
    s3 = get_s3_client()
    url = s3.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": settings.S3_BUCKET,
            "Key": key,
        },
        ExpiresIn=expires_in,
    )
    return url


def upload_bytes(data: bytes, key: str, content_type: str = "image/jpeg") -> str:
    """Upload bytes directly (server-side, used by Celery workers in Phase 3)."""
    s3 = get_s3_client()
    s3.put_object(
        Bucket=settings.S3_BUCKET,
        Key=key,
        Body=data,
        ContentType=content_type,
    )
    return key
