# Domain Pitfalls

**Domain:** AIGC E-commerce Product Image Generation Platform (XX甄选)
**Researched:** 2026-05-12
**Overall confidence:** MEDIUM — project-specific architecture details confirmed from PROJECT.md + 技术规格; ecosystem patterns from domain expertise (training data, last verified concepts)

---

## Critical Pitfalls

### 1. WeChat Mini Program Download Domain Whitelist Blocks Image Delivery

**What goes wrong:** Generated images stored on OSS (e.g., `xxx.oss-cn-hangzhou.aliyuncs.com`) fail to display or download in the Mini Program because the domain is not whitelisted in the WeChat MP admin console. Users see blank images or download failures with no clear error.

**Why it happens:** WeChat MP requires ALL network request domains AND download domains to be pre-registered in the MP admin console. OSS bucket URLs are not automatically allowed. The whitelist covers `request` (API calls), `uploadFile`, `downloadFile`, and `socket` domains separately — missing any one causes silent failures for that category.

**Consequences:**
- Images appear to generate successfully (job status = `succeeded`) but users cannot view or download them
- Watermarked images and raw images may use different domains, doubling the whitelist work
- CDN domain (if fronting OSS) must ALSO be whitelisted separately

**Prevention:**
- Register ALL domains in WeChat MP console before first deployment: BFF API domain, OSS domain(s), CDN domain(s)
- Use a single canonical domain for all image delivery (prefer CDN in front of OSS)
- Write a pre-deployment checklist that validates domain whitelist entries
- Test image download via `wx.downloadFile` and `wx.saveImageToPhotosAlbum` in real device mode, not just simulator

**Detection:** Images load in DevTools but not on real device; `wx.downloadFile` returns `fail url not in domain list` error.

**Phase to address:** Phase 1 (Infrastructure + first deployment pipeline must include domain whitelist setup)

---

### 2. AI Image Generation Output Is Non-Deterministic — Users Get Unpredictable Quality

**What goes wrong:** Same prompt + same input photo produces different images each call. Some results are excellent, some are unusable. Users complain about inconsistency, and there's no way to "regenerate the same result."

**Why it happens:** All current image generation APIs (Codex, Gemini, DALL-E, etc.) are stochastic. Temperature/seed parameters are either unavailable or poorly documented. The Vision API analysis of a demo image is also non-deterministic — it may describe the same image differently on each call.

**Consequences:**
- Users burn quota on bad results and feel cheated
- No "retry same settings" guarantees the same output
- Quality variance undermines trust in the product
- Free/demo scenarios show curated best-case; user's actual results are worse

