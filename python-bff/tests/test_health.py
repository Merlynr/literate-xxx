from __future__ import annotations
import pytest


@pytest.mark.asyncio
async def test_liveness(client):
    resp = await client.get("/api/v1/health/liveness")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_health_alias(client):
    resp = await client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_readiness(client):
    resp = await client.get("/api/v1/health/readiness")
    assert resp.status_code == 200
    data = resp.json()
    assert "database" in data["checks"]
    assert "redis" in data["checks"]
    assert "minio" in data["checks"]
