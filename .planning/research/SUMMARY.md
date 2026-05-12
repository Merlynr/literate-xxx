# Project Research Summary

**Project:** XX甄选 — AIGC Product Image Generation WeChat Mini Program
**Domain:** AIGC E-commerce / WeChat Mini Program
**Researched:** 2026-05-12
**Confidence:** MEDIUM-HIGH

## Executive Summary

XX甄选 is an AI-powered product promotional image generation platform delivered as a WeChat Mini Program, currently focused on agricultural products grown under solar panels. Users upload a real product photo and a demo/reference poster, the system uses Vision API (GPT-4o-mini) to auto-extract descriptive style tags from the demo, then calls Image Gen API to produce publication-ready promotional images. The architecture follows a classic async pipeline: WeChat Mini Program frontend (Uni-app Vue3) → FastAPI BFF → Celery task queue → AI provider calls → OSS storage → polling result delivery.

The recommended approach is a **fully API-driven architecture** — no self-hosted ML inference, no model weights. The BFF handles auth, business logic, and orchestration; Celery workers execute the AI pipeline (vision analysis → prompt assembly → image generation → upload). This keeps operational complexity low while enabling multi-provider switching. The three highest-risk areas are: (1) AI output non-determinism and quality variance, (2) Celery worker reliability under AI API timeout/flakiness, and (3) WeChat Mini Program platform constraints (domain whitelist, permission flows, package size limits).

Key mitigation strategies: task snapshot immutability (freeze rules at creation time), provider abstraction layer for multi-engine support, aggressive client-side image compression before upload, and a hard requirement to validate WeChat MP behavior on real devices from day one — not deferred to integration testing. The project has solid spec documentation (v2.0) and clear feature boundaries, which gives HIGH confidence on feature scope and MEDIUM confidence on specific library versions and AI API behaviors.

## Key Findings

### Recommended Stack

Uni-app Vue3 frontend targeting WeChat Mini Program, with FastAPI async BFF backend, Celery + Redis for async task execution, PostgreSQL for persistence, and Aliyun OSS for image storage. AI integration via official `openai` Python SDK (Vision: GPT-4o-mini, Image Gen: DALL-E 3 / GPT-image-1) with `httpx` for non-OpenAI providers (Gemini/Imagen).

**Core technologies:**
- **Uni-app (Vue3 + Composition API)**: Cross-compile to WeChat MP; mature ecosystem with uv-ui component library, Pinia state management, z-paging for lists
- **FastAPI**: Async-native BFF framework with automatic OpenAPI docs; ideal for concurrent external API orchestration
- **Celery + Redis**: Distributed task queue for AI pipeline (10s-120s+ jobs); Redis triple-roles as broker + result backend + cache
- **PostgreSQL 16+**: JSONB for semi-structured data (rule snapshots, prompt templates, tag collections); async via asyncpg + SQLAlchemy 2.0
- **Aliyun OSS**: Image storage with presigned URL direct upload (frontend → OSS, bypassing BFF bandwidth bottleneck)
- **openai SDK**: Vision + Image Gen unified call; provider abstraction enables Gemini/Codex switching

**Critical versions:** Vue 3.4+, FastAPI 0.115+, Celery 5.4+, PostgreSQL 16+, Redis 7.x, Pydantic v2

### Expected Features

**Must have (table stakes — 12 user features + 6 admin features):**
- WeChat login & tenant binding — entry gate
- Category + style selection with grid card UI — user guidance
- Photo upload (album/camera) + demo/reference image upload — core input
- AI generation pipeline (Vision → prompt assembly → Image Gen) — core value proposition
- Task status with polling & progress display — async UX bridge
- Result preview + download (watermarked + raw) — deliverable
- Task history (my works) with pull-to-refresh — reuse
- Quota/balance display on home + profile pages — usage visibility
- Privacy agreement & terms (legal compliance) — mandatory before first generation
- Task idempotency via client_request_id — prevent double-charging
- Admin CRUD: categories, styles, terms, promo rules, pricing plans
- Admin task monitoring & generation query

**Should have (differentiators):**
- Vision API auto-labeling of demo images (unique innovation)
- Configurable term library with priority/scope (operations-controlled prompt tuning)
- Rule engine + versioned prompt slot assembly (quality control)
- Pre-generation cost estimation ("trial calculation")
- Automatic watermark overlay (brand consistency)
- Multi-AI engine support (provider abstraction)
- Multi-tenant data isolation (B2B extensibility)

**Defer to v2+:**
- WeChat Payment (heavy review process; v1 is quota UI shell only)
- Image preprocessing / background removal (rembg) — adds ML dependency
- E-commerce platform API integration (Taobao/JD/Pinduoduo)
- Human review queue, RBAC, rate limiting, batch generation
- Image editing / post-processing, A/B testing, multi-language

### Architecture Approach

Layered architecture: **Client layer** (Uni-app WX MP + Admin UI) → **BFF layer** (FastAPI with auth, API routes, service layer containing Rule Engine / Prompt Assembler / Quota Manager) → **Infrastructure** (PostgreSQL, Redis, Celery, OSS) → **Worker layer** (Celery tasks executing AI pipeline with Provider Abstraction). Frontend never touches AI APIs directly; prompt assembly is strictly server-side; task snapshots freeze all rule/version data at creation time.