**Prevention:**
- **Seed pinning**: If the image gen API supports a `seed` parameter, store it with the job so users can "re-roll" or regenerate with the same seed. Document which APIs support this.
- **Quality gate**: Add a lightweight quality check (image dimensions, aspect ratio, obvious corruption) before showing results. Auto-retry once on low-quality output.
- **Preview mode**: Allow users to generate a low-res preview before consuming full quota
- **Variance disclosure**: UI should communicate that results vary and offer "regenerate" without re-consuming all quota (or at reduced cost)
- **Prompt template stability**: Use versioned prompt templates (see Pitfall #5) to minimize drift from prompt-side changes

**Detection:** User support tickets about "my images look different each time"; users abandoning after 1-2 generations.

**Phase to address:** Phase 1 (core generation flow must handle variance) + Phase 2 (quality gates, seed management)

---

### 3. Celery Worker Crashes or Hangs on AI API Timeouts → Jobs Stuck in "Running" Forever

**What goes wrong:** A Celery worker calls the image gen API, the API takes 60+ seconds (or hangs entirely), the worker thread blocks, and the job stays in `running` state permanently. If multiple calls hang, all workers are exhausted and the queue stops processing.

**Why it happens:**
- AI image generation APIs have highly variable latency (10s–120s+). Default HTTP timeouts are often too short.
- Celery tasks that make synchronous HTTP calls block the worker process. With `prefetch_multiplier=1` and limited concurrency, a few hanging tasks paralyze the system.
- Redis as broker means if Redis restarts, unacknowledged tasks can be lost or duplicated.

**Consequences:**
- Jobs stuck in `running` forever — users see perpetual "generating" spinner
- Worker pool exhaustion means ALL new jobs queue indefinitely
- No automatic recovery without manual intervention

**Prevention:**
- **Hard timeout + soft timeout**: Set `task_time_limit=180` (hard kill) and `task_soft_time_limit=150` (graceful signal) on the image generation task. Use `on_failure` handler to mark job as `failed` with timeout error code.
- **Async HTTP in workers**: Use `httpx` with async/await inside Celery tasks (or `gevent` pool) to avoid thread blocking on I/O.
- **Circuit breaker**: After N consecutive timeouts from the AI vendor, pause new submissions for 60s and surface a "vendor degraded" signal to the frontend.
- **Dead letter queue**: Configure Celery `task_reject_on_worker_lost=True` and a DLQ for tasks that fail repeatedly.
- **Heartbeat + watchdog**: Use Celery flower or a custom watchdog to detect workers with tasks running > 5 minutes and alert.
- **Redis persistence**: Enable Redis AOF persistence (`appendonly yes`) to survive restarts. Consider `REQUIREPASS` and connection pooling.
- **Job reconciliation**: A periodic background task scans for jobs stuck in `running` for > 5 minutes and transitions them to `failed`.

**Detection:** Celery Flower dashboard shows tasks with runtime > 5 minutes; job status query returns stale `running` states; Redis `LLEN` on queue grows without processing.

**Phase to address:** Phase 1 (task queue reliability is foundational — must ship with timeouts and recovery)

---

### 4. WeChat Mini Program `wx.saveImageToPhotosAlbum` Requires User Authorization and Fails Silently on iOS

**What goes wrong:** After generating an image, the user taps "Save to Album." On iOS, if the user previously denied photo library access, the save fails silently or shows a generic error. On Android, the permission flow is different. Users don't understand why they can't save.

**Why it happens:** WeChat's `authorize` API for `scope.writePhotosAlbum` is a one-shot prompt. If the user taps "Deny," subsequent calls to `saveImageToPhotosAlbum` fail without re-prompting. The only recovery is to manually go to system Settings → WeChat → Photos → Allow.

**Consequences:**
- Users complete the generation flow but can't save their image — terrible UX for a paid action
- Support burden: "I paid but can't download my image"
- If using quota/freeze billing model, user consumed quota but can't access result

**Prevention:**
- **Pre-flight auth check**: Before showing the save button, call `wx.getSetting` to check `scope.writePhotosAlbum`. If denied, show a custom dialog guiding the user to system settings.
- **Graceful fallback**: Offer "Copy link" or "Long-press to save" (showing the image in a `<image>` element that supports native long-press save on WeChat) as alternatives.
- **Authorization on first use**: Trigger `wx.authorize({scope: 'scope.writePhotosAlbum'})` early in the flow, not at the save moment, so users understand the context.
- **Test on real devices**: This behavior differs between iOS and Android, and between WeChat versions. Test on both.

**Detection:** Crash reports or analytics showing successful generation but failed save attempts; user complaints.

**Phase to address:** Phase 1 (save/download is core UX, must work from day 1)

---

### 5. Prompt Template Drift — Changing Prompts Breaks Historical Task Reproducibility

**What goes wrong:** An operator updates the prompt template (wording, style descriptions, negative prompts) in the admin panel. Old tasks that were created under the old prompt now show different results if re-run, and the admin can't understand why "the same style produces different results now."

**Why it happens:** The spec says "任务创建时固化规则版本 + Prompt，历史任务不受后续改规则影响" (snapshot at creation time). But the implementation must actually store the COMPLETE assembled prompt, not just a reference to the rule version. If the rule engine is re-evaluated on re-run, any code change to the assembly logic invalidates historical snapshots.

**Consequences:**
- "Re-run" of historical jobs produces different results
- A/B testing of prompt changes is impossible without proper versioning
- Debugging production quality issues requires knowing the exact prompt used

**Prevention:**
- **Store full prompt text in `generation_job`**: Not a reference to a rule, but the fully assembled prompt string. This is the only way to guarantee true snapshot isolation.
- **Immutable rule versions**: Rule versions are append-only. Editing creates a new version; old version remains accessible.
- **Prompt hash**: Compute and store a SHA-256 hash of the assembled prompt. Use this for deduplication and debugging.
- **A/B testing infrastructure**: Route a percentage of jobs through a different prompt version, compare success rates and quality scores.

**Detection:** Re-running a historical job produces different output; admin reports "rule changes affect old jobs."

**Phase to address:** Phase 1 (snapshot mechanism is architectural — must be correct from the start)

---

## Moderate Pitfalls

### 6. Image Gen API Cost Spikes — Uncontrolled Billing from Retry Storms

**What goes wrong:** A transient API failure triggers automatic retries. Each retry costs money. A cascade failure (API partially degraded, returning errors intermittently) causes exponential retry amplification. A single user's failed job can consume 5-10x the expected API cost.

**Why it happens:** Celery's default retry behavior (`autoretry_for`, `retry_backoff`) will keep retrying failed tasks. If the AI API charges per-call regardless of success, each retry costs money. The freeze/quota model may not account for retries.

**Prevention:**
- **Cap retries**: `max_retries=2` for AI API calls, not unlimited. After 2 retries, fail the job and refund quota.
- **Exponential backoff with jitter**: `retry_backoff=True, retry_jitter=True` to avoid thundering herd.
- **Cost-aware retry**: Only retry on transient errors (429 rate limit, 503 service unavailable), NOT on permanent errors (400 bad request, content policy violation).
- **Daily cost circuit breaker**: Set a daily API spend limit. When approaching it, slow down submission rate or queue jobs for off-peak processing.
- **Billing reconciliation**: Log every API call (success/failure/retry) with cost metadata. Build a daily cost report.

**Detection:** Sudden spike in API costs; `task-retried` events in Celery Flower; ratio of API calls to successful jobs > 2:1.

**Phase to address:** Phase 1 (retry logic) + Phase 2 (cost monitoring dashboard)

---

### 7. OSS Upload Race Condition — User Uploads Image But Presigned URL Expires Before Completion

**What goes wrong:** Backend generates a presigned OSS upload URL (valid for 60s). User is on slow mobile network. Upload starts but doesn't complete before the URL expires. Upload fails with `403 Forbidden`. User is confused.

**Why it happens:** Presigned URLs have a fixed expiration. Mobile networks (especially in rural areas — this is an agricultural product app) can be unreliable. Large images (5-10MB from phone cameras) on 3G/4G can take 30-60+ seconds.

**Prevention:**
- **Long presigned URL TTL**: Set expiration to 300s (5 minutes) for upload URLs. Balance security vs. usability.
- **Client-side compression**: Compress images before upload (quality 80%, max dimension 2048px). WeChat's `wx.compressImage` can reduce 5MB → 500KB.
- **Retry with new URL**: If upload fails with 403, request a new presigned URL and retry transparently.
- **Upload progress feedback**: Show upload progress bar so users know something is happening.
- **Backend validation**: After upload, verify the object exists in OSS before creating the job.

**Detection:** User reports "upload failed" errors; 403 responses in OSS access logs; high upload abandonment rate.

**Phase to address:** Phase 1 (upload is first interaction — must be smooth)

---

### 8. Uni-app `wx.previewImage` and File System Differences Between Platforms

**What goes wrong:** Development uses H5 mode for fast iteration. Image preview (`previewImage`) works perfectly in H5. Compilation to WeChat Mini Program has different behavior — local file paths don't work, network URLs require domain whitelist, and `canvas` rendering behaves differently.

**Why it happens:** Uni-app abstracts platform differences, but leaks through for file/image APIs:
- `uni.previewImage` in H5 uses browser's native preview; in WX MP it uses WeChat's fullscreen viewer
- `uni.saveImageToPhotosAlbum` needs the image to be a local temp file path or network URL — base64 data URLs don't work in WX MP
- `canvas` for watermark overlay has different coordinate systems and font rendering in WX MP vs H5

**Prevention:**
- **Test in WX MP mode early**: Don't defer Mini Program testing to the end. Use `uni.preview -p mp-weixin` or real device testing from phase 1.
- **Use network URLs exclusively**: Store all images in OSS and use signed URLs. Never rely on local file paths or base64 data URIs for display.
- **Canvas watermark on server**: Do watermark overlay server-side (PIL/Pillow) rather than client-side canvas. Client-side canvas in WX MP has font rendering issues and performance problems.
- **File size limits**: WeChat MP package size limit is 2MB (main package), 20MB total with subpackages. Image assets eat this fast. Use CDN for all images, not bundled assets.

**Detection:** Features work in H5 dev mode but fail in WX MP build; canvas rendering artifacts; image display failures.

**Phase to address:** Phase 1 (must validate WX MP behavior from the start, not retroactively)

---

### 9. Vision API Label Generation Is Inconsistent Across Demo Images

**What goes wrong:** The Vision API (GPT-4o-mini) analyzes a demo/reference image to generate descriptive labels (background, lighting, composition, style). The same demo image analyzed twice produces different label sets. This means the assembled prompt varies, causing downstream image generation results to drift.

**Why it happens:** GPT-4o-mini's vision analysis is non-deterministic. It may focus on different aspects of the image each time. Structured output (JSON mode) helps with format consistency but not content consistency.

**Prevention:**
- **Cache Vision API results**: Analyze each demo image ONCE and cache the labels. Store in the `style` or `promo_rule_version` table. Only re-analyze if the demo image changes.
- **Structured output with constraints**: Use JSON mode with a fixed schema: `{"background": "...", "lighting": "...", "composition": "...", "style": "...", "mood": "..."}`. Force the model to fill every field.
- **Temperature = 0**: Set temperature to 0 for vision analysis to maximize determinism.
- **Human-curated fallback**: For the initial 4 SKUs, pre-generate and manually verify the labels. Store as the canonical labels.

**Detection:** Same demo image produces different prompts on different requests; quality variance on same style + same input photo.

**Phase to address:** Phase 1 (label caching is part of the core pipeline)

---

### 10. WeChat Mini Program Image Size Limits — `wx.chooseImage` Returns Files Too Large for Processing

**What goes wrong:** Users take photos with modern phones (50MP+ cameras). The resulting images are 10-20MB. Upload is slow, OSS storage costs increase, and the AI API may reject or downscale the input, losing the benefit of high resolution.

**Why it happens:** `wx.chooseImage` does not compress by default. The `sizeType` parameter can request compression, but the behavior varies by device and WeChat version. Users in agricultural product contexts may use older phones with inconsistent compression.

**Prevention:**
- **Client-side compression mandatory**: Call `wx.compressImage` after `chooseImage`. Target: max 2048px on longest side, quality 80%. This typically reduces 10MB → 500KB-1MB.
- **Server-side validation**: Reject uploads > 5MB. Return a clear error: "图片过大，请压缩后重试."
- **Dimension check**: Validate image dimensions (min 512x512, max 4096x4096) server-side before sending to AI API.
- **Progressive upload**: Show compression progress, then upload progress, so the user understands the wait.

**Detection:** Upload timeouts; AI API rejecting large images; high OSS storage costs for raw photos.

**Phase to address:** Phase 1 (upload flow)

---

## Minor Pitfalls

### 11. Redis as Single Point of Failure for Both Queue and Cache

**What goes wrong:** Redis serves as both Celery's task broker AND application cache (session data, API response cache, quota lookups). If Redis goes down, the entire system stops — no new jobs can be queued, no cached data is available, and the frontend shows errors.

**Prevention:**
- **Separate Redis instances** (or at least separate databases): `redis:0` for Celery broker, `redis:1` for cache. This prevents cache eviction from affecting the queue.
- **Persistence config**: Enable AOF (`appendfsync everysec`) for the broker Redis. For cache Redis, RDB snapshots are sufficient.
- **Connection pool tuning**: Set `socket_connect_timeout=5`, `socket_timeout=10`, `retry_on_timeout=True` in Celery Redis config.
- **Graceful degradation**: If Redis cache is unavailable, fall back to PostgreSQL for quota lookups (slower but functional). If broker is unavailable, queue API returns 503 with "system busy" — don't silently lose requests.

**Detection:** Celery workers log connection errors; quota API returns 500; task submission fails with broker connection error.

**Phase to address:** Phase 1 (infrastructure baseline)

---

### 12. Watermark Logo Placement Fails on Non-Standard Image Sizes

**What goes wrong:** Watermark/logo overlay uses fixed pixel coordinates (e.g., bottom-right corner at 100px from edge). When the AI generates images with unusual aspect ratios or sizes, the watermark appears in the wrong position — overlapping key content, or cut off at the edge.

**Prevention:**
- **Percentage-based positioning**: Place watermark at 90% from left, 90% from top (percentage of image dimensions), not fixed pixels.
- **Scale watermark to image**: Watermark size should be proportional to image size (e.g., 10% of image width), not fixed pixel size.
- **Safe zone validation**: After overlaying, check that the watermark doesn't overlap detected faces or product areas (advanced — defer to P2).
- **Server-side rendering**: Use Pillow `Image.paste()` with alpha compositing. Don't rely on client-side canvas.

**Phase to address:** Phase 1 (watermark is part of core pipeline)

---

### 13. `client_request_id` Idempotency Key Not Actually Idempotent

**What goes wrong:** The spec requires `client_request_id` for idempotency — same ID = same job returned. But if the implementation checks the database for the ID and creates the job in two separate steps (not atomic), a race condition allows duplicate jobs under the same client_request_id.

**Why it happens:** Classic TOCTOU (time-of-check-to-time-of-use) race. Two concurrent requests with the same `client_request_id` both pass the "does it exist?" check before either inserts.

**Prevention:**
- **Database unique constraint**: `CREATE UNIQUE INDEX ON generation_job(client_request_id)`. The database enforces uniqueness atomically. Handle `IntegrityError` by fetching and returning the existing job.
- **No application-level check needed**: Don't SELECT-then-INSERT. INSERT directly and catch the unique constraint violation.
- **Redis lock as optimization**: Optional `SETNX` lock on `client_request_id` with 30s TTL as a fast-path rejection, but the DB constraint is the source of truth.

**Detection:** Duplicate jobs visible in database with same `client_request_id`; user charged twice for same request.

**Phase to address:** Phase 1 (idempotency is foundational)

---

### 14. WeChat Login Session Key Expiry Causes Silent Auth Failures

**What goes wrong:** WeChat login returns a `session_key` that can expire. If the backend caches the session and doesn't handle expiry, subsequent API calls (including `wx.getUserInfo`, encrypted data decryption) silently fail. Users appear logged in but operations fail.

**Prevention:**
- **Don't cache session_key long-term**: WeChat's `session_key` can be invalidated at any time by WeChat's server. Store it per-session with a TTL (e.g., 2 hours), and re-login when expired.
- **Handle `errcode: -41001` and `errcode: -41003`**: These indicate expired session_key. Frontend should detect and trigger re-login flow.
- **Silent re-login**: Use `wx.checkSession` to validate the session before critical operations. If invalid, call `wx.login` again without disrupting the user.

**Detection:** API calls return "invalid session" errors; users report being "logged in" but features not working.

**Phase to address:** Phase 1 (auth is prerequisite for everything)

---

### 15. OSS Signed URL Expiry Causes Stale Image Links in Task List

**What goes wrong:** Generated images are stored in OSS with signed URLs (time-limited). The task list and result pages show these URLs. If the user revisits an old task after the URL expires, images fail to load.

**Prevention:**
- **Generate signed URLs on-demand**: Don't store signed URLs in the database. Store the OSS object key (e.g., `jobs/{job_id}/result.png`) and generate fresh signed URLs when the API is called.
- **URL TTL strategy**: For result viewing, 1-hour TTL is usually sufficient. For "save to album" actions, generate a fresh URL immediately before the action.
- **Consider public-read for result images**: If watermark is applied and images are meant for public display (product listings), use public-read ACL instead of signed URLs. Saves complexity.

**Detection:** Users report "images disappeared" from old tasks; 403 errors on image URLs in task detail.

**Phase to address:** Phase 1 (image storage and delivery architecture)

---

### 16. Uni-app Conditional Compilation Gaps — `#ifdef` Missed for WX-Specific APIs

**What goes wrong:** Developer uses a WeChat-specific API (e.g., `wx.getFileSystemManager()`) without `#ifdef MP-WEIXIN` conditional compilation guard. Works in H5 mode (polyfilled or ignored), crashes in WX MP build.

**Prevention:**
- **Linting rule**: Add an eslint/uni-app lint rule that flags `wx.` or `uni.` APIs known to have platform differences.
- **Code review checklist**: Any file system, camera, or image API usage must have `#ifdef` guards or documented platform compatibility.
- **CI build for both targets**: Run `uni build -p mp-weixin` in CI, not just H5. Catch compilation errors early.

**Phase to address:** Phase 1 (build pipeline setup)

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation | # |
|-------------|---------------|------------|---|
| Upload + OSS | Presigned URL expiry on slow networks | 300s TTL + client compression + retry | 7, 10 |
| WeChat Auth | Session key expiry, silent failures | `wx.checkSession` + auto re-login | 14 |
| Domain Whitelist | Images don't load in MP | Register all domains before first deploy | 1 |
| Task Queue (Celery + Redis) | Workers hang on API timeout | Hard timeout + circuit breaker + watchdog | 3, 11 |
| AI Generation Pipeline | Non-deterministic output quality | Seed pinning + quality gate + variance disclosure | 2, 9 |
| Prompt Assembly | Drift breaks historical tasks | Store full prompt hash + immutable rule versions | 5 |
| Billing / Quota | Retry storms amplify costs | Retry cap + cost circuit breaker + error classification | 6 |
| Image Delivery | Signed URL expiry on old tasks | Generate URLs on-demand, not at creation time | 15 |
| Watermark Overlay | Wrong placement on unusual sizes | Percentage-based positioning + server-side rendering | 12 |
| Uni-app → WX MP | Platform API mismatches | `#ifdef` guards + CI for both targets + early MP testing | 8, 16 |
| Idempotency | Duplicate jobs under race condition | DB unique constraint, not app-level check | 13 |
| Compliance | AI-generated image copyright | See "Open Questions" below | — |

---

## Open Questions (Need Phase-Specific Research)

### AI-Generated Image Copyright & Compliance (China jurisdiction)
**Uncertainty:** HIGH — Chinese courts have issued conflicting rulings on AI-generated image copyright in 2024-2025. The Beijing Internet Court ruled AI-generated images CAN be copyrighted if sufficient human creative input is demonstrated. But this is not settled law.
**Risk:** If the generated product images are later deemed non-copyrightable, competitors could freely copy them. If the AI training data included copyrighted works, there may be claims from original artists.
**What to research before P1:**
- Current stance of Chinese regulators on AI-generated commercial images
- Platform-specific rules (WeChat, Taobao, Pinduoduo) on AI-generated product listing images
- Whether watermarks on AI images affect their legal status
- Whether the AI vendor (Codex/Gemini) provides IP indemnification

### LEX-AI API Behavior Specifics
**Uncertainty:** MEDIUM — The spec mentions LEX-AI as the primary image gen engine but also references Codex/Gemini API as alternatives. The actual API contract, error codes, rate limits, and timeout behavior of LEX-AI are not documented in the project files.
**What to research before Phase 1:**
- LEX-AI API documentation: request/response schema, supported parameters
- Rate limits and concurrency caps
- Synchronous vs. async invocation modes
- Error codes and retry semantics
- Pricing model (per-call, per-pixel, per-token?)

### WeChat Mini Program Subpackage Strategy
**Uncertainty:** MEDIUM — With 4 SKUs, multiple style templates, and admin features, the total MP package may approach the 20MB limit if assets are bundled.
**What to research before Phase 1:**
- Current MP package size limits (main + subpackages + plugins)
- Whether to use subpackages for admin/collection pages vs. main generation flow
- WeChat plugin support for shared functionality

### Celery Worker Scaling on Windows
**Uncertainty:** LOW-MEDIUM — The development environment appears to be Windows (based on file paths). Celery 5.x+ dropped official Windows support. Running Celery workers on Windows requires workarounds.
**What to research:**
- Use `--pool=solo` or `--pool=threads` on Windows (no `prefork`)
- For production, deploy on Linux. Document this as a hard requirement.
- Alternative: consider `arq` (async Redis queue) which has better Windows support

---

## Sources

- WeChat Mini Program official documentation: domain whitelist, `wx.saveImageToPhotosAlbum`, `wx.chooseImage`
- Celery official documentation: task timeouts, retry policies, Redis broker configuration
- Uni-app official documentation: conditional compilation, platform differences
- OpenAI API documentation: image generation parameters, rate limits
- Alibaba Cloud OSS documentation: presigned URLs, lifecycle policies
- Beijing Internet Court ruling on AI-generated images (2023-12, Li Yunkai v. Liu Yuanchun)
- Project-specific sources: PROJECT.md, 技术规格.md

*Note: Confidence is MEDIUM overall. WeChat MP restrictions, Celery pitfalls, and OSS patterns are well-established knowledge (HIGH confidence on mechanism). Specific API behaviors (LEX-AI, Codex image gen) need validation against actual vendor documentation (LOW confidence on specifics). Copyright landscape is actively evolving (LOW confidence on legal outcomes).*