from __future__ import annotations
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine
from app.api.router import api_router
from loguru import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting {} v{}", settings.PROJECT_NAME, settings.VERSION)
    try:
        from app.services.job_reconciliation import recover_stale_jobs_session

        stats = await recover_stale_jobs_session(trigger="bff_startup")
        if stats.get("requeued") or stats.get("failed"):
            logger.info("Recovered stale generation jobs on startup: {}", stats)
    except Exception as exc:
        logger.warning("Generation job startup recovery skipped: {}", exc)
    yield
    logger.info("Shutting down...")
    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        lifespan=lifespan,
    )
    # Web 端浏览器跨域（Bearer JWT，不用 cookie）
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)
    return app


app = create_app()
