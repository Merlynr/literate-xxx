# Phase 3: AI Generation Pipeline - Research

**Researched:** 2026-05-13
**Status:** Ready for planning

## Executive Summary

Phase 3 should use the Alibaba DashScope ecosystem for the generation side, with `tywx.py` as the working reference for Wanxiang image generation. The practical implementation pattern is:

1. User uploads product and reference/demo images to OSS via presigned URLs.
2. Backend confirms uploaded assets and stores asset rows.
3. Worker fetches the confirmed assets, analyzes the reference/demo image with a vision model, then assembles the final prompt.
4. Worker calls Wanxiang image generation, downloads the returned image URL immediately, and stores the canonical outputs back in OSS.
5. Backend returns OSS presigned URLs for both the raw and watermarked variants.

This phase is not a model-research phase. It is an integration phase. The main research result is the shape of the official APIs and the implication that the provider result URL is transient, so the worker must persist outputs to OSS right away.

## Official API Findings

### Wanxiang image generation

- Alibaba's official Wanxiang image generation/editing API exposes `wan2.7-image` and `wan2.7-image-pro`.
- The documented HTTP endpoint is `POST https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation`.
- The docs show `ImageGeneration.call(...)` and `ImageGeneration.async_call(...)` styles in the Python SDK.
- The response contains an image URL in `output.choices[0].message.content[*].image`.
- The docs state the returned image URL is temporary and should be downloaded promptly.
- `wan2.7-image-pro` supports text-to-image at 4K, while image editing and grouped generation are capped at 2K.

Source:
- [万相-图像生成与编辑2.7 API参考](https://help.aliyun.com/zh/model-studio/wan-image-generation-and-editing-api-reference)
- [如何调用万相图像编辑模型？](https://help.aliyun.com/zh/model-studio/wan-image-edit)

### Vision / image understanding

- Alibaba's DashScope vision docs support image input through multimodal conversation APIs.
- Official examples use `dashscope.MultiModalConversation.call(...)` with image URLs or local file URLs.
- The docs also show that image understanding can use URL-based inputs, which aligns with OSS signed download URLs after asset confirmation.

Source:
- [通义千问API参考](https://help.aliyun.com/zh/model-studio/use-qwen-by-calling-api)
- [视觉理解](https://help.aliyun.com/zh/model-studio/vision)

### Practical implication for this phase

- Use the confirmed asset's OSS signed URL for the worker's vision step.
- Treat the provider result URL as an ephemeral transfer URL, not a persistent asset URL.
- Persist both the provider raw image output and the server-generated watermarked variant as independent OSS objects.

## Planning Implications

### What to build

- A generation job model with idempotent creation and frozen snapshots.
- A confirm-upload endpoint to bridge `presign` and job creation.
- A worker pipeline that does vision analysis, prompt assembly, Wanxiang image generation, download, OSS re-upload, and job state updates.
- A polling API that exposes job state and result URLs.
- A frontend generate page that can upload assets, start jobs, and poll until completion.

### What not to overbuild

- No separate model-routing UI for phase 3.
- No new image preprocessing stage.
- No attempt to keep provider result URLs as durable references.
- No direct frontend calls to AI APIs.

### Open technical choices for planning

- Exact prompt assembly slot format.
- Whether the worker is one task or a small chained task graph.
- Exact job/event persistence schema beyond the already-locked fields.

## Sources

- `tywx.py`
- [万相-图像生成与编辑2.7 API参考](https://help.aliyun.com/zh/model-studio/wan-image-generation-and-editing-api-reference)
- [通义千问API参考](https://help.aliyun.com/zh/model-studio/use-qwen-by-calling-api)
- [视觉理解](https://help.aliyun.com/zh/model-studio/vision)
- `.planning/phases/03-ai-generation-pipeline/03-CONTEXT.md`
- `.planning/PROJECT.md`
- `.planning/REQUIREMENTS.md`
