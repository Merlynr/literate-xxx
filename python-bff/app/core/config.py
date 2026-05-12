from __future__ import annotations
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    PROJECT_NAME: str = "XX甄选 BFF"
    VERSION: str = "0.1.0"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # MySQL
    DATABASE_URL: str = "mysql+aiomysql://root:Eversec%40123098@192.168.10.88:3306/xxzx"

    # Redis
    REDIS_URL: str = "redis://:123456@192.168.10.88:6379/0"

    # Celery
    CELERY_BROKER_URL: str = "redis://:123456@192.168.10.88:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://:123456@192.168.10.88:6379/2"

    # S3 / MinIO
    S3_ENDPOINT: str = "http://192.168.10.88:9000"
    S3_ACCESS_KEY: str = "admin"
    S3_SECRET_KEY: str = "adminadmin"
    S3_BUCKET: str = "xxzx-assets"
    S3_REGION: str = "us-east-1"
    S3_USE_SSL: bool = False


settings = Settings()