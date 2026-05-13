"""Seed default category/style/term/promo-rule data for local development."""

from __future__ import annotations

import argparse
import asyncio
import pathlib
import sys
import uuid

# Ensure the project root is importable when the script is run directly.
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import select

from app.core.database import async_session_factory, engine
from app.models.category import Category
from app.models.promo_rule import PromoRule
from app.models.style import Style
from app.models.term import Term
from app.models.tenant import Tenant


DEFAULT_TENANT_NAME = "Local Dev Tenant"


DEFAULT_CATEGORIES = [
    {"category_code": "red_potato", "name": "红皮土豆", "sort_order": 1},
    {"category_code": "black_pearl_potato", "name": "黑珍珠土豆", "sort_order": 2},
    {"category_code": "yellow_potato", "name": "黄心土豆", "sort_order": 3},
    {"category_code": "mini_potato", "name": "小土豆", "sort_order": 4},
    {"category_code": "potato_gift_box", "name": "土豆礼盒", "sort_order": 5},
]

DEFAULT_STYLES = [
    {"name": "清新田园", "sort_order": 1},
    {"name": "高级电商", "sort_order": 2},
    {"name": "自然原产地", "sort_order": 3},
    {"name": "节日礼盒", "sort_order": 4},
]

DEFAULT_TERMS = [
    {"type": "positive", "content": "新鲜现采", "weight": 12, "sort_order": 1},
    {"type": "positive", "content": "产地直供", "weight": 11, "sort_order": 2},
    {"type": "positive", "content": "颗粒饱满", "weight": 10, "sort_order": 3},
    {"type": "positive", "content": "沙糯粉面", "weight": 10, "sort_order": 4},
    {"type": "positive", "content": "适合炖煮", "weight": 9, "sort_order": 5},
    {"type": "negative", "content": "模糊", "weight": 10, "sort_order": 1},
    {"type": "negative", "content": "低清", "weight": 10, "sort_order": 2},
    {"type": "negative", "content": "噪点", "weight": 10, "sort_order": 3},
    {"type": "prefix", "content": "突出商品主体", "weight": 10, "sort_order": 1},
    {"type": "prefix", "content": "保留包装识别信息", "weight": 10, "sort_order": 2},
    {"type": "brand", "content": "XX甄选", "weight": 10, "sort_order": 1},
]

DEFAULT_PROMO_RULE = {
    "name": "默认宣传规则",
    "slot_template": {
        "title": "卖点标题",
        "headline_limit": 18,
        "subheadline_limit": 24,
        "bullet_count": 3,
        "layout": "left_text_right_product",
        "tone": "commercial_clean",
    },
    "term_selection_strategy": "weighted_random",
    "aspect_ratio": "1:1",
    "watermark_config": {
        "text": "XX甄选",
        "position": "bottom_right",
        "opacity": 0.18,
    },
    "version": 1,
}


async def _get_or_create_tenant(session, tenant_id: uuid.UUID | None) -> Tenant:
    if tenant_id is not None:
        tenant = await session.get(Tenant, tenant_id)
        if tenant is None:
            raise RuntimeError(f"Tenant {tenant_id} not found")
        return tenant

    tenant = await session.scalar(select(Tenant).where(Tenant.name == DEFAULT_TENANT_NAME))
    if tenant is not None:
        return tenant

    tenant = Tenant(name=DEFAULT_TENANT_NAME)
    session.add(tenant)
    await session.flush()
    await session.refresh(tenant)
    return tenant


async def _upsert_category(session, tenant_id: uuid.UUID, payload: dict) -> str:
    existing = await session.scalar(
        select(Category).where(Category.category_code == payload["category_code"])
    )
    if existing:
        return "unchanged"

    session.add(
        Category(
            tenant_id=tenant_id,
            category_code=payload["category_code"],
            name=payload["name"],
            sort_order=payload["sort_order"],
            is_active=True,
        )
    )
    return "created"


async def _upsert_style(session, tenant_id: uuid.UUID, payload: dict) -> str:
    existing = await session.scalar(
        select(Style).where(Style.tenant_id == tenant_id, Style.name == payload["name"])
    )
    if existing:
        return "unchanged"

    session.add(
        Style(
            tenant_id=tenant_id,
            name=payload["name"],
            cover_image_url="",
            rule_version=1,
            sort_order=payload["sort_order"],
            is_active=True,
        )
    )
    return "created"


async def _upsert_term(session, tenant_id: uuid.UUID, payload: dict) -> str:
    existing = await session.scalar(
        select(Term).where(
            Term.tenant_id == tenant_id,
            Term.type == payload["type"],
            Term.content == payload["content"],
        )
    )
    if existing:
        return "unchanged"

    session.add(
        Term(
            tenant_id=tenant_id,
            type=payload["type"],
            content=payload["content"],
            weight=payload["weight"],
            sort_order=payload["sort_order"],
            scope=None,
            is_active=True,
        )
    )
    return "created"


async def _upsert_promo_rule(session, tenant_id: uuid.UUID, payload: dict) -> str:
    existing = await session.scalar(
        select(PromoRule).where(PromoRule.tenant_id == tenant_id, PromoRule.name == payload["name"])
    )
    if existing:
        return "unchanged"

    session.add(
        PromoRule(
            tenant_id=tenant_id,
            name=payload["name"],
            slot_template=payload["slot_template"],
            term_selection_strategy=payload["term_selection_strategy"],
            aspect_ratio=payload["aspect_ratio"],
            watermark_config=payload["watermark_config"],
            version=payload["version"],
            is_active=True,
        )
    )
    return "created"


async def seed_default_data(*, tenant_id: uuid.UUID | None = None) -> dict[str, int]:
    summary = {"created": 0, "updated": 0, "unchanged": 0}
    async with async_session_factory() as session:
        tenant = await _get_or_create_tenant(session, tenant_id)

        for payload in DEFAULT_CATEGORIES:
            result = await _upsert_category(session, tenant.id, payload)
            summary[result] += 1

        for payload in DEFAULT_STYLES:
            result = await _upsert_style(session, tenant.id, payload)
            summary[result] += 1

        for payload in DEFAULT_TERMS:
            result = await _upsert_term(session, tenant.id, payload)
            summary[result] += 1

        result = await _upsert_promo_rule(session, tenant.id, DEFAULT_PROMO_RULE)
        summary[result] += 1

        await session.commit()
        print(f"Seeded tenant: {tenant.id} ({tenant.name})")
    await engine.dispose()
    return summary


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed default data for XXZX local development")
    parser.add_argument("--tenant-id", type=uuid.UUID, default=None, help="Target tenant UUID")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    summary = asyncio.run(seed_default_data(tenant_id=args.tenant_id))
    print(
        "Seed summary:",
        f"created={summary['created']}",
        f"updated={summary['updated']}",
        f"unchanged={summary['unchanged']}",
    )


if __name__ == "__main__":
    main()
