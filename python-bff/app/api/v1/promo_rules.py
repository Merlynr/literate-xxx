from __future__ import annotations
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_tenant_id
from app.models.promo_rule import PromoRule
from app.schemas.promo_rule import PromoRuleCreate, PromoRuleUpdate, PromoRuleOut
from app.services.crud import list_items, get_item, create_item, update_item, delete_item

router = APIRouter(prefix="/promo-rules", tags=["promo-rules"])


@router.get("/", response_model=list[PromoRuleOut])
async def list_promo_rules(
    is_active: bool | None = Query(True),
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    return await list_items(db, PromoRule, tenant_id, is_active=is_active, offset=offset, limit=limit)


@router.post("/", response_model=PromoRuleOut, status_code=status.HTTP_201_CREATED)
async def create_promo_rule(
    body: PromoRuleCreate,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    return await create_item(db, PromoRule, tenant_id, **body.model_dump())


@router.get("/{item_id}", response_model=PromoRuleOut)
async def get_promo_rule(
    item_id: uuid.UUID,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    item = await get_item(db, PromoRule, item_id, tenant_id)
    if not item:
        raise HTTPException(status_code=404, detail="PromoRule not found")
    return item


@router.put("/{item_id}", response_model=PromoRuleOut)
async def update_promo_rule(
    item_id: uuid.UUID,
    body: PromoRuleUpdate,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    item = await update_item(db, PromoRule, item_id, tenant_id, **body.model_dump(exclude_unset=True))
    if not item:
        raise HTTPException(status_code=404, detail="PromoRule not found")
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_promo_rule(
    item_id: uuid.UUID,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    ok = await delete_item(db, PromoRule, item_id, tenant_id)
    if not ok:
        raise HTTPException(status_code=404, detail="PromoRule not found")
