# Phase 4: Quota, Billing & Frontend UX - Context

**Gathered:** 2026-05-13
**Status:** Ready for planning
**Source:** Roadmap + local code scan + existing Phase 3 implementation

<domain>
## Phase Boundary

This phase closes the product loop around the already-working generation pipeline:
- expose remaining quota in the Mini Program
- freeze quota on generation task creation, deduct on success, release on failure
- add pricing-plan management and quota ledger visibility
- complete the user journey from login to save-to-album
- add history browsing for past generations with pull-to-refresh
- require first-time privacy agreement acceptance before generation

The phase does not redesign the core AI pipeline. Phase 3 remains the source of truth for upload, prompt assembly, generation, and OSS delivery.
</domain>

<decisions>
## Implementation Decisions

### Quota model
- Use the roadmap's方案 A: freeze on task creation, deduct on success, release on failure.
- Track quota with a tenant-scoped account table plus append-only ledger entries.
- Keep pricing plans explicit and editable through backend CRUD so billing assumptions are visible in data.

### User-facing quota display
- Show remaining quota on the home page and on the "My" page.
- Expose quota summary through backend APIs rather than deriving it in the frontend.

### Privacy gate
- First-time users must accept the privacy agreement before creating a generation task.
- Acceptance state must persist so the user is not forced to re-accept on every launch.

### History and works browsing
- "My Works" is a generation-job history view, not a separate content system.
- The list should be paginated and refreshable so the frontend can support pull-to-refresh without loading all jobs at once.
- Each history row must include thumbnail, status, and timestamp, and reuse the existing signed download URLs from the generation pipeline.

### Album saving
- Save-to-album must use the WeChat Mini Program permission flow first.
- If permission is denied, provide a graceful fallback that explains how to enable album access or save manually.

### the agent's Discretion
- Exact table names, endpoint paths, and response schemas for quota/history/privacy.
- Whether privacy acceptance is stored on the user row, a dedicated consent table, or both.
- How much of the current simple home/my layout is retained versus refactored into reusable components.
- The exact visual treatment for quota cards and works rows, as long as the current brand palette is preserved.
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Roadmap and requirements
- `.planning/ROADMAP.md` — Phase 4 goal, requirements, and success criteria
- `.planning/REQUIREMENTS.md` — QUOTA-01..04 and UX-01..04 requirement definitions

### Existing frontend implementation
- `wx-fe/src/pages/index/index.vue` — current lightweight home page
- `wx-fe/src/pages/my/index.vue` — current profile/placeholder page
- `wx-fe/src/pages/generate/index.vue` — existing generation wizard entry point
- `wx-fe/src/stores/generation.ts` — current generation flow state machine
- `wx-fe/src/stores/user.ts` — current auth bootstrap and dev-login fallback
- `wx-fe/src/api/generation.ts` — current category/style/upload/job API integration
- `wx-fe/src/pages.json` — current tab bar and page registration

### Existing backend implementation
- `python-bff/app/api/v1/auth.py` — auth/dev-login/me endpoints
- `python-bff/app/api/v1/generation.py` — upload confirm, job create, job read APIs
- `python-bff/app/services/generation_jobs.py` — asset confirmation and job lifecycle helpers
- `python-bff/app/services/generation_results.py` — result OSS persistence helpers
- `python-bff/app/models/generation_job.py` — generation job schema and unique constraints
- `python-bff/app/models/generation_asset.py` — generation asset schema and download URL assumptions

### Phase 3 context
- `.planning/phases/03-ai-generation-pipeline/03-CONTEXT.md` — prior locked generation decisions, if present
</canonical_refs>

<specifics>
## Specific Ideas

- Home page can stay a single-screen entry point, but it now needs a visible quota card and a path into the generation wizard.
- The "My" tab is the natural place for quota detail, generation history, and privacy agreement status.
- Generation history should likely reuse the existing `generation_jobs` table instead of introducing a separate works table.
- The quota ledger should capture event type, delta, balance before/after, job_id, and tenant_id so admin inspection remains auditable.
- The frontend already has a `busy` state and upload/result panels in the generation store, so Phase 4 should extend those states instead of replacing them.
</specifics>

<deferred>
## Deferred Ideas

- No explicit v2-only features were identified in the roadmap for Phase 4.
- Advanced billing integrations, coupons, or external payment providers are out of scope for this phase unless a later requirement adds them.
</deferred>

---

*Phase: 04-quota-billing-frontend-ux*
*Context gathered: 2026-05-13 via roadmap + code scan*
