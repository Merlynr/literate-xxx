# Phase 3: AI Generation Pipeline - Context

**Gathered:** 2026-05-13
**Status:** Ready for planning

<domain>
## Phase Boundary

本阶段交付 AI 生成主链路：实物图上传、资产确认、Vision 分析、服务端规则/Prompt 组装、Image Gen 出图、水印处理、结果入 OSS、任务状态轮询与结果交付。

本阶段不做额度计费、不做完整前端向导、不做模型自研，只把已有的业务配置和上传资产串成可追踪、可复现的生成任务。

</domain>

<decisions>
## Implementation Decisions

### 生成引擎默认实现
- **D-24:** Vision 和 Image Gen 的默认实现使用阿里云万相（Wanxiang）路线，优先复用 `tywx.py` 里已经跑通的 DashScope 调用方式作为实现参考。
- **D-25:** 生成服务保持 provider 抽象，但 phase 3 的默认落地方案以阿里万相为主，不优先引入额外模型切换复杂度。

### 上传与资产边界
- **D-26:** 采用 `presign -> 客户端直传 OSS -> confirm -> 资产入库 -> 创建生成任务` 的两段式流程。
- **D-27:** 任务创建阶段只引用已确认的资产记录，不直接依赖未确认的 OSS key。

### 任务与结果
- **D-28:** 任务仍遵循幂等创建与冻结快照原则：`client_request_id` 唯一，创建时固化规则版本、Prompt 快照和相关输入。
- **D-29:** 原图和水印图都作为独立 OSS 对象持久化，接口分别返回签名下载 URL。
- **D-30:** 任务状态沿用 `queued -> running -> succeeded/failed` 的轮询模型，前端只做状态查询，不直接参与 AI 调用。

### the agent's Discretion
- Prompt 组装的具体模板格式和槽位填充细节
- Worker 内部的步骤拆分与重试细节
- 结果页的字段展示顺序与错误文案

</decisions>

<specifics>
## Specific Ideas

- 你明确要求默认走阿里云万相，并参考当前目录的 `tywx.py` 作为已经成功的 API demo。
- 你明确要求原图和水印图都独立存 OSS，并都返回签名 URL。
- 你选择了上传边界方案 A：先签名上传，再确认资产，最后创建任务。

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase scope and product constraints
- `.planning/ROADMAP.md` — Phase 3 scope, goals, success criteria
- `.planning/REQUIREMENTS.md` — PROMO-02, PROMO-03, GEN-01 ~ GEN-09
- `.planning/PROJECT.md` — core value, architecture constraints, AI flow assumptions

### Locked decisions from prior phases
- `.planning/phases/01-foundation-infrastructure/01-CONTEXT.md` — OSS/Celery/Uni-app foundation decisions
- `.planning/phases/02-auth-data-layer-admin-crud/02-CONTEXT.md` — tenant model, promo rule schema, frontend auth/token behavior

### Implementation reference docs
- `.planning/research/ARCHITECTURE.md` — generation pipeline, provider abstraction, task snapshot, polling flow
- `.planning/research/STACK.md` — confirmed libraries and implementation preferences
- `.planning/research/PITFALLS.md` — Celery timeout, OSS presign TTL, watermark handling pitfalls
- `AI_IMAGE_PIPELINE_CLARIFICATION.md` — business understanding of the AI poster workflow
- `tywx.py` — successful DashScope / Wanxiang demo reference for prompt shaping and API usage
- `商品宣传图-产品与技术规格.md` — authoritative spec for job state, API paths, and model assumptions

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `python-bff/app/services/oss.py` — already provides presigned upload/download helpers and server-side OSS upload
- `python-bff/app/workers/celery_app.py` — Celery app and retry/timeout defaults already exist
- `python-bff/app/workers/tasks.py` — baseline worker task pattern exists and can be extended into the generation pipeline
- `python-bff/app/api/v1/uploads.py` — upload presign endpoint already exists and matches the upload-first flow
- `wx-fe/src/api/request.ts` — token-aware request wrapper is already ready for polling APIs
- `wx-fe/src/pages/generate/index.vue` — placeholder generate page already exists and can be replaced with the real wizard

### Established Patterns
- Server-side AI orchestration is already the project norm; the frontend never talks to AI providers directly
- OSS access is already presigned URL based, so generated results should follow the same delivery model
- Tenant-aware models already inherit from `TenantModel`, so generation/job models should follow the same pattern
- Phase 2 already established JWT refresh and silent re-login behavior on the frontend

### Integration Points
- `python-bff/app/api/v1/` will need new job/asset routes and a confirm endpoint
- `python-bff/app/services/` will need prompt assembly, provider wrappers, and job orchestration logic
- `python-bff/app/workers/` will need the actual Vision -> Prompt -> Image Gen -> OSS pipeline task
- `python-bff/app/models/` will need generation job, asset, and job event persistence
- `wx-fe/src/pages/generate/` will eventually consume the upload, create-job, polling, and result APIs

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 03-ai-generation-pipeline*
*Context gathered: 2026-05-13*
