from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_dev_login_and_me(client, monkeypatch):
    monkeypatch.setattr("app.core.config.settings.DEBUG", True, raising=False)

    resp = await client.post(
        "/api/v1/auth/dev-login",
        json={"nickname": "本地调试", "avatar_url": ""},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["access_token"]
    assert data["refresh_token"]

    me_resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {data['access_token']}"},
    )
    assert me_resp.status_code == 200
    profile = me_resp.json()
    assert profile["openid"] == "dev-local-openid"
    assert profile["nickname"] == "本地调试"
