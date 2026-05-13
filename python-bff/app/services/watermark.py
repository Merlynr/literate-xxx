from __future__ import annotations

from dataclasses import dataclass
import io
from typing import Any, Mapping

from PIL import Image, ImageDraw, ImageFont


@dataclass(frozen=True)
class WatermarkedImage:
    content: bytes
    content_type: str
    width: int
    height: int
    image_format: str


def _pick_watermark_text(watermark_config: Mapping[str, Any] | None) -> str:
    if watermark_config:
        text = watermark_config.get("text") or watermark_config.get("label")
        if isinstance(text, str) and text.strip():
            return text.strip()
    return "XXZX"


def _font_size(width: int, height: int, watermark_config: Mapping[str, Any] | None) -> int:
    if watermark_config and isinstance(watermark_config.get("font_size"), int):
        return max(10, int(watermark_config["font_size"]))
    return max(16, int(min(width, height) * 0.045))


def apply_watermark(
    image_bytes: bytes,
    watermark_text: str | None = None,
    *,
    watermark_config: Mapping[str, Any] | None = None,
) -> WatermarkedImage | bytes:
    effective_config = watermark_config
    if effective_config is None and watermark_text is not None:
        effective_config = {"text": watermark_text}
    with Image.open(io.BytesIO(image_bytes)) as source:
        base = source.convert("RGBA")
        width, height = base.size
        overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        text = _pick_watermark_text(effective_config)
        font_size = _font_size(width, height, effective_config)
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except Exception:
            font = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        padding = max(12, int(min(width, height) * 0.03))
        x = max(padding, width - text_width - padding)
        y = max(padding, height - text_height - padding)

        draw.rounded_rectangle(
            (
                x - padding // 2,
                y - padding // 3,
                x + text_width + padding // 2,
                y + text_height + padding // 3,
            ),
            radius=max(8, padding // 2),
            fill=(0, 0, 0, 96),
        )
        draw.text((x, y), text, font=font, fill=(255, 255, 255, 220))

        composited = Image.alpha_composite(base, overlay)
        output = io.BytesIO()
        image_format = source.format or "PNG"
        if image_format.upper() == "JPEG":
            composited = composited.convert("RGB")
            composited.save(output, format="JPEG", quality=92)
            content_type = "image/jpeg"
        else:
            composited.save(output, format="PNG")
            content_type = "image/png"
            image_format = "PNG"

    result = WatermarkedImage(
        content=output.getvalue(),
        content_type=content_type,
        width=width,
        height=height,
        image_format=image_format,
    )
    if watermark_text is not None and watermark_config is None:
        return result.content
    return result
