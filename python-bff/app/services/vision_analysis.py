from __future__ import annotations

from typing import Sequence

from app.providers import get_vision_provider
from app.providers.base import DEFAULT_PROVIDER_NAME, VisionAnalysisResult
from app.services.generation_snapshot import GenerationContext


STYLE_REFERENCE_ANALYSIS_PROMPT = """
你是电商商品海报的视觉分析助手。
请分析给定的「风格参考图」（仅借鉴背景、光影、构图与排版，不要把它当成要生成的商品主体），输出严格 JSON，且必须包含这些键：
- background: 背景风格
- background_color: 背景主色与辅助色描述（如暖 beige 渐变、浅灰纯色等）
- lighting: 光线特征
- composition: 构图特征
- subject_placement: 模板中商品主体的摆放角度、朝向、透视、位置与画面占比
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
- subject_placement: 实拍图中商品当前的摆放角度、朝向与透视
- recommended_background: 与主体主色协调的背景色/渐变建议（需突出主体、避免撞色）
- label_text: 包装上可见的关键文字
- shape_and_material: 外形与材质
- defects_to_fix: 实拍图中需要弱化或去除的瑕疵（杂乱背景、反光等）
只输出 JSON，不要输出解释文字。
""".strip()

PRODUCT_SUBJECTS_ANALYSIS_PROMPT = """
你是电商商品海报的视觉分析助手。
用户上传了多张同一商品的实物照片（不同角度或细节），这些图片是生成海报时必须保留的商品主体参考。请综合分析并输出严格 JSON，且必须包含这些键：
- product_type: 商品类型简述
- must_preserve: 数组，综合所有角度后必须原样保留的外观特征（包装、标签文字、主色、材质等）
- dominant_colors: 主色数组
- subject_placement: 建议用于成图的主体摆放角度与朝向（可综合多张实拍与常用电商构图）
- recommended_background: 与主体主色协调的背景色/渐变建议（需突出主体、避免撞色）
- label_text: 包装上可见的关键文字
- shape_and_material: 外形与材质
- defects_to_fix: 实拍图中需要弱化或去除的瑕疵（杂乱背景、反光等）
- source_images: 数组，每项含 index（从1开始）、angle（该张图的角度描述）、notes（该张图补充信息）
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


async def analyze_product_subjects(
    *,
    image_urls: Sequence[str],
    prompt_hint: str = "",
    provider_name: str | None = None,
    model_name: str | None = None,
) -> VisionAnalysisResult:
    if len(image_urls) == 1:
        return await analyze_product_subject(
            image_url=image_urls[0],
            prompt_hint=prompt_hint,
            provider_name=provider_name,
            model_name=model_name,
        )
    return await analyze_reference_image(
        image_urls=image_urls,
        prompt_hint=prompt_hint,
        provider_name=provider_name,
        model_name=model_name,
        system_prompt=PRODUCT_SUBJECTS_ANALYSIS_PROMPT,
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
    source_image_urls: Sequence[str] | None = None,
    source_image_url: str | None = None,
    style_image_url: str | None = None,
    prompt_hint: str = "",
    provider_name: str | None = None,
    model_name: str | None = None,
) -> dict:
    """Analyze uploaded product photos first; optionally analyze style cover for layout only."""
    resolved_source_urls = list(source_image_urls or [])
    if not resolved_source_urls and source_image_url:
        resolved_source_urls = [source_image_url]
    if not resolved_source_urls:
        raise ValueError("At least one source image URL is required")

    product = await analyze_product_subjects(
        image_urls=resolved_source_urls,
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
