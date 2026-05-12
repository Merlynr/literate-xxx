from __future__ import annotations
import uuid
from pydantic import BaseModel


class TermCreate(BaseModel):
    type: str  # positive, negative, prefix, brand
    content: str
    weight: int = 10
    sort_order: int = 0
    scope: dict | None = None
    is_active: bool = True


class TermUpdate(BaseModel):
    type: str | None = None
    content: str | None = None
    weight: int | None = None
    sort_order: int | None = None
    scope: dict | None = None
    is_active: bool | None = None


class TermOut(BaseModel):
    id: uuid.UUID
    type: str
    content: str
    weight: int
    sort_order: int
    scope: dict | None
    is_active: bool

    class Config:
        from_attributes = True
