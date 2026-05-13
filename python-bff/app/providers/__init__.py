from __future__ import annotations

from app.providers.base import (
    DEFAULT_PROVIDER_NAME,
    DEFAULT_IMAGE_GEN_MODEL,
    DEFAULT_VISION_MODEL,
    ImageGenerationProvider,
    ProviderRegistry,
    VisionProvider,
)
from app.providers.image_gen.dashscope_wanxiang import (
    DashScopeWanxiangImageGenProvider,
    WanxiangImageGenerationProvider,
)
from app.providers.vision.dashscope import DashScopeVisionProvider


def build_default_provider_registry() -> ProviderRegistry:
    registry = ProviderRegistry()
    registry.register_vision_provider(DashScopeVisionProvider())
    registry.register_image_generation_provider(DashScopeWanxiangImageGenProvider())
    registry.default_vision_provider = DEFAULT_PROVIDER_NAME
    registry.default_image_generation_provider = DEFAULT_PROVIDER_NAME
    return registry


DEFAULT_PROVIDER_REGISTRY = build_default_provider_registry()


def get_vision_provider(name: str | None = None) -> VisionProvider:
    return DEFAULT_PROVIDER_REGISTRY.get_vision_provider(name)


def get_image_generation_provider(name: str | None = None) -> ImageGenerationProvider:
    return DEFAULT_PROVIDER_REGISTRY.get_image_generation_provider(name)


def list_provider_names() -> list[str]:
    return sorted(
        set(DEFAULT_PROVIDER_REGISTRY.vision_providers) | set(DEFAULT_PROVIDER_REGISTRY.image_generation_providers)
    )


# Backward-compatible aliases used by the wave 1 worker scaffold.
IMAGE_GEN_PROVIDER_NAME = DEFAULT_PROVIDER_NAME
VISION_PROVIDER_NAME = DEFAULT_PROVIDER_NAME
get_provider = get_image_generation_provider


__all__ = [
    "DEFAULT_PROVIDER_NAME",
    "DEFAULT_IMAGE_GEN_MODEL",
    "DEFAULT_VISION_MODEL",
    "DEFAULT_PROVIDER_REGISTRY",
    "DashScopeVisionProvider",
    "DashScopeWanxiangImageGenProvider",
    "WanxiangImageGenerationProvider",
    "ImageGenerationProvider",
    "ProviderRegistry",
    "VisionProvider",
    "IMAGE_GEN_PROVIDER_NAME",
    "VISION_PROVIDER_NAME",
    "build_default_provider_registry",
    "get_provider",
    "get_image_generation_provider",
    "get_vision_provider",
    "list_provider_names",
]
