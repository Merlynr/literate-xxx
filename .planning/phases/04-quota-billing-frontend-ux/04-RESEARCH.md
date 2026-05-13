# Phase 4: Quota, Billing & Frontend UX - Research

**Gathered:** 2026-05-13
**Status:** Ready for planning
**Scope:** Phase 4 planning support only

## What the codebase already gives us

- `wx-fe/src/pages/generate/index.vue` already implements the main generation shell: category selection, style selection, upload, prompt hint, progress, and result preview.
- `wx-fe/src/stores/generation.ts` already has the generation state machine, catalog loading, upload-confirm flow, job polling, and result URL handling.
- `wx-fe/src/stores/user.ts` already auto-authenticates and has a dev-login fallback, so Phase 4 can rely on an authenticated user store on all tabs.
- `python-bff/app/api/v1/generation.py` already exposes asset confirm, job create, and job read endpoints.
- `python-bff/app/services/generation_jobs.py` already contains the right service layer for job lifecycle extension.
- The current home and my pages are intentionally lightweight and can be extended without replacing the navigation model.

## Gaps to close

- There is no quota/billing model yet: no quota account, no ledger, no pricing plan, and no quota summary endpoint.
- There is no privacy agreement persistence or first-generation consent gate.
- There is no generation history API designed for a "My Works" list.
- The "My" page is currently a placeholder menu and does not yet show quota or history.
- The generation page does not yet handle save-to-album permission flow.

## Recommended implementation pattern

- Keep quota accounting on the backend, not in frontend local state.
- Treat the generation job as the source of truth for history rows and result URLs.
- Add consent state as a user-scoped backend record so the frontend can check it once and cache it.
- Use the existing tab bar and visual language; do not introduce a second brand system for Phase 4.
- Reuse the current Pinia stores and API helper pattern instead of creating a parallel request layer.

## Risks

- The phase touches both billing semantics and frontend UX, so the implementation should keep quota operations small and testable.
- No dedicated UI design contract exists yet for Phase 4, so the plan should preserve the current green/gold mini-program palette and avoid a redesign detour.
- The history page can become expensive if it loads all jobs at once; pagination or cursor-based queries are safer.
- Album saving permissions vary by device and WeChat version; the frontend needs a fallback path rather than a hard failure.

## Validation Architecture

Phase 4 should be validated across three layers:

1. Backend unit and API tests
   - quota freeze/deduct/release transitions
   - pricing plan CRUD
   - quota summary and estimate responses
   - privacy acceptance and generation history reads

2. Frontend type/build checks
   - `vue-tsc --noEmit`
   - existing component imports and store contracts compile cleanly

3. Manual UAT in the Mini Program / H5
   - login on launch
   - see quota on home and my pages
   - accept privacy agreement on first generation
   - create a job and verify quota freeze/release behavior
   - open a history item and save the result to album

---

*Phase: 04-quota-billing-frontend-ux*
*Research gathered: 2026-05-13*
