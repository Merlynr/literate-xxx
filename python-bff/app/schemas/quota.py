from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class QuotaSummary(BaseModel):
    total_units: int
    available_units: int
    frozen_units: int
    active_plan_name: str | None = None
    updated_at: datetime | None = None


class QuotaEstimateRequest(BaseModel):
    category_id: uuid.UUID | None = None
    style_id: uuid.UUID | None = None
    source_asset_id: uuid.UUID | None = None
    prompt_hint: str = Field(default="", max_length=1000)


class QuotaEstimateResponse(BaseModel):
    estimated_units: int
    price_cents: int
    plan_code: str


class QuotaLedgerItem(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    job_id: uuid.UUID | None
    plan_id: int | None
    event_type: str
    delta_units: int
    available_before: int
    available_after: int
    frozen_before: int
    frozen_after: int
    reason: str
    created_at: datetime

    class Config:
        from_attributes = True


class PricingPlanBase(BaseModel):
    plan_code: str
    plan_name: str
    quota_units: int = 100
    price_cents: int = 0
    valid_days: int = 30
    is_active: bool = True
    sort_order: int = 0


class PricingPlanCreate(PricingPlanBase):
    pass


class PricingPlanUpdate(BaseModel):
    plan_name: str | None = None
    quota_units: int | None = None
    price_cents: int | None = None
    valid_days: int | None = None
    is_active: bool | None = None
    sort_order: int | None = None


class PricingPlanOut(PricingPlanBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
