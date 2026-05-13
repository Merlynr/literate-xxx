from __future__ import annotations

from typing import Sequence

from app.providers import get_vision_provider
from app.providers.base import DEFAULT_PROVIDER_NAME, VisionAnalysisResult
from app.services.generation_snapshot import GenerationContext


VISION_ANALYSIS_SYSTEM_PROMPT = """
你是电商商品海报的视觉分析助手。
请分析给定的风格参考图，输出严格 JSON，且必须包含这些键：
- must_preserve: 数组，必须保留的视觉元素
- background: 背景风格
- lighting: 光线特征
- composition: 构图特征
- style: 整体视觉风格
- color_palette: 颜色关键词数组
- props: 可借鉴的装饰元素数组
- defects_to_fix: 需要规避的瑕疵数组
- mood: 画面情绪
- typography: 如果画面包含文字，描述文字排版特征
只输出 JSON，不要输出解释文字。
""".strip()


async def analyze_reference_image(
    *,
    image_urls: Sequence[str],
    prompt_hint: str = "",
    provider_name: str | None = None,
    model_name: str | None = None,
) -> VisionAnalysisResult:
    provider = get_vision_provider(provider_name or DEFAULT_PROVIDER_NAME)
    prompt = VISION_ANALYSIS_SYSTEM_PROMPT
    if prompt_hint.strip():
        prompt = f"{prompt}\n\n额外要求：{prompt_hint.strip()}"
    result = await provider.analyze(
        image_urls=image_urls,
        prompt=prompt,
        response_format={"type": "json_object"},
    )
    analysis = result.analysis if isinstance(result.analysis, dict) else {"raw_analysis": result.analysis}
    if model_name and result.model_name != model_name:
        return VisionAnalysisResult(
            provider=result.provider,
            model_name=model_name,
            image_urls=result.image_urls,
            analysis=analysis,
            request_id=result.request_id,
            raw_response=result.raw_response,
        )
    return VisionAnalysisResult(
        provider=result.provider,
        model_name=result.model_name,
        image_urls=result.image_urls,
        analysis=analysis,
        request_id=result.request_id,
        raw_response=result.raw_response,
    )


async def analyze_generation_source(context) -> VisionAnalysisResult:
    image_url = getattr(context, "style_image_url", "") or getattr(context, "source_image_url", "")
    prompt_hint = getattr(context, "prompt_hint", "")
    provider_name = context.job.get("provider") if hasattr(context, "job") and isinstance(context.job, dict) else None
    model_name = context.job.get("model_name") if hasattr(context, "job") and isinstance(context.job, dict) else None
    return await analyze_reference_image(
        image_urls=[image_url] if image_url else [],
        prompt_hint=str(prompt_hint or ""),
        provider_name=provider_name,
        model_name=model_name,
    )


async def analyze_generation_source(
    context: GenerationContext,
    provider_name: str | None = None,
    model_name: str | None = None,
) -> VisionAnalysisResult:
    image_urls = [context.source_image_url]
    if context.style_image_url:
        image_urls.append(context.style_image_url)
    prompt_hint = str(context.prompt_snapshot.get("prompt_hint") or "").strip()
    result = await analyze_reference_image(
        image_urls=image_urls,
        prompt_hint=prompt_hint,
        provider_name=provider_name,
        model_name=model_name,
    )
    return result
