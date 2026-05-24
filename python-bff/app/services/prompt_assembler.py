from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Any, Mapping, Sequence

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


DEFAULT_GENERATION_TERMS: tuple[str, ...] = (
    "画面主题须综合参考风格模板版式与用户补充描述，不得偏离运营配置的视觉意图。",
    "商品主体的摆放角度、朝向、透视与在画面中的位置，须优先遵循风格模板构图；若用户描述中有明确角度或姿态要求，以描述为准。",
    "背景主色与渐变须以商品主体主色为基准协调适配：可借鉴模板色系，但需保证主体清晰突出、色彩和谐，避免与包装主色冲突或抢戏。",
    "保留商品包装识别信息与真实质感，画面干净、高质感、适合电商详情页或推广页投放。",
)

_SLOT_TEMPLATE_LABELS: dict[str, str] = {
    "title": "模板标题",
    "layout": "版式布局",
    "tone": "画面气质",
    "headline_limit": "主标题字数上限",
    "subheadline_limit": "副标题字数上限",
    "bullet_count": "卖点条数",
}


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


def build_image_role_preamble(*, source_count: int = 1, has_style_template: bool = False) -> str:
    source_count = max(1, source_count)
    if source_count == 1 and not has_style_template:
        return "【输入图片】仅一张用户上传的商品实拍，必须作为画面唯一主体并保留包装细节。"
    if source_count == 1 and has_style_template:
        return (
            "【输入图片说明】\n"
            "第1张：用户上传的商品实拍——画面唯一商品主体，必须保留其包装外形、标签文字、主色与材质。\n"
            "第2张：运营配置的风格模板（Demo）——学习背景色、主体摆放角度、光影、构图、装饰元素与排版气质，禁止复制模板中的商品外观。"
        )
    lines = ["【输入图片说明】"]
    if source_count == 1:
        lines.append("第1张：用户上传的商品实拍——画面唯一商品主体，必须保留其包装外形、标签文字、主色与材质。")
    else:
        lines.append(
            f"第1-{source_count}张：用户上传的商品实拍（同一商品的不同角度/细节），必须综合参考并保留包装外形、标签文字、主色与材质。"
        )
    if has_style_template:
        style_index = source_count + 1
        lines.append(
            f"第{style_index}张：运营配置的风格模板（Demo）——学习背景色、主体摆放角度、光影、构图、装饰元素与排版气质，禁止复制模板中的商品外观。"
        )
    return "\n".join(lines)


def _source_assets_from_snapshot(prompt_snapshot: Mapping[str, Any]) -> list[dict[str, Any]]:
    source_assets = prompt_snapshot.get("source_assets")
    if isinstance(source_assets, list) and source_assets:
        return [snapshot_mapping(item) or {} for item in source_assets if isinstance(item, Mapping)]
    source_asset = snapshot_mapping(prompt_snapshot.get("source_asset")) or {}
    return [source_asset] if source_asset else []


def _format_slot_template(slot_template: Mapping[str, Any] | None) -> str:
    if not slot_template:
        return "（未配置 slot 模板，按风格名称与封面图生成）"
    parts: list[str] = []
    for key, label in _SLOT_TEMPLATE_LABELS.items():
        value = slot_template.get(key)
        if value not in (None, ""):
            parts.append(f"{label}：{value}")
    extra = slot_template.get("extra")
    if isinstance(extra, list):
        parts.extend(str(item) for item in extra if item)
    elif isinstance(extra, str) and extra.strip():
        parts.append(extra.strip())
    if not parts:
        return str(freeze_json(slot_template))
    return "；".join(parts)


def _vision_field(analysis: Mapping[str, Any] | None, key: str) -> str:
    if not analysis:
        return ""
    value = analysis.get(key)
    if isinstance(value, list):
        return "、".join(str(item) for item in value if item)
    if isinstance(value, str):
        return value.strip()
    return ""


def _format_resolved_terms(resolved_terms: Sequence[Mapping[str, Any]] | None) -> str:
    if not resolved_terms:
        return ""
    grouped: dict[str, list[str]] = {
        "prefix": [],
        "positive": [],
        "negative": [],
        "brand": [],
    }
    for term in resolved_terms:
        term_type = str(term.get("type") or "")
        content = str(term.get("content") or "").strip()
        if term_type in grouped and content:
            grouped[term_type].append(content)
    parts: list[str] = []
    if grouped["prefix"]:
        parts.append("前缀约束：" + "；".join(grouped["prefix"]))
    if grouped["positive"]:
        parts.append("正向强调：" + "、".join(grouped["positive"]))
    if grouped["brand"]:
        parts.append("品牌露出：" + "、".join(grouped["brand"]))
    if grouped["negative"]:
        parts.append("避免出现：" + "、".join(grouped["negative"]))
    return "\n".join(parts)


