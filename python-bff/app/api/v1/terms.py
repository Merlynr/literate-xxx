from __future__ import annotations
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_tenant_id
from app.models.term import Term
from app.schemas.term import TermCreate, TermUpdate, TermOut
from app.services.crud import list_items, get_item, create_item, update_item, delete_item

router = APIRouter(prefix="/terms", tags=["terms"])


@router.get("/", response_model=list[TermOut])
async def list_terms(
    is_active: bool | None = Query(True),
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    return await list_items(db, Term, tenant_id, is_active=is_active, offset=offset, limit=limit)


@router.post("/", response_model=TermOut, status_code=status.HTTP_201_CREATED)
async def create_term(
    body: TermCreate,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    return await create_item(db, Term, tenant_id, **body.model_dump())


@router.get("/{item_id}", response_model=TermOut)
async def get_term(
    item_id: uuid.UUID,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    item = await get_item(db, Term, item_id, tenant_id)
    if not item:
        raise HTTPException(status_code=404, detail="Term not found")
    return item


@router.put("/{item_id}", response_model=TermOut)
async def update_term(
    item_id: uuid.UUID,
    body: TermUpdate,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    item = await update_item(db, Term, item_id, tenant_id, **body.model_dump(exclude_unset=True))
    if not item:
        raise HTTPException(status_code=404, detail="Term not found")
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_term(
    item_id: uuid.UUID,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    ok = await delete_item(db, Term, item_id, tenant_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Term not found")
