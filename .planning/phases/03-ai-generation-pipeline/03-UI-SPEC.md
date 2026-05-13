# Phase 3: AI Generation Pipeline - UI-SPEC

**Status:** Ready for planning
**Scope:** Generate page, upload flow, task progress, result preview

## UI Contract

### Product feel

- Tone: premium, agricultural, clean, practical.
- Visual direction: warm cream base, deep green accents, solar gold highlights.
- Mood: trustworthy utility, not playful consumer app.
- Avoid generic purple gradients and default admin-card styling.

### Primary screen structure

- Entry point: `generate` tab page.
- Layout: one primary page with a visible step progression.
- Recommended steps:
  - Select category
  - Select style
  - Upload product photo
  - Upload demo/reference image
  - Confirm generation
  - Poll progress
  - View result

### Key components

- Step header: compact stepper that shows the current stage and the next stage.
- Category selector: card grid with clear selected state.
- Style selector: image-first card grid with cover art and short labels.
- Upload area:
  - two upload cards, one for product photo and one for demo/reference image
  - show preview thumbnail, file size, and replace action
  - show compression/upload status before task creation
- Confirmation panel:
  - summary of selected category, style, and uploaded assets
  - primary CTA to create the generation job
  - secondary action to go back and edit inputs
- Progress panel:
  - queued, running, succeeded, failed states
  - show elapsed time and a plain-language status hint
- Result panel:
  - show watermarked image as the default preview
  - provide raw image as a secondary download action
  - provide retry action on failure

### State rules

- Empty state: explain the three required inputs, not just "come back later".
- Loading state: use skeleton cards for category/style selections and a progress placeholder for the worker job.
- Error state: show actionable recovery text, such as re-upload, retry generation, or return to previous step.
- Success state: emphasize the generated result first, then expose download actions.

### Interaction rules

- The user should never see a blank page during polling.
- The create-job action must be disabled until both uploads are confirmed.
- The same page should support retry after failure without forcing a full refresh.
- Preserve the selected category/style when the job is retried.

### Responsive rules

- Mobile-first layout.
- Selector grids collapse to one column on very small screens and two columns on normal phones.
- The primary CTA remains sticky at the bottom on mobile.

### Copy rules

- Use short Chinese labels.
- Status text should be explicit: queued / running / succeeded / failed.
- Avoid technical jargon in user-facing hints.

## Planning Notes

- This UI spec is intentionally minimal and only covers the phase 3 generation flow.
- It does not define the later quota/billing or full wizard polish that belongs to phase 4.

