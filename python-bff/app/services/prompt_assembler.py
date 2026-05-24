from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Any, Mapping

from app.providers.base import VisionAnalysisResult
from app.services.generation_snapshot import GenerationContext, freeze_json, snapshot_mapping


@dataclass(frozen=True)
class PromptBundle:
    system_prompt: str
    user_prompt: str
    generation_prompt: str
    reference_urls: tuple[str, ...]
    prompt_snapshot: dict[str, Any]
    prompt_hash: str


def _format_mapping(value: Any) -> str:
    return freeze_json(value).__repr__() if not isinstance(value, Mapping) else str(freeze_json(value))


def _analysis_summary(analysis: Any) -> str:
    if isinstance(analysis, Mapping) and ("product_subject" in analysis or "style_reference" in analysis):
        product = snapshot_mapping(analysis.get("product_subject")) or {}
        style = snapshot_mapping(analysis.get("style_reference")) or {}
        parts = [f"商品主体（必须保留）：{_format_mapping(product)}"]
        if style:
            parts.append(f"风格参考（仅背景/光影/构图）：{_format_mapping(style)}")
        return "\n".join(parts)
    if isinstance(analysis, VisionAnalysisResult):
        summary = analysis.analysis.get("summary") or analysis.analysis.get("analysis") or analysis.analysis.get("text")
        if isinstance(summary, str) and summary.strip():
            return summary.strip()
        return _format_mapping(analysis.analysis)
    if isinstance(analysis, Mapping):
        summary = analysis.get("summary") or analysis.get("analysis") or analysis.get("text")
        if isinstance(summary, str) and summary.strip():
            return summary.strip()
        return _format_mapping(analysis)
    if hasattr(analysis, "analysis"):
        return _analysis_summary(getattr(analysis, "analysis"))
    return str(analysis)


def build_image_role_preamble(*, has_style_template: bool) -> str:
    if not has_style_template:
        return "【输入图片】仅一张用户上传的商品实拍，必须作为画面唯一主体并保留包装细节。"
    return (
        "【输入图片说明】\n"
        "第1张：用户上传的商品实拍——画面唯一商品主体，必须保留其包装外形、标签文字、主色与材质。\n"
        "第2张：运营配置的风格模板（Demo）——学习背景、光影、构图、装饰元素与排版气质，禁止复制模板中的商品外观。"
    )


def _build_from_snapshot(
    *,
    prompt_snapshot: Mapping[str, Any],
    rule_snapshot: Mapping[str, Any],
    vision_analysis: Mapping[str, Any] | VisionAnalysisResult | Any,
) -> PromptBundle:
    source_asset = snapshot_mapping(prompt_snapshot.get("source_asset")) or {}
    category = snapshot_mapping(prompt_snapshot.get("category"))
    style = snapshot_mapping(prompt_snapshot.get("style"))
    prompt_hint = str(prompt_snapshot.get("prompt_hint") or "").strip()
    analysis_summary = _analysis_summary(vision_analysis)
    category_name = (category or {}).get("name") or "商品"
    category_code = (category or {}).get("category_code") or ""
    style_name = (style or {}).get("name") or "默认风格"
    style_cover = (style or {}).get("cover_image_url") or ""
    rule_text = str(freeze_json(rule_snapshot))
    style_ref_analysis = ""
    product_analysis = ""
    if isinstance(vision_analysis, Mapping):
        style_ref_analysis = _format_mapping(vision_analysis.get("style_reference") or {})
        product_analysis = _format_mapping(vision_analysis.get("product_subject") or {})

    system_prompt = (
        "你是电商商品海报生成助手。"
        "需要保留主体真实结构、标签和配色，同时产出适合投放的商业海报。"
    )
    user_prompt = "\n".join(
        [
            f"类别：{category_name}",
            f"风格：{style_name}",
            f"主体快照：{freeze_json(source_asset)}",
            f"视觉分析：{analysis_summary}",
            f"规则快照：{rule_text}",
            f"补充要求：{prompt_hint or '无'}",
        ]
    )
    generation_prompt = "\n".join(
        [
            f"请生成一张「{category_name}」类目的商品宣传海报（类目编码：{category_code or '未指定'}）。",
            f"运营配置的风格为「{style_name}」，需学习该风格模板的背景、光影、构图与版式气质。",
            "【硬性要求】以用户上传的实物照片为唯一商品主体：必须保留实拍图中的包装外形、标签文字、主色与材质，不得替换成模板图中的其他商品。",
            "【风格学习】若有第二张风格模板图，只借鉴其背景/光影/构图/装饰与排版，不要把模板里的商品抄进成图。",
            f"商品主体分析：{product_analysis or analysis_summary}",
            f"风格模板分析：{style_ref_analysis or '（无风格封面，仅按类目与风格名称生成）'}",
            f"规则冻结：{rule_text}",
            "输出画面应干净、高质感、商业化，适合直接用于详情页或推广页。",
            f"画面要求：{prompt_hint or '无'}",
        ]
    )
    reference_urls = tuple(
        url
        for url in (
            (prompt_snapshot.get("source_image_url") or source_asset.get("download_url")),
            (prompt_snapshot.get("style_image_url") or style_cover),
        )
        if isinstance(url, str) and url
    )
    prompt_snapshot_out = {
        "version": "phase3.prompt.v2",
        "system_prompt": system_prompt,
        "user_prompt": user_prompt,
        "generation_prompt": generation_prompt,
        "prompt_hash": hashlib.sha256(generation_prompt.encode("utf-8")).hexdigest(),
        "prompt_hint": prompt_hint,
        "source_asset": source_asset,
        "category": category,
        "style": style,
        "rule_snapshot": snapshot_mapping(rule_snapshot) or {},
        "vision_analysis": freeze_json(vision_analysis),
    }
    return PromptBundle(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        generation_prompt=generation_prompt,
        reference_urls=reference_urls,
        prompt_snapshot=prompt_snapshot_out,
        prompt_hash=prompt_snapshot_out["prompt_hash"],
    )


def assemble_generation_prompt(
    context: GenerationContext | None = None,
    analysis: VisionAnalysisResult | Mapping[str, Any] | Any | None = None,
    *,
    prompt_snapshot: Mapping[str, Any] | None = None,
    rule_snapshot: Mapping[str, Any] | None = None,
    vision_analysis: Mapping[str, Any] | VisionAnalysisResult | Any | None = None,
) -> PromptBundle:
    if context is not None:
        return _build_from_snapshot(
            prompt_snapshot=context.prompt_snapshot,
            rule_snapshot=context.rule_snapshot,
            vision_analysis=analysis or {},
        )
    if prompt_snapshot is None or rule_snapshot is None or vision_analysis is None:
        raise TypeError("assemble_generation_prompt requires either context+analysis or prompt_snapshot/rule_snapshot/vision_analysis")
    return _build_from_snapshot(
        prompt_snapshot=prompt_snapshot,
        rule_snapshot=rule_snapshot,
        vision_analysis=vision_analysis,
    )
