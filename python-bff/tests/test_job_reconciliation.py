from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
import uuid
from zoneinfo import ZoneInfo

import pytest

from app.services import job_reconciliation as reconciliation


TENANT_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
JOB_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")
SH = ZoneInfo("Asia/Shanghai")
NOW = datetime(2026, 5, 24, 18, 31, 0, tzinfo=SH)


def _job(
    *,
    status: str,
    created_at: datetime,
    updated_at: datetime | None = None,
    started_at: datetime | None = None,
):
    return SimpleNamespace(
        id=JOB_ID,
        tenant_id=TENANT_ID,
        status=status,
        created_at=created_at,
        updated_at=updated_at or created_at,
        started_at=started_at,
        task_id="old-task",
        error_code="",
        error_message="",
        finished_at=None,
    )


def test_is_queued_stale_only_after_threshold():
    job = _job(status="queued", created_at=NOW - timedelta(minutes=4))
    assert reconciliation.is_queued_stale(job, now=NOW) is True
    fresh = _job(status="queued", created_at=NOW - timedelta(minutes=1))
    assert reconciliation.is_queued_stale(fresh, now=NOW) is False


def test_is_queued_stale_naive_local_datetime_not_treated_as_utc():
    """MySQL 常返回 naive 本地时间；误当 UTC 会导致永远不算 stale。"""
    created = datetime(2026, 5, 24, 16, 56, 17)  # naive, 上海墙钟
    job = _job(status="queued", created_at=created, updated_at=NOW)
    assert reconciliation.is_queued_stale(job, now=NOW) is True


def test_is_running_stale_only_after_threshold():
    started = NOW - timedelta(minutes=6)
    job = _job(
        status="running",
        created_at=started,
        updated_at=NOW - timedelta(minutes=10),
        started_at=started,
    )
    assert reconciliation.is_running_stale(job, now=NOW) is True


@pytest.mark.asyncio
async def test_requeue_generation_job_dispatches_and_records_event(monkeypatch):
    job = _job(status="queued", created_at=NOW - timedelta(minutes=10))
    db = MagicMock()
    db.scalar = AsyncMock(return_value=0)
    db.flush = AsyncMock()

    def fake_dispatch(current):
        current.task_id = "task-new"
        return "task-new"

    monkeypatch.setattr(reconciliation, "dispatch_generation_job", fake_dispatch)
    record_calls: list[str] = []

    async def fake_record_job_event(db_arg, **kwargs):
        record_calls.append(kwargs["event_type"])

    monkeypatch.setattr(reconciliation, "record_job_event", fake_record_job_event)

    requeued = await reconciliation.requeue_generation_job(db, job, trigger="poll")

    assert requeued is True
    assert job.task_id == "task-new"
    assert record_calls == ["job.requeued"]


@pytest.mark.asyncio
async def test_maybe_recover_job_fails_stale_running(monkeypatch):
    stale_started = NOW - timedelta(minutes=6)
    job = _job(
        status="running",
        created_at=stale_started,
        updated_at=stale_started,
        started_at=stale_started,
    )
    db = MagicMock()
    fail_calls: list[str] = []

    async def fake_fail_stale_running_job(db_arg, current, *, trigger):
        fail_calls.append(trigger)

    monkeypatch.setattr(reconciliation, "fail_stale_running_job", fake_fail_stale_running_job)

    action = await reconciliation.maybe_recover_job(db, job, trigger="watchdog")

    assert action == "failed"
    assert fail_calls == ["watchdog"]
