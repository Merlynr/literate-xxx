from __future__ import annotations

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.services.generation_jobs import delete_generation_job


TENANT_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
JOB_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")
NOW = datetime(2026, 5, 24, 12, 0, 0, tzinfo=timezone.utc)


def _job(*, status: str):
    return SimpleNamespace(
        id=JOB_ID,
        tenant_id=TENANT_ID,
        status=status,
    )


@pytest.mark.asyncio
async def test_delete_generation_job_rejects_running(monkeypatch):
    db = MagicMock()
    job = _job(status="running")

    async def fake_get(*args, **kwargs):
        return job

    monkeypatch.setattr("app.services.generation_jobs.get_generation_job", fake_get)

    with pytest.raises(HTTPException) as exc:
        await delete_generation_job(db, tenant_id=TENANT_ID, job_id=JOB_ID)
    assert exc.value.status_code == 409


@pytest.mark.asyncio
async def test_delete_generation_job_removes_events_and_job(monkeypatch):
    db = MagicMock()
    job = _job(status="failed")
    db.execute = AsyncMock()
    db.delete = AsyncMock()
    db.flush = AsyncMock()

    async def fake_get(*args, **kwargs):
        return job

    release_calls: list[str] = []

    async def fake_release(*args, **kwargs):
        release_calls.append(kwargs.get("reason", ""))

    monkeypatch.setattr("app.services.generation_jobs.get_generation_job", fake_get)
    monkeypatch.setattr("app.services.generation_jobs.release_quota", fake_release)

    await delete_generation_job(db, tenant_id=TENANT_ID, job_id=JOB_ID)

    assert release_calls == ["generation.job.deleted"]
    db.execute.assert_awaited_once()
    db.delete.assert_awaited_once_with(job)
    db.flush.assert_awaited_once()