**Major components:**
1. **FastAPI BFF** — API gateway, auth (WeChat login → JWT), presigned upload orchestration, business logic
2. **Rule Engine + Prompt Assembler** — deterministic, rule-based prompt construction from frozen snapshots + vision tags; pure function, no external calls
3. **Celery Workers** — execute 5-step pipeline: Vision API → Prompt Assembly → Image Gen API → OSS Upload → DB update + quota confirmation
4. **Provider Abstraction Layer** — Strategy pattern: IVisionProvider / IImageGenProvider interfaces with registry for GPT-4o-mini, Codex, Gemini implementations
5. **Quota Manager** — freeze/deduct/refund lifecycle with append-only ledger

### Critical Pitfalls

1. **WeChat MP domain whitelist blocks image delivery** — ALL domains (BFF API, OSS, CDN) must be registered in MP console before first deployment; test on real device, not just DevTools
2. **AI output is non-deterministic** — same prompt produces different images; mitigate with seed pinning, quality gates, variance disclosure in UI, and Vision label caching
3. **Celery worker hangs on AI API timeouts** — set hard timeout (180s) + soft timeout (150s), use circuit breaker after N consecutive failures, implement job reconciliation watchdog for stuck `running` jobs
4. **Prompt template drift breaks historical reproducibility** — store FULL assembled prompt text (not just rule reference) in job row; rule versions are append-only; compute prompt hash for debugging
5. **Presigned URL expiry on slow mobile networks** — 300s TTL + mandatory client-side compression (wx.compressImage, target 2048px/80%) + transparent retry with fresh URL on 403

## Implications for Roadmap

Based on combined research, the architecture suggests **5 phases** (consolidated from the 11-step dependency analysis in ARCHITECTURE.md, aligned with FEATURES.md MVP groupings):

### Phase 1: Foundation & Infrastructure
**Rationale:** Everything depends on database schema, BFF skeleton, OSS connectivity, and WeChat MP build pipeline. Must validate WX MP domain whitelist and platform constraints immediately — not at the end.
**Delivers:** Running FastAPI app with PostgreSQL + Alembic migrations; OSS bucket with presigned upload/download; WeChat MP project scaffold with domain whitelist configured; Redis + Celery skeleton with health check.
**Addresses:** Infrastructure for all table stakes features
**Avoids:** Pitfall #1 (domain whitelist), #8 (Uni-app platform differences), #16 (conditional compilation gaps)

### Phase 2: Data Layer & Admin CRUD
**Rationale:** Categories, styles, terms, and rules are the data backbone that drives the AI pipeline. Admin must be able to configure these before the generation flow can be tested end-to-end. Auth (WeChat login) also lands here as it gates all user-facing features.
**Delivers:** WeChat login + JWT auth + tenant binding; Category/Style/Tag CRUD APIs; AI Term CRUD with scoping; Promo Rule CRUD + versioning; Admin UI for all CRUD operations.
**Addresses:** T1 (login), T2 (categories), T3 (styles), A1-A3 (admin CRUD)
**Avoids:** Pitfall #14 (session key expiry), #5 (prompt drift — establish snapshot pattern from start)

### Phase 3: AI Generation Pipeline
**Rationale:** This is the core value proposition and the integration bottleneck. Depends on data layer (rules/terms), task infrastructure (Celery), and AI provider abstraction all being ready. The three highest-complexity features converge here.
**Delivers:** Celery worker with retry/timeout/circuit breaker; Provider abstraction (IVisionProvider, IImageGenProvider); Full pipeline: Vision → Prompt Assembly → Image Gen → OSS upload → DB update; Job creation (idempotent) + polling API; Upload flow (presigned URL + confirm + image compression validation).
**Addresses:** T4-T8 (uploads, AI generation, status, results), D5 (preview calculation — basic), D6 (watermark), D8 (idempotency)
**Avoids:** Pitfall #2 (non-determinism — quality gate), #3 (worker hangs — timeouts), #6 (cost spikes — retry cap), #7 (URL expiry), #9 (Vision inconsistency — caching), #10 (image size — compression), #13 (idempotency race — DB constraint)

### Phase 4: Quota, Billing & Polish
**Rationale:** Quota/billing depends on job lifecycle (freeze/deduct/release requires working generation pipeline). Frontend integration depends on all APIs being ready. This phase closes the commercial loop and delivers the complete user experience.
**Delivers:** Quota account + ledger models; Freeze/deduct/release logic; Pricing plan CRUD; Pre-generation cost estimation; Uni-app frontend: complete wizard flow (login → category → style → upload → confirm → polling → result → save); Task history list with z-paging; Quota display on home + profile pages.
**Addresses:** T9 (task list), T10 (quota display), A5-A6 (pricing/quota admin), D5 (trial calculation), D6 (watermark polish)
**Avoids:** Pitfall #4 (wx.saveImageToPhotosAlbum — pre-flight auth check), #12 (watermark placement — percentage-based)

