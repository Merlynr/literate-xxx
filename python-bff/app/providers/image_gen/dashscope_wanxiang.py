from __future__ import annotations

from dataclasses import dataclass
import asyncio
import json
import os
from typing import Any, Mapping, Sequence

import httpx

from app.providers.base import (
    DEFAULT_DASHSCOPE_API_BASE_URL,
    DEFAULT_DASHSCOPE_IMAGE_GENERATION_PATH,
    DEFAULT_PROVIDER_NAME,
    DEFAULT_IMAGE_GEN_MODEL,
    ImageGenerationResult,
    ProviderError,
    extract_first_image_url,
    json_safe,
)


@dataclass
class DashScopeWanxiangImageGenProvider:
    name: str = DEFAULT_PROVIDER_NAME
    model_name: str = DEFAULT_IMAGE_GEN_MODEL
    api_key: str | None = None
    base_url: str = DEFAULT_DASHSCOPE_API_BASE_URL
    timeout: float = 180.0
    poll_interval: float = 3.0
    max_poll_attempts: int = 40

    def _resolve_api_key(self) -> str:
        api_key = self.api_key or os.getenv("DASHSCOPE_API_KEY", "").strip()
        if not api_key:
            raise ProviderError("DASHSCOPE_API_KEY is required for DashScope image generation")
        return api_key

    def _build_payload(
        self,
        *,
        prompt: str,
        image_urls: Sequence[str],
        size: str,
        watermark: bool,
        n: int,
    ) -> dict[str, Any]:
        content = [{"text": prompt}]
        content.extend({"image": image_url} for image_url in image_urls)
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
                "size": size,
                "n": n,
                "watermark": watermark,
            },
        }

    async def _submit_task(
        self,
        client: httpx.AsyncClient,
        *,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self._resolve_api_key()}",
            "Content-Type": "application/json",
            "X-DashScope-Async": "enable",
        }
        response = await client.post(
            f"{self.base_url.rstrip('/')}{DEFAULT_DASHSCOPE_IMAGE_GENERATION_PATH}",
            headers=headers,
            json=payload,
        )
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise ProviderError(f"DashScope image generation request failed: {exc.response.text}") from exc
        try:
            return response.json()
        except Exception as exc:
            raise ProviderError("DashScope image generation returned a non-JSON response") from exc

    async def _poll_task(
        self,
        client: httpx.AsyncClient,
        *,
        task_id: str,
    ) -> dict[str, Any]:
        url = f"{self.base_url.rstrip('/')}/tasks/{task_id}"
        headers = {
            "Authorization": f"Bearer {self._resolve_api_key()}",
        }
        last_body: dict[str, Any] | None = None
        for _attempt in range(self.max_poll_attempts):
            response = await client.get(url, headers=headers)
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise ProviderError(f"DashScope task poll failed: {exc.response.text}") from exc
            try:
                body = response.json()
            except Exception as exc:
                raise ProviderError("DashScope task poll returned a non-JSON response") from exc
            last_body = body
            output = body.get("output", {}) if isinstance(body, dict) else {}
            task_status = str(output.get("task_status") or output.get("status") or "").upper()
            if task_status in {"SUCCEEDED", "SUCCESS", "COMPLETED"}:
                return body
            if task_status in {"FAILED", "ERROR", "CANCELLED"}:
                raise ProviderError(f"DashScope task failed: {json.dumps(body, ensure_ascii=False)}")
            await asyncio.sleep(self.poll_interval)
        raise ProviderError(f"DashScope task did not finish in time: {json.dumps(last_body or {}, ensure_ascii=False)}")

    async def generate(
        self,
        *,
        prompt: str,
        image_urls: Sequence[str] = (),
        source_image_url: str | None = None,
        style_image_url: str | None = None,
        size: str = "2K",
        watermark: bool = False,
        n: int = 1,
    ) -> ImageGenerationResult:
        effective_image_urls = list(image_urls)
        if not effective_image_urls:
            for candidate in (source_image_url, style_image_url):
                if candidate:
                    effective_image_urls.append(candidate)
        if not effective_image_urls:
            raise ProviderError("At least one image URL is required for DashScope image generation")
        payload = self._build_payload(
            prompt=prompt,
            image_urls=effective_image_urls,
            size=size,
            watermark=watermark,
            n=n,
        )
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            submission = await self._submit_task(client, payload=payload)
            task_id = None
            if isinstance(submission, dict):
                task_id = (
                    submission.get("task_id")
                    or submission.get("output", {}).get("task_id")
                    or submission.get("output", {}).get("taskId")
                )
            body = await self._poll_task(client, task_id=str(task_id)) if task_id else submission

        image_url = extract_first_image_url(body)
        if not image_url and isinstance(body, dict):
            output = body.get("output", {})
            if isinstance(output, dict):
                results = output.get("results") or []
                if results and isinstance(results, list):
                    first = results[0]
                    if isinstance(first, dict):
                        image_url = first.get("url", "")
        if not image_url:
            raise ProviderError(f"DashScope image generation did not return an image URL: {json.dumps(body, ensure_ascii=False)}")

        request_id = body.get("request_id") if isinstance(body, dict) else None
        return ImageGenerationResult(
            provider=self.name,
            model_name=self.model_name,
            prompt=prompt,
            image_urls=tuple(effective_image_urls),
            image_url=image_url,
            request_id=request_id,
            task_id=str(task_id) if task_id else None,
            raw_response=json_safe(body),
        )


WanxiangImageGenerationProvider = DashScopeWanxiangImageGenProvider
