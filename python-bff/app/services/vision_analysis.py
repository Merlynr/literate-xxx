from __future__ import annotations

from typing import Sequence

from app.providers import get_vision_provider
from app.providers.base import DEFAULT_PROVIDER_NAME, VisionAnalysisResult
from app.services.generation_snapshot import GenerationContext


STYLE_REFERENCE_ANALYSIS_PROMPT = """
你是电商商品海报的视觉分析助手。
请分析给定的「风格参考图」（仅借鉴背景、光影、构图与排版，不要把它当成要生成的商品主体），输出严格 JSON，且必须包含这些键：
- background: 背景风格
- lighting: 光线特征
- composition: 构图特征
- style: 整体视觉风格
- color_palette: 颜色关键词数组
- props: 可借鉴的装饰元素数组
- mood: 画面情绪
- typography: 如果画面包含文字，描述文字排版特征
只输出 JSON，不要输出解释文字。
""".strip()

PRODUCT_SUBJECT_ANALYSIS_PROMPT = """
你是电商商品海报的视觉分析助手。
请分析给定的「用户上传实物照片」，这是生成海报时必须保留的唯一商品主体，输出严格 JSON，且必须包含这些键：
- product_type: 商品类型简述
- must_preserve: 数组，必须原样保留的外观特征（瓶身形状、包装、标签文字、主色、材质等）
- dominant_colors: 主色数组
- label_text: 包装上可见的关键文字
- shape_and_material: 外形与材质
- defects_to_fix: 实拍图中需要弱化或去除的瑕疵（杂乱背景、反光等）
只输出 JSON，不要输出解释文字。
""".strip()

# 兼容旧引用
VISION_ANALYSIS_SYSTEM_PROMPT = STYLE_REFERENCE_ANALYSIS_PROMPT


async def analyze_reference_image(
    *,
    image_urls: Sequence[str],
    prompt_hint: str = "",
    provider_name: str | None = None,
    model_name: str | None = None,
    system_prompt: str | None = None,
) -> VisionAnalysisResult:
    provider = get_vision_provider(provider_name or DEFAULT_PROVIDER_NAME)
    prompt = system_prompt or STYLE_REFERENCE_ANALYSIS_PROMPT
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


async def analyze_product_subject(
    *,
    image_url: str,
    prompt_hint: str = "",
    provider_name: str | None = None,
    model_name: str | None = None,
) -> VisionAnalysisResult:
    return await analyze_reference_image(
        image_urls=[image_url],
        prompt_hint=prompt_hint,
        provider_name=provider_name,
        model_name=model_name,
        system_prompt=PRODUCT_SUBJECT_ANALYSIS_PROMPT,
    )


async def analyze_style_reference(
    *,
    image_url: str,
    prompt_hint: str = "",
    provider_name: str | None = None,
    model_name: str | None = None,
) -> VisionAnalysisResult:
    return await analyze_reference_image(
        image_urls=[image_url],
        prompt_hint=prompt_hint,
        provider_name=provider_name,
        model_name=model_name,
        system_prompt=STYLE_REFERENCE_ANALYSIS_PROMPT,
    )


async def analyze_generation_vision(
    *,
    source_image_url: str,
    style_image_url: str | None = None,
    prompt_hint: str = "",
    provider_name: str | None = None,
    model_name: str | None = None,
) -> dict:
    """Analyze uploaded product first; optionally analyze style cover for layout only."""
    product = await analyze_product_subject(
        image_url=source_image_url,
        prompt_hint=prompt_hint,
        provider_name=provider_name,
        model_name=model_name,
    )
    style = None
    if style_image_url:
        style = await analyze_style_reference(
            image_url=style_image_url,
            prompt_hint=prompt_hint,
            provider_name=provider_name,
            model_name=model_name,
        )
    return {
        "product_subject": product.analysis,
        "style_reference": style.analysis if style else {},
    }


async def analyze_generation_source(
    context: GenerationContext,
    provider_name: str | None = None,
    model_name: str | None = None,
) -> dict:
    prompt_hint = str(context.prompt_snapshot.get("prompt_hint") or "").strip()
    return await analyze_generation_vision(
        source_image_url=context.source_image_url,
        style_image_url=context.style_image_url,
        prompt_hint=prompt_hint,
        provider_name=provider_name,
        model_name=model_name,
    )
