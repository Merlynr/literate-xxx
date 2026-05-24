from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from types import SimpleNamespace
import uuid

import pytest

from app.workers import generation as generation_worker
from app.workers.tasks import process_generation_task


TENANT_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
JOB_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")
SOURCE_ASSET_ID = uuid.UUID("33333333-3333-3333-3333-333333333333")
RAW_ASSET_ID = uuid.UUID("44444444-4444-4444-4444-444444444444")
WATERMARKED_ASSET_ID = uuid.UUID("55555555-5555-5555-5555-555555555555")
NOW = datetime(2026, 5, 13, 12, 0, 0, tzinfo=timezone.utc)


class FakeDB:
    def __init__(self):
        self.flush_calls = 0
        self.commit_calls = 0
        self.rollback_calls = 0

    async def flush(self):
        self.flush_calls += 1

    async def commit(self):
        self.commit_calls += 1

    async def rollback(self):
        self.rollback_calls += 1


class FakeSessionFactory:
    def __init__(self, db: FakeDB):
        self.db = db

    def __call__(self):
        return self

    async def __aenter__(self):
        return self.db

    async def __aexit__(self, exc_type, exc, tb):
        return False


@dataclass
class FakeAsset:
    id: uuid.UUID
    tenant_id: uuid.UUID
    job_id: uuid.UUID | None
    asset_role: str
    oss_bucket: str
    oss_key: str
    original_filename: str = "source.jpg"
    content_type: str = "image/jpeg"
    size_bytes: int | None = 123
    sha256: str = "sha"
    etag: str = ""
    width: int | None = 120
    height: int | None = 240
    extra_metadata: dict | None = None
    created_at: datetime = NOW
    updated_at: datetime = NOW


@dataclass
class FakeJob:
    id: uuid.UUID
    tenant_id: uuid.UUID
    client_request_id: str
    status: str
    category_id: uuid.UUID | None
    style_id: uuid.UUID | None
    source_asset_id: uuid.UUID
    raw_result_asset_id: uuid.UUID | None
    watermarked_result_asset_id: uuid.UUID | None
    task_id: str | None
    provider: str
    model_name: str
    rule_snapshot: dict
    prompt_snapshot: dict
    request_snapshot: dict
    error_code: str
    error_message: str
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime = NOW
    updated_at: datetime = NOW


