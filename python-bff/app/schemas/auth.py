from __future__ import annotations
import uuid
from pydantic import BaseModel


class WechatLoginRequest(BaseModel):
    code: str  # wx.login() code


class DevLoginRequest(BaseModel):
    nickname: str = "本地调试"
    avatar_url: str = ""


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class TokenPayload(BaseModel):
    sub: str  # user_id (UUID string)
    tenant_id: str  # tenant_id (UUID string)
    type: str  # "access" or "refresh"
    exp: int
    iat: int


class UserProfile(BaseModel):
    id: uuid.UUID
    openid: str
    nickname: str
    avatar_url: str
    tenant_id: uuid.UUID

    class Config:
        from_attributes = True
