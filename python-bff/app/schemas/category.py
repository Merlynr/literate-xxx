from __future__ import annotations
import uuid
from pydantic import BaseModel


class CategoryCreate(BaseModel):
    category_code: str
    name: str
    sort_order: int = 0
    is_active: bool = True


class CategoryUpdate(BaseModel):
    name: str | None = None
    sort_order: int | None = None
    is_active: bool | None = None


class CategoryOut(BaseModel):
    id: uuid.UUID
    category_code: str
    name: str
    sort_order: int
    is_active: bool

    class Config:
        from_attributes = True
