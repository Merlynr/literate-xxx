# Phase 4: Quota, Billing & Frontend UX - Validation

**Phase:** 4
**Status:** Ready for execution verification

## Validation Goals

- Verify quota is frozen when a generation task is created.
- Verify quota is deducted on successful completion.
- Verify quota is released when generation fails.
- Verify the user can see remaining quota on home and my pages.
- Verify the user must accept the privacy agreement before the first generation task.
- Verify the user can browse generation history and save a result to the photo album.

## Required Checks

### Backend
- `alembic upgrade head` succeeds on a clean database with the Phase 4 migration applied.
- API tests cover:
  - quota summary response fields
  - pricing plan CRUD
  - quota freeze/deduct/release transitions
  - consent acceptance and persistence
  - generation history pagination

### Frontend
- `vue-tsc --noEmit` succeeds after the new quota/history/privacy UI code lands.
- The home page renders a quota card instead of only the placeholder login bar.
- The my page renders quota plus history instead of only a menu.
- The generation page enforces privacy acceptance before submission and exposes album save actions after success.

### Manual UAT
- Login on app launch.
- Confirm quota is visible on the home page.
- Open the "My" page and confirm quota plus works history are visible.
- Attempt first generation without privacy acceptance and verify the app blocks submission.
- Accept the privacy agreement, create a generation job, and verify quota changes in the backend.
- Open a successful result and save it to the photo album.

## Failure Conditions

- Any generation job can be created without privacy acceptance on a first-time user.
- Quota remains unchanged after a successful job.
- Quota stays frozen after a failed job.
- History rows do not show result thumbnails or timestamps.
- Album save does not provide a permission fallback path.

---

*Phase: 04-quota-billing-frontend-ux*
*Validation written: 2026-05-13*
