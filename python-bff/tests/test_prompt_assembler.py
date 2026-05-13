from __future__ import annotations

from copy import deepcopy

from app.services.prompt_assembler import PromptBundle, assemble_generation_prompt


def test_prompt_assembler_uses_frozen_snapshots_and_prompt_hash():
    prompt_snapshot = {
        "source_asset": {
            "id": "asset-1",
            "tenant_id": "tenant-1",
            "asset_role": "source",
            "oss_bucket": "xxzx-assets",
            "oss_key": "uploads/source.jpg",
            "original_filename": "source.jpg",
            "content_type": "image/jpeg",
            "size_bytes": 123,
            "sha256": "sha-source",
            "etag": "",
            "width": 100,
            "height": 200,
            "extra_metadata": {"camera": "phone"},
        },
        "category": {
            "id": "cat-1",
            "tenant_id": "tenant-1",
            "category_code": "potato",
            "name": "Potato",
            "sort_order": 1,
            "is_active": True,
        },
        "style": {
            "id": "style-1",
            "tenant_id": "tenant-1",
            "name": "Warm Poster",
            "cover_image_url": "https://signed.example/style.jpg",
            "rule_version": 2,
            "sort_order": 1,
            "is_active": True,
        },
        "prompt_hint": "keep the product centered",
    }
    rule_snapshot = {
        "slot_template": {
            "title": "Warm farm poster",
            "extra": ["no clutter", "clean lighting"],
        },
        "watermark_config": {"text": "XXZX"},
        "aspect_ratio": "1:1",
    }
    vision_analysis = {
        "background": "studio",
        "lighting": "soft",
        "composition": "centered",
        "style": "premium",
        "must_preserve": ["label"],
        "defects_to_fix": ["noise"],
    }

    bundle = assemble_generation_prompt(
        prompt_snapshot=prompt_snapshot,
        rule_snapshot=rule_snapshot,
        vision_analysis=vision_analysis,
    )

    assert isinstance(bundle, PromptBundle)
    assert bundle.generation_prompt
    assert bundle.prompt_snapshot["generation_prompt"] == bundle.generation_prompt
    assert len(bundle.prompt_snapshot["prompt_hash"]) == 64
    assert bundle.prompt_snapshot["source_asset"]["oss_key"] == "uploads/source.jpg"
    assert bundle.prompt_snapshot["style"]["cover_image_url"] == "https://signed.example/style.jpg"
    assert bundle.prompt_snapshot["vision_analysis"]["background"] == "studio"
    assert "keep the product centered" in bundle.generation_prompt
    assert "Warm farm poster" in bundle.generation_prompt

    original = deepcopy(bundle)
    prompt_snapshot["source_asset"]["oss_key"] = "mutated.jpg"
    prompt_snapshot["style"]["cover_image_url"] = "https://example.invalid/changed.jpg"
    rule_snapshot["slot_template"]["title"] = "changed"
    vision_analysis["background"] = "mutated"

    assert bundle == original
    assert bundle.prompt_snapshot["source_asset"]["oss_key"] == "uploads/source.jpg"
    assert bundle.prompt_snapshot["style"]["cover_image_url"] == "https://signed.example/style.jpg"
    assert bundle.prompt_snapshot["vision_analysis"]["background"] == "studio"
