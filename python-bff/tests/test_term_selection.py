from __future__ import annotations

from types import SimpleNamespace

from app.services.term_selection import resolve_terms, term_matches_scope


def _term(**kwargs):
    defaults = {
        "id": "term-id",
        "type": "positive",
        "content": "默认词条",
        "weight": 10,
        "sort_order": 0,
        "scope": None,
        "is_active": True,
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def test_term_matches_scope_filters_by_category_and_style():
    scoped = _term(scope={"category_ids": ["cat-1"], "style_ids": ["style-1"]})
    assert term_matches_scope(scoped, category_id="cat-1", style_id="style-1") is True
    assert term_matches_scope(scoped, category_id="cat-2", style_id="style-1") is False
    assert term_matches_scope(_term(scope=None), category_id=None, style_id=None) is True


def test_resolve_terms_weighted_random_is_deterministic_with_seed():
    terms = [
        _term(id="p1", type="prefix", content="突出商品主体", sort_order=1),
        _term(id="p2", type="prefix", content="保留包装识别信息", sort_order=2),
        _term(id="n1", type="negative", content="模糊"),
        _term(id="pos1", type="positive", content="新鲜现采", weight=12),
        _term(id="pos2", type="positive", content="产地直供", weight=11),
        _term(id="pos3", type="positive", content="颗粒饱满", weight=10),
        _term(id="pos4", type="positive", content="沙糯粉面", weight=9),
        _term(id="b1", type="brand", content="XX甄选"),
    ]

    first = resolve_terms(terms, seed="req-1")
    second = resolve_terms(terms, seed="req-1")

    assert first == second
    assert [term["type"] for term in first] == ["prefix", "prefix", "negative", "positive", "positive", "positive", "brand"]
    assert "突出商品主体" in [term["content"] for term in first]
    assert "模糊" in [term["content"] for term in first]
    assert "XX甄选" in [term["content"] for term in first]


def test_resolve_terms_all_strategy_includes_every_matching_term():
    terms = [
        _term(id="pos1", type="positive", content="A"),
        _term(id="pos2", type="positive", content="B"),
        _term(id="pos3", type="positive", content="C"),
    ]

    resolved = resolve_terms(terms, strategy="all")

    assert [term["content"] for term in resolved] == ["A", "B", "C"]