### Phase 5: Hardening & Launch Prep
**Rationale:** Final quality pass before launch. Addresses operational concerns, compliance, and edge cases discovered during integration testing.
**Delivers:** Privacy agreement & terms UI; Error code standardization; Monitoring + observability (Sentry, Celery Flower); Job reconciliation watchdog; Prompt hash + debug tooling; End-to-end testing on real WX MP devices.
**Addresses:** Compliance requirements, all "minor" pitfalls, operational readiness
**Avoids:** Pitfall #11 (Redis SPOF — separate DB instances), #15 (signed URL expiry — on-demand generation)

### Phase Ordering Rationale

- **Phase 1→2→3 follows the critical path** identified in ARCHITECTURE.md: Foundation → Data Layer → AI Pipeline. Phase 3 is the integration bottleneck where prompt engine, task infrastructure, and AI providers converge.
- **Phase 4 (Quota + Frontend) comes after Pipeline** because the frontend needs working APIs to integrate against, and quota logic requires the job lifecycle to be functional.
- **Phase 5 (Hardening) is deliberately last** because many pitfalls (WX MP behavior, edge cases) only surface during end-to-end testing with real devices.
- **Auth lands in Phase 2, not Phase 1**, because infrastructure can be validated with test endpoints. WeChat login has external dependencies (app registration, OAuth flow) that benefit from a focused phase.
- **Admin CRUD is grouped with Data Layer** because admin operations are prerequisites for testing the AI pipeline (you need categories, styles, and rules configured before generating images).

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 3 (AI Pipeline):** AI API contracts (request/response schemas, error codes, rate limits) need validation against actual vendor docs. LEX-AI specifics are undocumented. Image gen API parameters (seed support, quality settings) affect architecture decisions.
- **Phase 4 (Quota):** Freeze vs. deduct billing model choice needs final decision. WeChat Payment integration research if deferred features are reconsidered.

Phases with standard patterns (skip research-phase):
- **Phase 1 (Foundation):** Standard FastAPI + PostgreSQL + OSS setup. Well-documented patterns.
- **Phase 2 (Data Layer):** Standard CRUD + WeChat login OAuth. Uni-app + uv-ui patterns well-established.
- **Phase 5 (Hardening):** Standard monitoring, error handling, compliance patterns.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | MEDIUM-HIGH | Core stack confirmed in PROJECT.md; specific version numbers from training data (need live verification); library recommendations align with ecosystem consensus |
| Features | HIGH | Derived from detailed spec v2.0 (2026-05-11); feature boundaries clear; anti-features explicitly documented |
| Architecture | HIGH | Grounded in validated tech spec + standard FastAPI/Celery patterns; build order derived from dependency analysis; all patterns have code examples |
| Pitfalls | MEDIUM | WeChat MP restrictions and Celery pitfalls are well-established; AI API specific behaviors (LEX-AI, Codex image gen) need vendor doc validation; copyright landscape is actively evolving |

**Overall confidence:** MEDIUM-HIGH — Strong on product spec and architecture patterns. Gaps are in AI API specifics and WeChat MP edge cases that require real-device validation.

### Gaps to Address

- **AI API vendor specifics:** LEX-AI API contract is undocumented in project files. Codex/Gemini image gen parameters (seed support, quality presets, async modes) need validation before Phase 3 planning.
- **AI-generated image copyright (China):** Beijing Internet Court ruled AI images CAN be copyrighted (2023), but law is unsettled. Platform-specific rules (WeChat, Taobao) on AI product images need research before launch.
- **Celery on Windows:** Development environment is Windows. Celery 5.x+ dropped official Windows support. Must use `--pool=solo`/`--pool=threads` for dev; production MUST be Linux.
- **WeChat MP subpackage strategy:** With 4 SKUs, multiple styles, and admin features, total package may approach 20MB limit. Needs early investigation of subpackage splitting.
- **Freeze vs. deduct billing model:** Features spec presents two options (Plan A: freeze at creation, deduct on success; Plan B: deduct on success directly). Needs final architectural decision before Phase 4.

## Sources

### Primary (HIGH confidence)
- `商品宣传图-产品与技术规格.md` v2.0 (2026-05-11) — authoritative technical spec
- `PROJECT.md` — confirmed architecture and tech stack decisions
- `AI_IMAGE_PIPELINE_CLARIFICATION.md` — AI flow clarification

### Secondary (MEDIUM confidence)
- FastAPI / Celery / SQLAlchemy official documentation — standard patterns
- WeChat Mini Program official docs — domain whitelist, permissions, package limits
- Aliyun OSS documentation — presigned URLs, lifecycle policies
- Uni-app official docs — conditional compilation, platform differences

### Tertiary (LOW confidence)
- Specific library version numbers — from training data, need live verification
- Beijing Internet Court AI copyright ruling (2023) — evolving legal landscape
- LEX-AI API behavior — undocumented, inferred from spec mentions
- Celery Windows workarounds — community solutions, not official support

---
*Research completed: 2026-05-12*
*Ready for roadmap: yes*
