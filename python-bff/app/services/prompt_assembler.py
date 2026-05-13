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
    style_name = (style or {}).get("name") or "默认风格"
    rule_text = str(freeze_json(rule_snapshot))

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
            f"请生成一张{category_name}商品海报，参考风格为{style_name}。",
            f"保持产品主体真实可识别，保留商品标签和关键卖点。",
            f"视觉分析摘要：{analysis_summary}",
            f"冻结快照：{freeze_json(prompt_snapshot)}",
            f"规则冻结：{rule_text}",
            "输出画面应干净、高质感、商业化，适合直接用于详情页或推广页。",
            f"额外要求：{prompt_hint or '无'}",
        ]
    )
    reference_urls = tuple(
        url for url in (
            (prompt_snapshot.get("source_image_url") or source_asset.get("download_url")),
            (prompt_snapshot.get("style_image_url")),
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
