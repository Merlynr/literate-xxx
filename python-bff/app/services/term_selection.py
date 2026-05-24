from __future__ import annotations

import random
import uuid
from typing import Any, Mapping, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.term import Term


def _freeze_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _freeze_json(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_freeze_json(item) for item in value]
    return value


def _term_attr(term: Term | Mapping[str, Any], name: str, default: Any = None) -> Any:
    if isinstance(term, Mapping):
        return term.get(name, default)
    return getattr(term, name, default)


def _term_snapshot(term: Term | Mapping[str, Any]) -> dict[str, Any]:
    return {
        "id": str(_term_attr(term, "id") or ""),
        "type": str(_term_attr(term, "type") or ""),
        "content": str(_term_attr(term, "content") or ""),
        "weight": int(_term_attr(term, "weight") or 0),
        "sort_order": int(_term_attr(term, "sort_order") or 0),
        "scope": _freeze_json(_term_attr(term, "scope")),
    }


def term_matches_scope(
    term: Term | Mapping[str, Any],
    *,
    category_id: uuid.UUID | str | None,
    style_id: uuid.UUID | str | None,
) -> bool:
    scope = _term_attr(term, "scope")
    if not scope:
        return True

    category_ids = scope.get("category_ids") or []
    style_ids = scope.get("style_ids") or []
    if category_ids:
        if not category_id or str(category_id) not in {str(item) for item in category_ids}:
            return False
    if style_ids:
        if not style_id or str(style_id) not in {str(item) for item in style_ids}:
            return False
    return True


def resolve_terms(
    terms: Sequence[Term | Mapping[str, Any]],
    *,
    category_id: uuid.UUID | str | None = None,
    style_id: uuid.UUID | str | None = None,
    strategy: str = "weighted_random",
    seed: str | None = None,
) -> list[dict[str, Any]]:
    matched: list[Term | Mapping[str, Any]] = []
    for term in terms:
        if not _term_attr(term, "is_active", True):
            continue
        if term_matches_scope(term, category_id=category_id, style_id=style_id):
            matched.append(term)

    by_type: dict[str, list[Term | Mapping[str, Any]]] = {}
    for term in matched:
        term_type = str(_term_attr(term, "type") or "")
        by_type.setdefault(term_type, []).append(term)

    def sort_key(term: Term | Mapping[str, Any]) -> tuple[int, int]:
        return (int(_term_attr(term, "sort_order") or 0), -int(_term_attr(term, "weight") or 0))

    resolved: list[dict[str, Any]] = []
    if strategy == "all":
        for term_type in ("prefix", "positive", "brand", "negative"):
            for term in sorted(by_type.get(term_type, []), key=sort_key):
                resolved.append(_term_snapshot(term))
        return resolved

    rng = random.Random(seed or "")

    def weighted_pick(items: Sequence[Term | Mapping[str, Any]], count: int) -> list[Term | Mapping[str, Any]]:
        if count <= 0 or not items:
            return []
        if count >= len(items):
            return list(items)
        pool = list(items)
        selected: list[Term | Mapping[str, Any]] = []
        for _ in range(count):
            if not pool:
                break
            weights = [max(int(_term_attr(item, "weight") or 0), 1) for item in pool]
            pick = rng.choices(pool, weights=weights, k=1)[0]
            selected.append(pick)
            pool.remove(pick)
        return selected

    for term in sorted(by_type.get("prefix", []), key=sort_key):
        resolved.append(_term_snapshot(term))

    for term in sorted(by_type.get("negative", []), key=sort_key):
        resolved.append(_term_snapshot(term))

    for term in weighted_pick(sorted(by_type.get("positive", []), key=sort_key), 3):
        resolved.append(_term_snapshot(term))

    brand_terms = sorted(by_type.get("brand", []), key=sort_key)
    if brand_terms:
        weights = [max(int(_term_attr(term, "weight") or 0), 1) for term in brand_terms]
        picked = rng.choices(brand_terms, weights=weights, k=1)[0]
        resolved.append(_term_snapshot(picked))

    return resolved


async def load_active_terms(db: AsyncSession, tenant_id: uuid.UUID) -> list[Term]:
    result = await db.scalars(
        select(Term)
        .where(Term.tenant_id == tenant_id, Term.is_active.is_(True))
        .order_by(Term.sort_order.asc(), Term.weight.desc())
    )
    return list(result)


async def resolve_terms_for_generation(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    category_id: uuid.UUID | None,
    style_id: uuid.UUID | None,
    strategy: str = "weighted_random",
    seed: str,
) -> list[dict[str, Any]]:
    terms = await load_active_terms(db, tenant_id)
    return resolve_terms(
        terms,
        category_id=category_id,
        style_id=style_id,
        strategy=strategy,
        seed=seed,
    )
