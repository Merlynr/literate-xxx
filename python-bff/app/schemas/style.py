from __future__ import annotations
import uuid
from pydantic import BaseModel


class StyleCreate(BaseModel):
    name: str
    cover_image_url: str = ""
    rule_version: int = 1
    sort_order: int = 0
    is_active: bool = True


class StyleUpdate(BaseModel):
    name: str | None = None
    cover_image_url: str | None = None
    rule_version: int | None = None
    sort_order: int | None = None
    is_active: bool | None = None


class StyleOut(BaseModel):
    id: uuid.UUID
    name: str
    cover_image_url: str
    rule_version: int
    sort_order: int
    is_active: bool

    class Config:
        from_attributes = True
