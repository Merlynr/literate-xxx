from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
import uuid

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.services import quota_service
from app.services.generation_jobs import create_generation_job


TENANT_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
USER_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")
JOB_ID = uuid.UUID("33333333-3333-3333-3333-333333333333")
SOURCE_ASSET_ID = uuid.UUID("44444444-4444-4444-4444-444444444444")


class FakeDB:
    def __init__(self):
        self.added = []
        self.scalar_result = None
        self.flush_calls = 0
        self.refresh_calls = 0

    async def scalar(self, *args, **kwargs):
        return self.scalar_result

    def add(self, obj):
        self.added.append(obj)

    async def flush(self):
        self.flush_calls += 1

    async def refresh(self, obj):
        self.refresh_calls += 1

    async def get(self, model, identity):
        return None


@pytest.mark.asyncio
async def test_quota_transitions(monkeypatch):
    account = SimpleNamespace(
        tenant_id=TENANT_ID,
        total_units=10,
        available_units=10,
        frozen_units=0,
        active_plan_id=1,
        updated_at=datetime(2026, 5, 13, tzinfo=timezone.utc),
    )
    events: list[str] = []

    async def fake_get_or_create_quota_account(db, tenant_id):
        assert tenant_id == TENANT_ID
        return account

    async def fake_add_entry(db, **kwargs):
        events.append(kwargs["event_type"])
        return SimpleNamespace()

    db = FakeDB()
    monkeypatch.setattr(quota_service, "get_or_create_quota_account", fake_get_or_create_quota_account)
    monkeypatch.setattr(quota_service, "_add_ledger_entry", fake_add_entry)

    await quota_service.freeze_quota(db, tenant_id=TENANT_ID, job_id=JOB_ID, units=1, reason="create")
    assert account.available_units == 9
    assert account.frozen_units == 1
    assert events[-1] == "freeze"

    await quota_service.commit_quota_deduction(db, tenant_id=TENANT_ID, job_id=JOB_ID, units=1, reason="success")
    assert account.available_units == 9
    assert account.frozen_units == 0
    assert account.total_units == 9
    assert events[-1] == "deduct"

    await quota_service.freeze_quota(db, tenant_id=TENANT_ID, job_id=JOB_ID, units=1, reason="create")
    await quota_service.release_quota(db, tenant_id=TENANT_ID, job_id=JOB_ID, units=1, reason="failed")
    assert account.available_units == 9
    assert account.frozen_units == 0
    assert events[-1] == "release"


