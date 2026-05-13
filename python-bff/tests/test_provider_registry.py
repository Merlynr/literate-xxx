from __future__ import annotations

import pytest

from app.providers import (
    DEFAULT_PROVIDER_NAME,
    DEFAULT_PROVIDER_REGISTRY,
    DashScopeVisionProvider,
    DashScopeWanxiangImageGenProvider,
    IMAGE_GEN_PROVIDER_NAME,
    get_image_generation_provider,
    get_provider,
    get_vision_provider,
    build_default_provider_registry,
)


def test_default_provider_registry_uses_dashscope_wanxiang():
    registry = build_default_provider_registry()
    vision_provider = registry.get_vision_provider()
    image_provider = registry.get_image_generation_provider()
    assert isinstance(vision_provider, DashScopeVisionProvider)
    assert isinstance(image_provider, DashScopeWanxiangImageGenProvider)


def test_provider_aliases_point_to_the_default_dashscope_registry():
    assert DEFAULT_PROVIDER_NAME == IMAGE_GEN_PROVIDER_NAME
    assert isinstance(get_provider(), DashScopeWanxiangImageGenProvider)
    assert isinstance(get_image_generation_provider(), DashScopeWanxiangImageGenProvider)
    assert isinstance(get_vision_provider(), DashScopeVisionProvider)


def test_registry_rejects_unknown_names():
    with pytest.raises(KeyError):
        DEFAULT_PROVIDER_REGISTRY.get_vision_provider("unknown")
    with pytest.raises(KeyError):
        DEFAULT_PROVIDER_REGISTRY.get_image_generation_provider("unknown")
