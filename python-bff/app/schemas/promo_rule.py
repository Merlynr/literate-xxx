from __future__ import annotations
import uuid
from pydantic import BaseModel


class PromoRuleCreate(BaseModel):
    name: str
    slot_template: dict | None = None
    term_selection_strategy: str = "weighted_random"
    aspect_ratio: str = "1:1"
    watermark_config: dict | None = None
    is_active: bool = True


class PromoRuleUpdate(BaseModel):
    name: str | None = None
    slot_template: dict | None = None
    term_selection_strategy: str | None = None
    aspect_ratio: str | None = None
    watermark_config: dict | None = None
    is_active: bool | None = None


class PromoRuleOut(BaseModel):
    id: uuid.UUID
    name: str
    slot_template: dict | None
    term_selection_strategy: str
    aspect_ratio: str
    watermark_config: dict | None
    version: int
    is_active: bool

    class Config:
        from_attributes = True
