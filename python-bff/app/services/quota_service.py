from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pricing_plan import PricingPlan
from app.models.quota_account import QuotaAccount
from app.models.quota_ledger import QuotaLedgerEntry


DEFAULT_PLAN_CODE = "DEFAULT_100"


@dataclass(frozen=True)
class QuotaSnapshot:
    total_units: int
    available_units: int
    frozen_units: int
    active_plan_id: int | None
    active_plan_name: str | None
    updated_at: datetime | None


async def get_active_plan(db: AsyncSession) -> PricingPlan:
    plan = await db.scalar(
        select(PricingPlan)
        .where(PricingPlan.is_active.is_(True))
        .order_by(PricingPlan.sort_order.asc(), PricingPlan.id.asc())
    )
    if plan:
        return plan

    plan = PricingPlan(
        plan_code=DEFAULT_PLAN_CODE,
        plan_name="Default 100",
        quota_units=100,
        price_cents=0,
        valid_days=30,
        is_active=True,
        sort_order=0,
    )
    db.add(plan)
    await db.flush()
    await db.refresh(plan)
    return plan


async def get_or_create_quota_account(db: AsyncSession, tenant_id: uuid.UUID) -> QuotaAccount:
    account = await db.scalar(select(QuotaAccount).where(QuotaAccount.tenant_id == tenant_id))
    if account:
        return account

    plan = await get_active_plan(db)
    account = QuotaAccount(
        tenant_id=tenant_id,
        total_units=plan.quota_units,
        available_units=plan.quota_units,
        frozen_units=0,
        active_plan_id=plan.id,
    )
    db.add(account)
    await db.flush()
    await db.refresh(account)
    return account


async def _add_ledger_entry(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    job_id: uuid.UUID | None,
    plan_id: int | None,
    event_type: str,
    delta_units: int,
    available_before: int,
    available_after: int,
    frozen_before: int,
    frozen_after: int,
    reason: str,
    metadata: dict[str, Any] | None = None,
) -> QuotaLedgerEntry:
    entry = QuotaLedgerEntry(
        tenant_id=tenant_id,
        job_id=job_id,
        plan_id=plan_id,
        event_type=event_type,
        delta_units=delta_units,
        available_before=available_before,
        available_after=available_after,
        frozen_before=frozen_before,
        frozen_after=frozen_after,
        reason=reason,
        metadata_json=metadata,
    )
    db.add(entry)
    await db.flush()
    await db.refresh(entry)
    return entry


async def freeze_quota(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    job_id: uuid.UUID,
    units: int,
    reason: str,
) -> QuotaAccount:
    account = await get_or_create_quota_account(db, tenant_id)
    if account.available_units < units:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient quota",
        )
    before_available = account.available_units
    before_frozen = account.frozen_units
    account.available_units -= units
    account.frozen_units += units
    account.total_units = account.available_units + account.frozen_units
    await _add_ledger_entry(
        db,
        tenant_id=tenant_id,
        job_id=job_id,
        plan_id=account.active_plan_id,
        event_type="freeze",
        delta_units=units,
        available_before=before_available,
        available_after=account.available_units,
        frozen_before=before_frozen,
        frozen_after=account.frozen_units,
        reason=reason,
    )
    await db.flush()
    await db.refresh(account)
    return account


async def commit_quota_deduction(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    job_id: uuid.UUID,
    units: int,
    reason: str,
) -> QuotaAccount:
    account = await get_or_create_quota_account(db, tenant_id)
    if account.frozen_units < units:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Frozen quota is not sufficient",
        )
    before_available = account.available_units
    before_frozen = account.frozen_units
    account.frozen_units -= units
    account.total_units = account.available_units + account.frozen_units
    await _add_ledger_entry(
        db,
        tenant_id=tenant_id,
        job_id=job_id,
        plan_id=account.active_plan_id,
        event_type="deduct",
        delta_units=-units,
        available_before=before_available,
        available_after=account.available_units,
        frozen_before=before_frozen,
        frozen_after=account.frozen_units,
        reason=reason,
    )
    await db.flush()
    await db.refresh(account)
    return account


async def release_quota(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    job_id: uuid.UUID,
    units: int,
    reason: str,
) -> QuotaAccount:
    account = await get_or_create_quota_account(db, tenant_id)
    if account.frozen_units < units:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Frozen quota is not sufficient",
        )
    before_available = account.available_units
    before_frozen = account.frozen_units
    account.available_units += units
    account.frozen_units -= units
    account.total_units = account.available_units + account.frozen_units
    await _add_ledger_entry(
        db,
        tenant_id=tenant_id,
        job_id=job_id,
        plan_id=account.active_plan_id,
        event_type="release",
        delta_units=units,
        available_before=before_available,
        available_after=account.available_units,
        frozen_before=before_frozen,
        frozen_after=account.frozen_units,
        reason=reason,
    )
    await db.flush()
    await db.refresh(account)
    return account


async def get_quota_snapshot(db: AsyncSession, tenant_id: uuid.UUID) -> QuotaSnapshot:
    account = await get_or_create_quota_account(db, tenant_id)
    plan_name = None
    if account.active_plan_id is not None:
        plan = await db.get(PricingPlan, account.active_plan_id)
        if not plan:
            plan = await get_active_plan(db)
            account.active_plan_id = plan.id
            await db.flush()
        plan_name = plan.plan_name if plan else None
    return QuotaSnapshot(
        total_units=account.total_units,
        available_units=account.available_units,
        frozen_units=account.frozen_units,
        active_plan_id=account.active_plan_id,
        active_plan_name=plan_name,
        updated_at=account.updated_at,
    )


async def estimate_quota_cost(db: AsyncSession, tenant_id: uuid.UUID) -> dict[str, Any]:
    account = await get_or_create_quota_account(db, tenant_id)
    plan = None
    if account.active_plan_id is not None:
        plan = await db.get(PricingPlan, account.active_plan_id)
    if not plan:
        plan = await get_active_plan(db)
        account.active_plan_id = plan.id
        await db.flush()
    return {
        "estimated_units": 1,
        "price_cents": plan.price_cents,
        "plan_code": plan.plan_code,
    }


async def list_quota_ledger(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID | None = None,
    offset: int = 0,
    limit: int = 100,
) -> list[QuotaLedgerEntry]:
    stmt = select(QuotaLedgerEntry).order_by(QuotaLedgerEntry.created_at.desc())
    if tenant_id:
        stmt = stmt.where(QuotaLedgerEntry.tenant_id == tenant_id)
    result = await db.execute(stmt.offset(offset).limit(limit))
    return list(result.scalars().all())
