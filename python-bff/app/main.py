from __future__ import annotations
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.config import settings
from app.core.database import engine
from app.api.router import api_router
from loguru import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting {} v{}", settings.PROJECT_NAME, settings.VERSION)
    yield
    logger.info("Shutting down...")
    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        lifespan=lifespan,
    )
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)
    return app


app = create_app()
