from __future__ import annotations
import uuid
from typing import Type, TypeVar, Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.base import TenantModel

T = TypeVar("T", bound=TenantModel)


async def list_items(
    db: AsyncSession,
    model: Type[T],
    tenant_id: uuid.UUID,
    *,
    is_active: bool | None = True,
    offset: int = 0,
    limit: int = 100,
) -> Sequence[T]:
    """List items scoped to tenant with optional is_active filter."""
    stmt = select(model).where(model.tenant_id == tenant_id)
    if is_active is not None:
        stmt = stmt.where(model.is_active == is_active)
    stmt = stmt.offset(offset).limit(limit)
    if hasattr(model, "sort_order"):
        stmt = stmt.order_by(model.sort_order.asc())
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_item(
    db: AsyncSession,
    model: Type[T],
    item_id: uuid.UUID,
    tenant_id: uuid.UUID,
) -> T | None:
    """Get a single item by ID, scoped to tenant."""
    result = await db.execute(
        select(model).where(model.id == item_id, model.tenant_id == tenant_id)
    )
    return result.scalar_one_or_none()


async def create_item(
    db: AsyncSession,
    model: Type[T],
    tenant_id: uuid.UUID,
    **kwargs,
) -> T:
    """Create a new item with tenant_id injected."""
    item = model(tenant_id=tenant_id, **kwargs)
    db.add(item)
    await db.flush()
    return item


async def update_item(
    db: AsyncSession,
    model: Type[T],
    item_id: uuid.UUID,
    tenant_id: uuid.UUID,
    **kwargs,
) -> T | None:
    """Update an item's fields. Only non-None values in kwargs are applied."""
    item = await get_item(db, model, item_id, tenant_id)
    if not item:
        return None
    for key, value in kwargs.items():
        if value is not None and hasattr(item, key):
            setattr(item, key, value)
    await db.flush()
    return item


async def delete_item(
    db: AsyncSession,
    model: Type[T],
    item_id: uuid.UUID,
    tenant_id: uuid.UUID,
) -> bool:
    """Soft-delete by setting is_active=False. Returns True if item was found."""
    item = await get_item(db, model, item_id, tenant_id)
    if not item:
        return False
    item.is_active = False
    await db.flush()
    return True
