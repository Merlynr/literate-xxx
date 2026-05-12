# Roadmap: XX甄选 — AIGC Product Image Generation Platform

## Overview

XX甄选 delivers AI-generated product promotional images via a WeChat Mini Program. The journey goes: build the infrastructure foundation (FastAPI + Celery + OSS + WX MP scaffold) → establish the data layer and authentication (categories, styles, terms, rules, WeChat login) → build the core AI generation pipeline (upload → Vision analysis → prompt assembly → image gen → watermark → delivery) → close the commercial and UX loop (quota system + complete frontend wizard) → harden and prepare for launch (monitoring, error standardization, watchdog). Five phases, 35 requirements, one clear critical path: infrastructure → data → pipeline → UX+quota → hardening.

## Phases

- [ ] **Phase 1: Foundation & Infrastructure** - Backend skeleton, Celery/Redis/OSS infra, WeChat MP scaffold with domain whitelist
- [ ] **Phase 2: Auth, Data Layer & Admin CRUD** - WeChat login + tenant isolation, category/style/term/rule CRUD, admin UI
- [ ] **Phase 3: AI Generation Pipeline** - Upload flow, Vision API, Image Gen, Celery worker pipeline, prompt engine, watermark, task lifecycle
- [ ] **Phase 4: Quota, Billing & Frontend UX** - Quota system, complete wizard flow, task history, save to album, privacy compliance
- [ ] **Phase 5: Hardening & Launch Prep** - Task monitoring, error codes, job watchdog, Sentry + Flower observability

## Phase Details

### Phase 1: Foundation & Infrastructure
**Goal**: The system can run end-to-end at the infrastructure level — backend serves API, Celery processes tasks, images upload/download via OSS, WeChat MP renders on device.
**Depends on**: Nothing (first phase)
**Requirements**: INFRA-01, INFRA-02, INFRA-03, INFRA-04
**Success Criteria** (what must be TRUE):
  1. User can open the WeChat Mini Program on a real device and see a landing page (domain whitelist configured, mp-weixin build works)
  2. Developer can hit a health-check endpoint on the FastAPI BFF and get a 200 response (skeleton running with PostgreSQL connected)
  3. A file can be uploaded to OSS via a presigned URL and downloaded back (upload/download round-trip verified)
  4. A test Celery task can be dispatched via API and its result retrieved (Redis broker + worker pipeline functional)
**Plans**: TBD
**UI hint**: yes

Plans:
- [ ] 01-01: TBD
- [ ] 01-02: TBD
- [ ] 01-03: TBD

### Phase 2: Auth, Data Layer & Admin CRUD
**Goal**: Users can authenticate via WeChat, admins can configure all product data (categories, styles, terms, rules), and the data layer provides the foundation for the AI generation pipeline.
**Depends on**: Phase 1
**Requirements**: AUTH-01, AUTH-02, AUTH-03, DATA-01, DATA-02, DATA-03, DATA-04, PROMO-01
**Success Criteria** (what must be TRUE):
  1. User can log in via WeChat and access authenticated APIs with a valid JWT
  2. Admin can create, edit, list, and delete categories, styles, terms, and promo rules via admin UI/API
  3. Authenticated user can fetch available categories and styles for selection (returns tenant-scoped data)
  4. Requests from tenant A cannot access tenant B's data (tenant isolation enforced on all queries)
  5. When WeChat session expires, the frontend silently re-authenticates without disrupting the user
**Plans**: TBD
**UI hint**: yes

Plans:
- [ ] 02-01: TBD
- [ ] 02-02: TBD
- [ ] 02-03: TBD

### Phase 3: AI Generation Pipeline
**Goal**: Users can upload product photos, and the system generates promotional images via the full AI pipeline — Vision analysis, prompt assembly, image generation, watermark overlay — with task tracking and result delivery.
**Depends on**: Phase 2
**Requirements**: PROMO-02, PROMO-03, GEN-01, GEN-02, GEN-03, GEN-04, GEN-05, GEN-06, GEN-07, GEN-08, GEN-09
**Success Criteria** (what must be TRUE):
  1. User can upload a product photo + demo image and trigger AI generation; a promotional image is returned (end-to-end pipeline works)
  2. User can track task progress via polling (sees queued → running → succeeded/failed transitions)
  3. Submitting the same client_request_id twice returns the same task without creating a duplicate or double-charging
  4. Generated results include both a watermarked image and a high-res raw image available for download via presigned URLs
  5. Changing admin rules after a task is created does not alter that task's frozen prompt snapshot (snapshot immutability verified)
**Plans**: TBD

Plans:
- [ ] 03-01: TBD
- [ ] 03-02: TBD
- [ ] 03-03: TBD

### Phase 4: Quota, Billing & Frontend UX
**Goal**: The complete user journey works end-to-end in the WeChat Mini Program — from login through generation to saving results — with quota management ensuring proper resource accounting.
**Depends on**: Phase 3
**Requirements**: QUOTA-01, QUOTA-02, QUOTA-03, QUOTA-04, UX-01, UX-02, UX-03, UX-04
**Success Criteria** (what must be TRUE):
  1. User can see remaining quota on the home page and profile page
  2. System freezes quota on task creation, deducts on success, and releases on failure (verified via ledger entries)
  3. User can complete the full wizard: login → select category → select style → upload photos → confirm → view progress → preview result → save to album
  4. User can browse past generations in "My Works" list with pull-to-refresh
  5. First-time user must accept privacy agreement before creating a generation task (agreement state persists)
**Plans**: TBD
**UI hint**: yes

Plans:
- [ ] 04-01: TBD
- [ ] 04-02: TBD
- [ ] 04-03: TBD

### Phase 5: Hardening & Launch Prep
**Goal**: The platform is production-ready with proper monitoring, standardized error handling, and automated recovery from stuck jobs.
**Depends on**: Phase 4
**Requirements**: ADMIN-01, ADMIN-02, ADMIN-03, INFRA-05
**Success Criteria** (what must be TRUE):
  1. Admin can query and filter generation tasks by status, date, and category, with detailed failure reason display
  2. All API errors return standardized error codes; the frontend maps them to user-friendly Chinese messages
  3. Jobs stuck in "running" for >5 minutes are automatically detected and transitioned to "failed" (watchdog functional)
  4. Error events are reported to Sentry; Celery task status is visible in Flower dashboard
**Plans**: TBD

Plans:
- [ ] 05-01: TBD
- [ ] 05-02: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation & Infrastructure | 0/3 | Not started | - |
| 2. Auth, Data Layer & Admin CRUD | 0/3 | Not started | - |
| 3. AI Generation Pipeline | 0/3 | Not started | - |
| 4. Quota, Billing & Frontend UX | 0/3 | Not started | - |
| 5. Hardening & Launch Prep | 0/2 | Not started | - |