@pytest.mark.asyncio
async def test_generation_worker_pipeline_with_fakes(monkeypatch):
    db = FakeDB()
    monkeypatch.setattr(generation_worker, "async_session_factory", FakeSessionFactory(db))

    job = FakeJob(
        id=JOB_ID,
        tenant_id=TENANT_ID,
        client_request_id="req-1",
        status="queued",
        category_id=None,
        style_id=None,
        source_asset_id=SOURCE_ASSET_ID,
        raw_result_asset_id=None,
        watermarked_result_asset_id=None,
        task_id="task-1",
        provider="alibaba-dashscope",
        model_name="wan2.7-image",
        rule_snapshot={
            "slot_template": {"title": "Warm poster"},
            "watermark_config": {"text": "XXZX"},
        },
        prompt_snapshot={
            "source_asset": {
                "id": str(SOURCE_ASSET_ID),
                "tenant_id": str(TENANT_ID),
                "asset_role": "source",
                "oss_bucket": "xxzx-assets",
                "oss_key": "uploads/source.jpg",
                "original_filename": "source.jpg",
                "content_type": "image/jpeg",
                "size_bytes": 123,
                "sha256": "sha-source",
                "etag": "",
                "width": 120,
                "height": 240,
                "extra_metadata": None,
            },
            "style": {
                "id": "style-1",
                "tenant_id": str(TENANT_ID),
                "name": "Warm Style",
                "cover_image_url": "https://signed.example/style.jpg",
                "rule_version": 1,
                "sort_order": 1,
                "is_active": True,
            },
            "category": None,
            "prompt_hint": "keep the product centered",
        },
        request_snapshot={"client_request_id": "req-1"},
        error_code="",
        error_message="",
        started_at=None,
        finished_at=None,
    )
    source_asset = FakeAsset(
        id=SOURCE_ASSET_ID,
        tenant_id=TENANT_ID,
        job_id=None,
        asset_role="source",
        oss_bucket="xxzx-assets",
        oss_key="uploads/source.jpg",
    )

    events: list[tuple[str, dict]] = []
    download_calls: list[str] = []
    prompt_calls: list[dict] = []
    provider_calls: list[dict] = []
    persist_calls: list[dict] = []

    async def fake_load_job(db_arg, job_id):
        assert db_arg is db
        assert job_id == JOB_ID
        return job

    async def fake_load_source_asset(db_arg, job_arg):
        assert db_arg is db
        assert job_arg is job
        return source_asset

    async def fake_record_job_event(db_arg, **kwargs):
        assert db_arg is db
        events.append((kwargs["event_type"], kwargs.get("payload") or {}))
        return SimpleNamespace()

    def fake_generation_asset_download_url(asset):
        assert asset is source_asset
        return "https://signed.example/source.jpg"

    async def fake_analyze_generation_vision(
        *,
        source_image_url,
        style_image_url=None,
        prompt_hint="",
        provider_name=None,
        model_name=None,
    ):
        assert source_image_url == "https://signed.example/source.jpg"
        assert style_image_url == "https://signed.example/style.jpg"
        assert prompt_hint == "keep the product centered"
        assert provider_name == "alibaba-dashscope"
        assert model_name == "wan2.7-image"
        return {
            "product_subject": {"must_preserve": ["green bottle", "label text"]},
            "style_reference": {"background": "studio", "lighting": "soft"},
        }

    def fake_assemble_generation_prompt(*, prompt_snapshot, rule_snapshot, vision_analysis):
        prompt_calls.append(
            {
                "prompt_snapshot": prompt_snapshot,
                "rule_snapshot": rule_snapshot,
                "vision_analysis": vision_analysis,
            }
        )
        return SimpleNamespace(
            system_prompt="SYSTEM",
            user_prompt="USER",
            generation_prompt="PROMPT TEXT",
            reference_urls=("https://signed.example/source.jpg",),
            prompt_snapshot={"prompt_hash": "a" * 64, "assembled_prompt": "PROMPT TEXT"},
        )

    class FakeImageProvider:
        async def generate(self, *, prompt, image_urls, size, watermark, n, source_image_url=None, style_image_url=None):
            provider_calls.append(
                {
                    "prompt": prompt,
                    "image_urls": list(image_urls),
                    "source_image_url": source_image_url,
                    "size": size,
                    "watermark": watermark,
                    "n": n,
                }
            )
            return SimpleNamespace(
                provider="alibaba-dashscope",
                model_name="wan2.7-image",
                prompt=prompt,
                image_urls=tuple(image_urls),
                image_url="https://generated.example/raw.png",
                request_id="gen-1",
                task_id="task-gen-1",
                raw_response={"ok": True},
            )

    async def fake_download_image_bytes(url):
        download_calls.append(url)
        return b"raw-image-bytes", "image/png"

    def fake_apply_watermark(image_bytes, *, watermark_config=None):
        assert image_bytes == b"raw-image-bytes"
        assert watermark_config == {"text": "XXZX"}
        return SimpleNamespace(
            content=b"watermarked-bytes",
            content_type="image/png",
            width=120,
            height=240,
            image_format="PNG",
        )

    async def fake_persist_generation_result_assets(
        db_arg,
        *,
        tenant_id,
        job_id,
        raw_content,
        raw_content_type,
        watermarked_content,
        watermarked_content_type,
        raw_metadata=None,
        watermarked_metadata=None,
        width=None,
        height=None,
    ):
        assert db_arg is db
        persist_calls.append(
            {
                "tenant_id": tenant_id,
                "job_id": job_id,
                "raw_content": raw_content,
                "raw_content_type": raw_content_type,
                "watermarked_content": watermarked_content,
                "watermarked_content_type": watermarked_content_type,
                "raw_metadata": raw_metadata,
                "watermarked_metadata": watermarked_metadata,
                "width": width,
                "height": height,
            }
        )
        return SimpleNamespace(
            raw_asset=SimpleNamespace(id=RAW_ASSET_ID),
            watermarked_asset=SimpleNamespace(id=WATERMARKED_ASSET_ID),
        )

    monkeypatch.setattr(generation_worker, "_load_job", fake_load_job)
    monkeypatch.setattr(generation_worker, "_load_source_asset", fake_load_source_asset)
    monkeypatch.setattr(generation_worker, "record_job_event", fake_record_job_event)
    monkeypatch.setattr(generation_worker, "generation_asset_download_url", fake_generation_asset_download_url)
    monkeypatch.setattr(generation_worker, "analyze_generation_vision", fake_analyze_generation_vision)
    monkeypatch.setattr(generation_worker, "assemble_generation_prompt", fake_assemble_generation_prompt)
    monkeypatch.setattr(generation_worker, "get_image_generation_provider", lambda provider_name: FakeImageProvider())
    monkeypatch.setattr(generation_worker, "_download_image_bytes", fake_download_image_bytes)
    monkeypatch.setattr(generation_worker, "apply_watermark", fake_apply_watermark)
    monkeypatch.setattr(generation_worker, "persist_generation_result_assets", fake_persist_generation_result_assets)

    result = await generation_worker.run_generation_job(str(JOB_ID))

    assert result["status"] == "succeeded"
    assert result["raw_asset_id"] == str(RAW_ASSET_ID)
    assert result["watermarked_asset_id"] == str(WATERMARKED_ASSET_ID)
    assert job.status == "succeeded"
    assert job.raw_result_asset_id == RAW_ASSET_ID
    assert job.watermarked_result_asset_id == WATERMARKED_ASSET_ID
    assert job.started_at is not None
    assert job.finished_at is not None
    assert db.flush_calls >= 2
    assert db.commit_calls == 1
    assert [event_type for event_type, _ in events] == ["job.running", "job.succeeded"]
    assert download_calls == ["https://generated.example/raw.png"]
    assert provider_calls[0]["image_urls"] == [
        "https://signed.example/source.jpg",
        "https://signed.example/style.jpg",
    ]
    assert provider_calls[0]["source_image_url"] == "https://signed.example/source.jpg"
    assert "第1张" in provider_calls[0]["prompt"]
    assert "PROMPT TEXT" in provider_calls[0]["prompt"]
    assert prompt_calls[0]["vision_analysis"] == {"background": "studio", "lighting": "soft"}
    assert persist_calls[0]["raw_content"] == b"raw-image-bytes"
    assert persist_calls[0]["watermarked_content"] == b"watermarked-bytes"
    assert persist_calls[0]["raw_metadata"]["prompt_hash"] == "a" * 64


def test_generation_task_delegates_to_sync_runner(monkeypatch):
    called = {}

    def fake_sync_runner(job_id):
        called["job_id"] = job_id
        return {"job_id": job_id}

    monkeypatch.setattr("app.workers.tasks.run_generation_job_sync", fake_sync_runner)
    assert process_generation_task("job-123") == {"job_id": "job-123"}
    assert called["job_id"] == "job-123"
