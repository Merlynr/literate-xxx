from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_tenant_id, get_db
from app.schemas.quota import (
    QuotaEstimateRequest,
    QuotaEstimateResponse,
    QuotaLedgerItem,
    QuotaSummary,
)
from app.services.quota_service import (
    estimate_quota_cost,
    get_quota_snapshot,
    list_quota_ledger,
)

router = APIRouter(prefix="/quota", tags=["quota"])


@router.get("/summary", response_model=QuotaSummary)
async def quota_summary(
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    snapshot = await get_quota_snapshot(db, tenant_id)
    return QuotaSummary(
        total_units=snapshot.total_units,
        available_units=snapshot.available_units,
        frozen_units=snapshot.frozen_units,
        active_plan_name=snapshot.active_plan_name,
        updated_at=snapshot.updated_at,
    )


@router.post("/estimate", response_model=QuotaEstimateResponse)
async def quota_estimate(
    _: QuotaEstimateRequest,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    return QuotaEstimateResponse(**await estimate_quota_cost(db, tenant_id))


@router.get("/admin/quota-ledger", response_model=list[QuotaLedgerItem])
async def admin_quota_ledger(
    tenant_id: uuid.UUID | None = Query(default=None),
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    return await list_quota_ledger(db, tenant_id=tenant_id, offset=offset, limit=limit)