@pytest.mark.asyncio
async def test_create_generation_job_requires_privacy(monkeypatch):
    db = FakeDB()
    async def fake_source(*args, **kwargs):
        return SimpleNamespace()

    async def fake_none(*args, **kwargs):
        return None

    monkeypatch.setattr("app.services.generation_jobs._load_source_asset", fake_source)
    monkeypatch.setattr("app.services.generation_jobs._load_category", fake_none)
    monkeypatch.setattr("app.services.generation_jobs._load_style", fake_none)
    monkeypatch.setattr("app.services.generation_jobs._load_active_rule", fake_none)
    async def fake_privacy(*args, **kwargs):
        return False
    async def fake_freeze(*args, **kwargs):
        return None
    monkeypatch.setattr("app.services.generation_jobs.has_generation_privacy_agreement", fake_privacy)
    monkeypatch.setattr("app.services.generation_jobs.freeze_quota", fake_freeze)

    with pytest.raises(HTTPException) as exc:
        await create_generation_job(
            db,
            tenant_id=TENANT_ID,
            user_id=USER_ID,
            client_request_id="req-1",
            source_asset_id=SOURCE_ASSET_ID,
        )
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_create_generation_job_freezes_quota(monkeypatch):
    db = FakeDB()
    freeze_calls = []

    async def fake_source(*args, **kwargs):
        return SimpleNamespace(id=SOURCE_ASSET_ID, tenant_id=TENANT_ID, asset_role="source", oss_bucket="b", oss_key="k", original_filename="source.jpg", content_type="image/jpeg", size_bytes=1, sha256="", etag="", width=None, height=None, extra_metadata=None)

    async def fake_none(*args, **kwargs):
        return None

    async def fake_rule(*args, **kwargs):
        return None

    async def fake_privacy(*args, **kwargs):
        return True

    async def fake_freeze(*args, **kwargs):
        freeze_calls.append(kwargs)
        return SimpleNamespace()

    class FakeResult:
        id = "task-1"

    monkeypatch.setattr("app.services.generation_jobs._load_source_asset", fake_source)
    monkeypatch.setattr("app.services.generation_jobs._load_category", fake_none)
    monkeypatch.setattr("app.services.generation_jobs._load_style", fake_none)
    monkeypatch.setattr("app.services.generation_jobs._load_active_rule", fake_rule)
    monkeypatch.setattr("app.services.generation_jobs.has_generation_privacy_agreement", fake_privacy)
    monkeypatch.setattr("app.services.generation_jobs.freeze_quota", fake_freeze)
    async def fake_record_event(*args, **kwargs):
        return None
    monkeypatch.setattr("app.services.generation_jobs.record_job_event", fake_record_event)
    monkeypatch.setattr("app.services.generation_jobs.celery_app.send_task", lambda *args, **kwargs: FakeResult())
    db.scalar_result = None

    job = await create_generation_job(
        db,
        tenant_id=TENANT_ID,
        user_id=USER_ID,
        client_request_id="req-1",
        source_asset_id=SOURCE_ASSET_ID,
    )
    assert job.client_request_id == "req-1"
    assert freeze_calls[0]["units"] == 1
    assert freeze_calls[0]["reason"] == "generation.job.create"


