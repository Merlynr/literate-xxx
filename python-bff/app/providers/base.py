from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
import json
from typing import Any, Mapping, Protocol, Sequence


DEFAULT_DASHSCOPE_API_BASE_URL = "https://dashscope.aliyuncs.com/api/v1"
DEFAULT_DASHSCOPE_IMAGE_GENERATION_PATH = "/services/aigc/image-generation/generation"
DEFAULT_DASHSCOPE_VISION_PATH = "/services/aigc/multimodal-generation/generation"
DEFAULT_PROVIDER_NAME = "alibaba-dashscope"
DEFAULT_IMAGE_GEN_MODEL = "wan2.7-image"
DEFAULT_VISION_MODEL = "qwen3.6-plus"


class ProviderError(RuntimeError):
    """Raised when a provider request fails or returns an unexpected payload."""


@dataclass(frozen=True)
class VisionAnalysisResult:
    provider: str
    model_name: str
    image_urls: tuple[str, ...]
    analysis: dict[str, Any]
    request_id: str | None = None
    raw_response: dict[str, Any] | None = None


@dataclass(frozen=True)
class ImageGenerationResult:
    provider: str
    model_name: str
    prompt: str
    image_urls: tuple[str, ...]
    image_url: str
    request_id: str | None = None
    task_id: str | None = None
    raw_response: dict[str, Any] | None = None


GeneratedImageResult = ImageGenerationResult


class VisionProvider(Protocol):
    name: str
    model_name: str

    async def analyze(
        self,
        *,
        image_urls: Sequence[str],
        prompt: str,
        response_format: Mapping[str, Any] | None = None,
    ) -> VisionAnalysisResult:
        raise NotImplementedError


class ImageGenerationProvider(Protocol):
    name: str
    model_name: str

    async def generate(
        self,
        *,
        prompt: str,
        image_urls: Sequence[str],
        size: str = "2K",
        watermark: bool = False,
        n: int = 1,
    ) -> ImageGenerationResult:
        raise NotImplementedError


def json_safe(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [json_safe(item) for item in value]
    if is_dataclass(value):
        return json_safe(asdict(value))
    if hasattr(value, "model_dump"):
        return json_safe(value.model_dump())  # type: ignore[no-any-return]
    if hasattr(value, "dict"):
        return json_safe(value.dict())  # type: ignore[no-any-return]
    return str(value)


def parse_json_maybe(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if is_dataclass(value):
        dumped = asdict(value)
        return dumped if isinstance(dumped, dict) else json_safe(dumped)
    if hasattr(value, "model_dump"):
        dumped = value.model_dump()  # type: ignore[call-arg]
        return dumped if isinstance(dumped, dict) else json_safe(dumped)
    if hasattr(value, "dict"):
        dumped = value.dict()  # type: ignore[call-arg]
        return dumped if isinstance(dumped, dict) else json_safe(dumped)
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return {}
        return json.loads(stripped)
    return json_safe(value)


def _extract_output_container(payload: Any) -> Any:
    if isinstance(payload, Mapping):
        return payload.get("output", payload)
    if hasattr(payload, "output"):
        return getattr(payload, "output")
    return payload


def _extract_choices(container: Any) -> list[Any]:
    if isinstance(container, Mapping):
        return list(container.get("choices") or [])
    if hasattr(container, "choices"):
        return list(getattr(container, "choices") or [])
    return []


def _extract_message(choice: Any) -> Any:
    if isinstance(choice, Mapping):
        return choice.get("message")
    if hasattr(choice, "message"):
        return getattr(choice, "message")
    return None


def _extract_content(message: Any) -> Any:
    if isinstance(message, Mapping):
        return message.get("content")
    if hasattr(message, "content"):
        return getattr(message, "content")
    return None


def extract_first_text(payload: Any) -> str:
    container = _extract_output_container(payload)
    for choice in _extract_choices(container):
        message = _extract_message(choice)
        content = _extract_content(message)
        if isinstance(content, str) and content.strip():
            return content.strip()
        if isinstance(content, Sequence) and not isinstance(content, (str, bytes, bytearray)):
            for part in content:
                if isinstance(part, Mapping):
                    text = part.get("text")
                    if isinstance(text, str) and text.strip():
                        return text.strip()
    if isinstance(container, Mapping):
        text = container.get("text")
        if isinstance(text, str) and text.strip():
            return text.strip()
    if hasattr(container, "text"):
        text = getattr(container, "text")
        if isinstance(text, str) and text.strip():
            return text.strip()
    return ""


def extract_first_image_url(payload: Any) -> str:
    container = _extract_output_container(payload)
    for choice in _extract_choices(container):
        message = _extract_message(choice)
        content = _extract_content(message)
        if isinstance(content, Sequence) and not isinstance(content, (str, bytes, bytearray)):
            for part in content:
                if isinstance(part, Mapping):
                    image_url = part.get("image") or part.get("url")
                    if isinstance(image_url, str) and image_url:
                        return image_url
    if isinstance(container, Mapping):
        for key in ("image_url", "url"):
            image_url = container.get(key)
            if isinstance(image_url, str) and image_url:
                return image_url
    if hasattr(container, "image_url"):
        image_url = getattr(container, "image_url")
        if isinstance(image_url, str) and image_url:
            return image_url
    return ""


@dataclass
class ProviderRegistry:
    vision_providers: dict[str, VisionProvider] = field(default_factory=dict)
    image_generation_providers: dict[str, ImageGenerationProvider] = field(default_factory=dict)
    default_vision_provider: str = DEFAULT_PROVIDER_NAME
    default_image_generation_provider: str = DEFAULT_PROVIDER_NAME

    def register_vision_provider(self, provider: VisionProvider, *, name: str | None = None) -> None:
        self.vision_providers[name or provider.name] = provider

    def register_image_generation_provider(
        self,
        provider: ImageGenerationProvider,
        *,
        name: str | None = None,
    ) -> None:
        self.image_generation_providers[name or provider.name] = provider

    def get_vision_provider(self, name: str | None = None) -> VisionProvider:
        provider_name = name or self.default_vision_provider
        if provider_name not in self.vision_providers:
            raise KeyError(f"Unknown vision provider: {provider_name}")
        return self.vision_providers[provider_name]

    def get_image_generation_provider(self, name: str | None = None) -> ImageGenerationProvider:
        provider_name = name or self.default_image_generation_provider
        if provider_name not in self.image_generation_providers:
            raise KeyError(f"Unknown image generation provider: {provider_name}")
        return self.image_generation_providers[provider_name]