def _build_from_snapshot(
    *,
    prompt_snapshot: Mapping[str, Any],
    rule_snapshot: Mapping[str, Any],
    vision_analysis: Mapping[str, Any] | VisionAnalysisResult | Any,
) -> PromptBundle:
    source_assets = _source_assets_from_snapshot(prompt_snapshot)
    source_asset = source_assets[0] if source_assets else {}
    category = snapshot_mapping(prompt_snapshot.get("category"))
    style = snapshot_mapping(prompt_snapshot.get("style"))
    prompt_hint = str(prompt_snapshot.get("prompt_hint") or "").strip()
    resolved_terms = prompt_snapshot.get("resolved_terms") or []
    operational_terms = _format_resolved_terms(resolved_terms if isinstance(resolved_terms, list) else [])
    analysis_summary = _analysis_summary(vision_analysis)
    category_name = (category or {}).get("name") or "商品"
    category_code = (category or {}).get("category_code") or ""
    style_name = (style or {}).get("name") or "默认风格"
    style_cover = (style or {}).get("cover_image_url") or ""
    rule_text = str(freeze_json(rule_snapshot))
    slot_template = snapshot_mapping(rule_snapshot.get("slot_template")) or {}
    template_requirements = _format_slot_template(slot_template)
    style_ref: Mapping[str, Any] = {}
    product_ref: Mapping[str, Any] = {}
    if isinstance(vision_analysis, Mapping):
        style_ref = snapshot_mapping(vision_analysis.get("style_reference")) or {}
        product_ref = snapshot_mapping(vision_analysis.get("product_subject")) or {}
    style_ref_analysis = _format_mapping(style_ref)
    product_analysis = _format_mapping(product_ref)
    template_subject_placement = _vision_field(style_ref, "subject_placement")
    template_background_color = _vision_field(style_ref, "background_color") or _vision_field(style_ref, "background")
    product_subject_placement = _vision_field(product_ref, "subject_placement")
    recommended_background = _vision_field(product_ref, "recommended_background")
    product_dominant_colors = _vision_field(product_ref, "dominant_colors")
    default_terms = "\n".join(f"- {term}" for term in DEFAULT_GENERATION_TERMS)
    source_count = len(source_assets)
    source_requirement = (
        "【硬性要求】以用户上传的全部实物照片为同一商品主体的参考：必须保留实拍图中的包装外形、标签文字、主色与材质，不得替换成模板图中的其他商品。"
        if source_count > 1
        else "【硬性要求】以用户上传的实物照片为唯一商品主体：必须保留实拍图中的包装外形、标签文字、主色与材质，不得替换成模板图中的其他商品。"
    )
    style_learning = (
        f"【风格学习】若有第{source_count + 1}张风格模板图，只借鉴其背景/光影/构图/装饰与排版，不要把模板里的商品抄进成图。"
        if source_count > 1
        else "【风格学习】若有第二张风格模板图，只借鉴其背景/光影/构图/装饰与排版，不要把模板里的商品抄进成图。"
    )

    system_prompt = (
        "你是电商商品海报生成助手。"
        "需要保留主体真实结构、标签和配色，同时产出适合投放的商业海报。"
        "生成时须参照风格模板与用户描述，协调主体摆放角度与背景配色。"
    )
    user_prompt = "\n".join(
        [
            f"类别：{category_name}",
            f"风格：{style_name}",
            f"主体快照：{freeze_json(source_assets if source_count > 1 else source_asset)}",
            f"视觉分析：{analysis_summary}",
            f"模板要求：{template_requirements}",
            f"运营词条：{operational_terms or '无'}",
            f"规则快照：{rule_text}",
            f"补充要求：{prompt_hint or '无'}",
        ]
    )
    generation_prompt = "\n".join(
        [
            f"请生成一张「{category_name}」类目的商品宣传海报（类目编码：{category_code or '未指定'}）。",
            f"运营配置的风格为「{style_name}」，需学习该风格模板的背景色、主体角度、光影、构图与版式气质。",
            f"模板版式要求：{template_requirements}",
            source_requirement,
            style_learning,
            "【主体角度】商品主体的摆放角度、朝向与透视须参照风格模板构图"
            + (f"（模板：{template_subject_placement}）" if template_subject_placement else "")
            + "；若用户描述中有明确角度或姿态要求，以描述为准"
            + (f"（实拍现状：{product_subject_placement}）" if product_subject_placement else "")
            + "。",
            "【背景配色】背景主色须与商品主体主色协调适配，以主体视觉为中心调整，保证主体清晰突出"
            + (f"（主体主色：{product_dominant_colors}）" if product_dominant_colors else "")
            + (f"（建议背景：{recommended_background}）" if recommended_background else "")
            + (f"（模板背景参考：{template_background_color}）" if template_background_color else "")
            + "。",
            f"商品主体分析：{product_analysis or analysis_summary}",
            f"风格模板分析：{style_ref_analysis or '（无风格封面，仅按类目与风格名称生成）'}",
            f"规则冻结：{rule_text}",
            f"【默认词条】\n{default_terms}",
            f"【运营词条】\n{operational_terms or '（无匹配的运营词条）'}",
            f"用户补充描述：{prompt_hint or '无额外描述，按模板与默认词条执行'}",
        ]
    )
    reference_urls = tuple(
        url
        for url in (
            *(
                prompt_snapshot.get("source_image_urls")
                if isinstance(prompt_snapshot.get("source_image_urls"), list)
                else [item.get("download_url") for item in source_assets]
            ),
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
        "resolved_terms": freeze_json(resolved_terms) if resolved_terms else [],
        "source_assets": freeze_json(source_assets),
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
