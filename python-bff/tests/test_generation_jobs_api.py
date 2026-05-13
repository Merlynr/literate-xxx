from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from app.api import deps
from app.models.generation_asset import GenerationAsset
from app.models.generation_job import GenerationJob


TENANT_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
NOW = datetime(2026, 5, 13, 0, 0, 0, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def override_tenant_dependency(app):
    app.dependency_overrides[deps.get_current_tenant_id] = lambda: TENANT_ID
    yield
    app.dependency_overrides.pop(deps.get_current_tenant_id, None)


@pytest.mark.asyncio
async def test_confirm_generation_asset(client, monkeypatch):
    async def fake_confirm_generation_asset(*args, **kwargs):
        return GenerationAsset(
            id=uuid.UUID("22222222-2222-2222-2222-222222222222"),
            tenant_id=TENANT_ID,
            asset_role="source",
            oss_bucket="xxzx-assets",
            oss_key="uploads/demo.jpg",
            original_filename="demo.jpg",
            content_type="image/jpeg",
            size_bytes=123,
            sha256="abc123",
            etag="",
            width=100,
            height=200,
            extra_metadata=None,
            created_at=NOW,
            updated_at=NOW,
        )

    monkeypatch.setattr("app.api.v1.generation.confirm_generation_asset", fake_confirm_generation_asset)
    resp = await client.post(
        "/api/v1/generation-assets/confirm",
        json={
            "oss_key": "uploads/demo.jpg",
            "filename": "demo.jpg",
            "content_type": "image/jpeg",
            "size_bytes": 123,
            "sha256": "abc123",
            "asset_role": "source",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["oss_key"] == "uploads/demo.jpg"
    assert data["asset_role"] == "source"
    assert data["download_url"]


@pytest.mark.asyncio
async def test_create_generation_job(client, monkeypatch):
    async def fake_create_generation_job(*args, **kwargs):
        return GenerationJob(
            id=uuid.UUID("33333333-3333-3333-3333-333333333333"),
            tenant_id=TENANT_ID,
            client_request_id="req-1",
            status="queued",
            category_id=None,
            style_id=None,
            source_asset_id=uuid.UUID("22222222-2222-2222-2222-222222222222"),
            raw_result_asset_id=None,
            watermarked_result_asset_id=None,
            task_id="task-1",
            provider="alibaba-dashscope",
            model_name="wan2.7-image",
            rule_snapshot={"provider": "alibaba-dashscope"},
            prompt_snapshot={"prompt_hint": "clean"},
            request_snapshot={"client_request_id": "req-1"},
            error_code="",
            error_message="",
            created_at=NOW,
            updated_at=NOW,
        )

    monkeypatch.setattr("app.api.v1.generation.create_generation_job", fake_create_generation_job)
    resp = await client.post(
        "/api/v1/generation-jobs",
        json={
            "client_request_id": "req-1",
            "source_asset_id": "22222222-2222-2222-2222-222222222222",
            "prompt_hint": "clean",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["client_request_id"] == "req-1"
    assert data["status"] == "queued"
    assert data["task_id"] == "task-1"


@pytest.mark.asyncio
async def test_read_generation_job(client, monkeypatch):
    async def fake_get_generation_job(*args, **kwargs):
        return GenerationJob(
            id=uuid.UUID("44444444-4444-4444-4444-444444444444"),
            tenant_id=TENANT_ID,
            client_request_id="req-2",
            status="running",
            category_id=None,
            style_id=None,
            source_asset_id=uuid.UUID("22222222-2222-2222-2222-222222222222"),
            raw_result_asset_id=None,
            watermarked_result_asset_id=None,
            task_id="task-2",
            provider="alibaba-dashscope",
            model_name="wan2.7-image",
            rule_snapshot={"provider": "alibaba-dashscope"},
            prompt_snapshot={"prompt_hint": "clean"},
            request_snapshot={"client_request_id": "req-2"},
            error_code="",
            error_message="",
            created_at=NOW,
            updated_at=NOW,
        )

    monkeypatch.setattr("app.api.v1.generation.get_generation_job", fake_get_generation_job)
    resp = await client.get("/api/v1/generation-jobs/44444444-4444-4444-4444-444444444444")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "running"
    assert data["task_id"] == "task-2"
