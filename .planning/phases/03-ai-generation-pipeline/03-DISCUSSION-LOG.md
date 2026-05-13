# Phase 3: AI Generation Pipeline - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-13
**Phase:** 03-ai-generation-pipeline
**Areas discussed:** 生成引擎默认实现, 上传与资产边界, 任务与结果

---

## 生成引擎默认实现

| Option | Description | Selected |
|--------|-------------|----------|
| 阿里云万相 | 默认使用阿里云万相路线，参考成功 demo 落地 | ✓ |
| OpenAI / Gemini | 继续保留可替换 provider，但不是 phase 3 的默认实现 | |
| 你决定 | 让规划阶段自己选默认供应商 | |

**User's choice:** 阿里云万相，参考当前目录 `tywx.py` 的成功 API demo
**Notes:** 你明确要求学习已经成功的 DashScope / Wanxiang 调用方式，作为 phase 3 的默认实现参考。

---

## 上传与资产边界

| Option | Description | Selected |
|--------|-------------|----------|
| presign -> confirm -> job | 先签名上传，确认资产，再创建生成任务 | ✓ |
| job 直接收 key | 创建任务时直接传 OSS key，不单独确认资产 | |
| 你决定 | 让规划阶段自行决定上传资产落库方式 | |

**User's choice:** A，先 `presign` 上传，再 `confirm` 记录资产，最后创建任务
**Notes:** 该方案更贴合现有 `uploads/presign` 路由，也能把任务输入固定为已确认资产。

---

## 任务与结果

| Option | Description | Selected |
|--------|-------------|----------|
| 独立 OSS 对象 | 原图和水印图都单独存储，并分别返回签名 URL | ✓ |
| 单对象按需生成 | 只存一份，另一份在请求时现算或变换 | |
| 你决定 | 由规划阶段决定结果交付细节 | |

**User's choice:** 原图和水印图都作为独立 OSS 对象存储并返回签名 URL
**Notes:** 这会让结果交付和后续下载逻辑更直接，也方便前端同时展示两种版本。

---

## the agent's Discretion

- Prompt 模板格式
- Worker 步骤拆分
- 结果页展示细节

## Deferred Ideas

None — no scope creep during discussion.
