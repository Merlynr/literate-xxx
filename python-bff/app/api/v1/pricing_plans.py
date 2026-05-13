from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.pricing_plan import PricingPlan
from app.schemas.quota import PricingPlanCreate, PricingPlanOut, PricingPlanUpdate

router = APIRouter(prefix="/admin/pricing-plans", tags=["pricing-plans"])


@router.get("", response_model=list[PricingPlanOut])
async def list_pricing_plans(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(PricingPlan).order_by(PricingPlan.sort_order.asc(), PricingPlan.id.asc())
    )
    return result.scalars().all()


@router.post("", response_model=PricingPlanOut, status_code=status.HTTP_201_CREATED)
async def create_pricing_plan(body: PricingPlanCreate, db: AsyncSession = Depends(get_db)):
    plan = PricingPlan(**body.model_dump())
    db.add(plan)
    await db.flush()
    await db.refresh(plan)
    return plan


@router.put("/{plan_id}", response_model=PricingPlanOut)
async def update_pricing_plan(
    plan_id: int,
    body: PricingPlanUpdate,
    db: AsyncSession = Depends(get_db),
):
    plan = await db.get(PricingPlan, plan_id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pricing plan not found")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(plan, key, value)
    await db.flush()
    await db.refresh(plan)
    return plan


@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pricing_plan(plan_id: int, db: AsyncSession = Depends(get_db)):
    plan = await db.get(PricingPlan, plan_id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pricing plan not found")
    plan.is_active = False
    await db.flush()