@pytest.mark.asyncio
async def test_auth_me_exposes_privacy_status(client, app, monkeypatch):
    fake_user = SimpleNamespace(
        id=USER_ID,
        tenant_id=TENANT_ID,
        nickname="本地调试",
        openid="dev-local-openid",
        avatar_url="",
    )

    async def fake_user_dep():
        return fake_user

    async def fake_db_dep():
        yield FakeDB()

    app.dependency_overrides[get_current_user] = fake_user_dep
    app.dependency_overrides[get_db] = fake_db_dep

    async def fake_status(*args, **kwargs):
        return SimpleNamespace(consented_at=datetime(2026, 5, 13, 12, 0, tzinfo=timezone.utc))

    monkeypatch.setattr("app.api.v1.auth.get_generation_privacy_status", fake_status)

    resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer fake-token"},
    )
    assert resp.status_code == 200
    assert resp.json()["privacy_accepted_at"] is not None

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_quota_and_privacy_routes(client, app, monkeypatch):
    fake_user = SimpleNamespace(
        id=USER_ID,
        tenant_id=TENANT_ID,
        nickname="本地调试",
        openid="dev-local-openid",
        avatar_url="",
    )

    async def fake_user_dep():
        return fake_user

    async def fake_db_dep():
        yield FakeDB()

    app.dependency_overrides[get_current_user] = fake_user_dep
    app.dependency_overrides[get_db] = fake_db_dep

    async def fake_quota_snapshot(*args, **kwargs):
        return quota_service.QuotaSnapshot(
            total_units=10,
            available_units=9,
            frozen_units=1,
            active_plan_id=1,
            active_plan_name="Default 100",
            updated_at=datetime(2026, 5, 13, tzinfo=timezone.utc),
        )
    async def fake_estimate(*args, **kwargs):
        return {"estimated_units": 1, "price_cents": 0, "plan_code": "DEFAULT_100"}

    async def fake_ledger(*args, **kwargs):
        return []

    async def fake_none(*args, **kwargs):
        return None

    async def fake_accept(*args, **kwargs):
        return SimpleNamespace(consented_at=datetime(2026, 5, 13, 12, 0, tzinfo=timezone.utc))

    monkeypatch.setattr("app.api.v1.quota.get_quota_snapshot", fake_quota_snapshot)
    monkeypatch.setattr("app.api.v1.quota.estimate_quota_cost", fake_estimate)
    monkeypatch.setattr("app.api.v1.quota.list_quota_ledger", fake_ledger)
    monkeypatch.setattr("app.api.v1.privacy.get_generation_privacy_status", fake_none)
    monkeypatch.setattr("app.api.v1.privacy.accept_generation_privacy", fake_accept)

    summary = await client.get("/api/v1/quota/summary", headers={"Authorization": "Bearer fake-token"})
    assert summary.status_code == 200
    assert summary.json()["available_units"] == 9

    estimate = await client.post("/api/v1/quota/estimate", json={}, headers={"Authorization": "Bearer fake-token"})
    assert estimate.status_code == 200
    assert estimate.json()["plan_code"] == "DEFAULT_100"

    privacy = await client.get("/api/v1/privacy/agreement-status", headers={"Authorization": "Bearer fake-token"})
    assert privacy.status_code == 200
    assert privacy.json()["has_privacy_agreement"] is False

    accepted = await client.post("/api/v1/privacy/accept", json={}, headers={"Authorization": "Bearer fake-token"})
    assert accepted.status_code == 200
    assert accepted.json()["has_privacy_agreement"] is True

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_generation_history_route(client, app, monkeypatch):
    fake_user = SimpleNamespace(
        id=USER_ID,
        tenant_id=TENANT_ID,
        nickname="本地调试",
        openid="dev-local-openid",
        avatar_url="",
    )

    async def fake_user_dep():
        return fake_user

    fake_db = FakeDB()

    async def fake_db_get(model, identity):
        if identity == SOURCE_ASSET_ID:
            return source_asset
        if identity == raw_asset.id:
            return raw_asset
        if identity == watermarked_asset.id:
            return watermarked_asset
        return None

    fake_db.get = fake_db_get  # type: ignore[assignment]

    async def fake_db_dep():
        yield fake_db

    app.dependency_overrides[get_current_user] = fake_user_dep
    app.dependency_overrides[get_db] = fake_db_dep

    source_asset = SimpleNamespace(
        id=SOURCE_ASSET_ID,
        tenant_id=TENANT_ID,
        oss_key="uploads/source.jpg",
        asset_role="source",
    )
    raw_asset = SimpleNamespace(
        id=uuid.UUID("55555555-5555-5555-5555-555555555555"),
        tenant_id=TENANT_ID,
        oss_key="generation/raw.jpg",
        asset_role="raw",
    )
    watermarked_asset = SimpleNamespace(
        id=uuid.UUID("66666666-6666-6666-6666-666666666666"),
        tenant_id=TENANT_ID,
        oss_key="generation/watermarked.jpg",
        asset_role="watermarked",
    )

    async def fake_jobs(*args, **kwargs):
        return [
            SimpleNamespace(
                id=JOB_ID,
                status="succeeded",
                created_at=datetime(2026, 5, 13, 12, 0, tzinfo=timezone.utc),
                updated_at=datetime(2026, 5, 13, 12, 5, tzinfo=timezone.utc),
                source_asset_id=SOURCE_ASSET_ID,
                raw_result_asset_id=raw_asset.id,
                watermarked_result_asset_id=watermarked_asset.id,
                error_message="",
            )
        ]

    monkeypatch.setattr("app.api.v1.generation_history.list_generation_jobs", fake_jobs)

    resp = await client.get("/api/v1/generation-history", headers={"Authorization": "Bearer fake-token"})
    assert resp.status_code == 200
    payload = resp.json()
    assert payload[0]["job_id"] == str(JOB_ID)
    assert payload[0]["watermarked_result_download_url"]

    app.dependency_overrides.clear()
