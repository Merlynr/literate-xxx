from __future__ import annotations
import uuid
import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_user
from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.models.user import User
from app.models.tenant import Tenant
from app.schemas.auth import (
    DevLoginRequest,
    WechatLoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    UserProfile,
)

router = APIRouter(prefix="/auth", tags=["auth"])
DEV_LOGIN_OPENID = "dev-local-openid"


def _issue_tokens(user: User) -> TokenResponse:
    user_id_str = str(user.id)
    tenant_id_str = str(user.tenant_id)
    return TokenResponse(
        access_token=create_access_token(user_id_str, tenant_id_str),
        refresh_token=create_refresh_token(user_id_str, tenant_id_str),
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


async def _get_or_create_dev_user(
    db: AsyncSession,
    *,
    nickname: str = "本地调试",
    avatar_url: str = "",
) -> User:
    result = await db.execute(select(User).where(User.openid == DEV_LOGIN_OPENID))
    user = result.scalar_one_or_none()
    if user:
        return user

    tenant = Tenant(name="Local Dev Tenant")
    db.add(tenant)
    await db.flush()
    await db.refresh(tenant)

    user = User(
        openid=DEV_LOGIN_OPENID,
        nickname=nickname,
        avatar_url=avatar_url,
        tenant_id=tenant.id,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
async def wechat_login(body: WechatLoginRequest, db: AsyncSession = Depends(get_db)):
    """WeChat login: code -> openid -> create/find user -> issue JWT pair."""
    # 1. Call WeChat code2session API
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://api.weixin.qq.com/sns/jscode2session",
            params={
                "appid": settings.WX_APP_ID,
                "secret": settings.WX_APP_SECRET,
                "js_code": body.code,
                "grant_type": "authorization_code",
            },
            timeout=10.0,
        )
    data = resp.json()
    openid = data.get("openid")
    if not openid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"WeChat login failed: {data.get('errmsg', 'unknown error')}",
        )

    # 2. Find or create user + tenant
    result = await db.execute(select(User).where(User.openid == openid))
    user = result.scalar_one_or_none()

    if not user:
        # First login: create tenant then user
        tenant = Tenant(name=f"Tenant-{openid[:8]}")
        db.add(tenant)
        await db.flush()  # get tenant.id
        await db.refresh(tenant)

        user = User(
            openid=openid,
            nickname="",
            avatar_url="",
            tenant_id=tenant.id,
        )
        db.add(user)
        await db.flush()
        await db.refresh(user)

    return _issue_tokens(user)


@router.post("/dev-login", response_model=TokenResponse)
async def dev_login(body: DevLoginRequest | None = None, db: AsyncSession = Depends(get_db)):
    """Local development login. Only available when DEBUG=true."""
    if not settings.DEBUG:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    payload = body or DevLoginRequest()
    user = await _get_or_create_dev_user(
        db,
        nickname=payload.nickname,
        avatar_url=payload.avatar_url,
    )
    return _issue_tokens(user)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(body: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    """Exchange a valid refresh_token for a new token pair."""
    payload = decode_token(body.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    user_id = payload["sub"]
    tenant_id = payload["tenant_id"]

    # Verify user still exists
    result = await db.execute(
        select(User).where(User.id == uuid.UUID(user_id))
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return TokenResponse(
        access_token=create_access_token(user_id, tenant_id),
        refresh_token=create_refresh_token(user_id, tenant_id),
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.get("/me", response_model=UserProfile)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current authenticated user profile."""
    return current_user
