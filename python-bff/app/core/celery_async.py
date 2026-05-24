from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from typing import TypeVar

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

T = TypeVar("T")


@asynccontextmanager
async def celery_async_session() -> AsyncIterator[AsyncSession]:
    """
    为 Celery 任务创建独立 AsyncEngine，避免与 FastAPI 或其它 asyncio.run()
    共用全局 engine 导致 "Future attached to a different loop"。
    """
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        pool_pre_ping=True,
    )
    session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    try:
        async with session_factory() as session:
            yield session
    finally:
        await engine.dispose()


def run_celery_async(
    fn: Callable[[AsyncSession], Awaitable[T]],
) -> T:
    async def _run() -> T:
        async with celery_async_session() as db:
            return await fn(db)

    return asyncio.run(_run())
