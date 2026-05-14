from __future__ import annotations

from dataclasses import dataclass
import json
import os
from typing import Any, Mapping, Sequence

import httpx

from app.providers.base import (
    DEFAULT_DASHSCOPE_API_BASE_URL,
    DEFAULT_DASHSCOPE_VISION_PATH,
    DEFAULT_PROVIDER_NAME,
    DEFAULT_VISION_MODEL,
    ProviderError,
    VisionAnalysisResult,
    extract_first_text,
    json_safe,
    parse_json_maybe,
)
from app.core.config import settings


@dataclass
class DashScopeVisionProvider:
    name: str = DEFAULT_PROVIDER_NAME
    model_name: str = DEFAULT_VISION_MODEL
    api_key: str | None = None
    base_url: str = DEFAULT_DASHSCOPE_API_BASE_URL
    timeout: float = 120.0

    def _resolve_api_key(self) -> str:
        api_key = (self.api_key or settings.DASHSCOPE_API_KEY or os.getenv("DASHSCOPE_API_KEY", "")).strip()
        if not api_key:
            raise ProviderError("DASHSCOPE_API_KEY is required for DashScope vision analysis")
        return api_key

    def _build_payload(
        self,
        *,
        image_urls: Sequence[str],
        prompt: str,
        response_format: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        content: list[dict[str, Any]] = [{"image": image_url} for image_url in image_urls]
        content.append({"text": prompt})
        return {
            "model": self.model_name,
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": content,
                    }
                ]
            },
            "parameters": {
                "response_format": dict(response_format or {"type": "json_object"}),
                "enable_thinking": False,
            },
        }

    async def analyze(
        self,
        *,
        image_urls: Sequence[str],
        prompt: str,
        response_format: Mapping[str, Any] | None = None,
    ) -> VisionAnalysisResult:
        if not image_urls:
            raise ProviderError("At least one image URL is required for vision analysis")

        payload = self._build_payload(
            image_urls=image_urls,
            prompt=prompt,
            response_format=response_format,
        )
        headers = {
            "Authorization": f"Bearer {self._resolve_api_key()}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True, trust_env=False) as client:
            response = await client.post(
                f"{self.base_url.rstrip('/')}{DEFAULT_DASHSCOPE_VISION_PATH}",
                headers=headers,
                json=payload,
            )
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise ProviderError(f"DashScope vision request failed: {exc.response.text}") from exc

        body: dict[str, Any]
        try:
            body = response.json()
        except Exception:
            text = response.text.strip()
            body = {"text": text} if text else {}

        analysis: dict[str, Any] = {}
        if isinstance(body, dict):
            output = body.get("output", {})
            if isinstance(output, dict):
                maybe_text = extract_first_text(output)
                if maybe_text:
                    try:
                        analysis = parse_json_maybe(maybe_text)
                    except Exception:
                        analysis = {"raw_text": maybe_text}
                else:
                    maybe_output_text = output.get("text")
                    if maybe_output_text:
                        try:
                            analysis = parse_json_maybe(maybe_output_text)
                        except Exception:
                            analysis = {"raw_text": str(maybe_output_text)}
            if not analysis and body.get("text"):
                try:
                    analysis = parse_json_maybe(body["text"])
                except Exception:
                    analysis = {"raw_text": str(body["text"])}
        if not analysis:
            analysis = {"raw_text": json_safe(body)} if body else {}

        request_id = body.get("request_id") if isinstance(body, dict) else None
        return VisionAnalysisResult(
            provider=self.name,
            model_name=self.model_name,
            image_urls=tuple(image_urls),
            analysis=analysis,
            request_id=request_id,
            raw_response=json_safe(body) if body else None,
        )
