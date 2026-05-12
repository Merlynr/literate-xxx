# Architecture Patterns

**Domain:** AIGC E-commerce Product Image Generation
**Researched:** 2026-05-12
**Confidence:** HIGH — grounded in validated tech spec (商品宣传图-产品与技术规格.md) plus standard FastAPI/Celery patterns

## Recommended Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          Clients                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │
│  │  WeChat Mini  │  │   Admin UI   │  │  Future      │               │
│  │  Program      │  │   (Desktop)  │  │  OpenAPI     │               │
│  │  (Uni-app)    │  │              │  │  (P2)        │               │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘               │
│         │ REST             │ REST             │ REST                  │
└─────────┼─────────────────┼─────────────────┼───────────────────────┘
          │                 │                 │
          ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    FastAPI BFF (python-bff/)                         │
│                                                                     │
│  ┌─────────────┐ ┌──────────────┐ ┌─────────────┐ ┌──────────────┐ │
│  │  Auth Layer  │ │  Job API     │ │  Config API  │ │  Upload API  │ │
│  │  (WX Login)  │ │  (CRUD+Poll) │ │  (Admin CRUD)│ │  (Presign)   │ │
│  └──────┬──────┘ └──────┬───────┘ └──────┬──────┘ └──────┬───────┘ │
│         │               │                │                │         │
│         ▼               ▼                ▼                │         │
│  ┌─────────────────────────────────────────────┐          │         │
│  │          Service Layer (Business Logic)      │          │         │
│  │  ┌────────────┐ ┌────────────┐ ┌──────────┐ │          │         │
│  │  │ Quota Mgr  │ │ Rule Engine │ │Prompt    │ │          │         │
│  │  │ (Freeze/   │ │ (Snapshot  │ │Assembler │ │          │         │
│  │  │  Deduct)   │ │  + Eval)   │ │(Rule+Tag)│ │          │         │
│  │  └────────────┘ └────────────┘ └──────────┘ │          │         │
│  └──────────────────────┬──────────────────────┘          │         │
│                         │                                  │         │
│          ┌──────────────┼──────────────────┐              │         │
│          ▼              ▼                  ▼              ▼         │
│  ┌──────────────┐ ┌──────────┐ ┌──────────────┐ ┌──────────────┐   │
│  │  PostgreSQL   │ │  Redis   │ │  Celery      │ │     OSS      │   │
│  │  (Persist)    │ │  (Cache  │ │  (Dispatch)  │ │  (Presign)   │   │
│  │              │ │   Broker)│ │              │ │              │   │
│  └──────────────┘ └──────────┘ └──────┬───────┘ └──────────────┘   │
└───────────────────────────────────────┼─────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  Celery Workers                                      │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    Task Execution Pipeline                    │   │
│  │                                                              │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐ │   │
│  │  │ 1. Vision API │  │ 2. Prompt    │  │ 3. Image Gen API  │ │   │
│  │  │ (Analyze Demo)│→ │    Assembly  │→ │ (Generate Image)  │ │   │
│  │  └──────────────┘  └──────────────┘  └─────────┬──────────┘ │   │
│  │                                                 │            │   │
│  │  ┌──────────────┐  ┌──────────────┐            │            │   │
│  │  │ 5. Update DB  │← │ 4. Upload    │←───────────┘            │   │
│  │  │ (Status+URL)  │  │    to OSS    │                         │   │
│  │  └──────────────┘  └──────────────┘                         │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │              AI Provider Abstraction Layer                    │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │   │
│  │  │ IVisionProvider│ │IImageGenProv.│  │ Future...    │       │   │
│  │  │ ┌────────────┐│  │ ┌────────────┐│  │              │       │   │
│  │  │ │GPT4oMini   ││  │ │CodexAPI    ││  │              │       │   │
│  │  │ │Provider    ││  │ │Provider    ││  │              │       │   │
│  │  │ └────────────┘│  │ ├────────────┤│  │              │       │   │
│  │  │ ┌────────────┐│  │ │GeminiAPI   ││  │              │       │   │
│  │  │ │GeminiVision││  │ │Provider    ││  │              │       │   │
│  │  │ │Provider    ││  │ └────────────┘│  │              │       │   │
│  │  │ └────────────┘│  └──────────────┘  └──────────────┘       │   │
│  │  └──────────────┘                                             │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### Component Boundaries

| Component | Responsibility | Communicates With | Port/Layer |
|-----------|---------------|-------------------|------------|
| **Uni-app Frontend** | User-facing UI: upload, selection wizard, task polling, result preview/download | BFF only (REST) | `wx-fe/` |
| **Admin UI** | CRUD for categories, styles, terms, rules, pricing; task monitoring | BFF only (REST) | Desktop web, same BFF |
| **FastAPI BFF** | API gateway, auth, business logic orchestration, presigned upload URLs | PostgreSQL, Redis, Celery, OSS | `python-bff/` |
| **Auth Layer** | WeChat login, token management, tenant binding | Redis (session), PostgreSQL (user) | Inside BFF |
| **Rule Engine** | Evaluate promo rules against category+style+tag combo; produce rule snapshot | PostgreSQL (rules, terms) | Inside BFF service layer |
| **Prompt Assembler** | Deterministic, rule-based prompt construction from snapshot + tags | No external deps (pure logic) | Inside BFF service layer |
| **Quota Manager** | Freeze/deduct/refund quota; ledger append-only writes | PostgreSQL (quota_account, quota_ledger) | Inside BFF service layer |
| **Celery Workers** | Execute AI pipeline: vision → prompt assembly → image gen → OSS upload | AI APIs, OSS, PostgreSQL | `python-bff/workers/` |
| **Redis** | Celery broker, result backend, ephemeral cache (config, rate limits) | BFF, Workers | Infrastructure |
| **PostgreSQL** | All persistent state: users, jobs, rules, terms, categories, styles, quota ledger | BFF, Workers | Infrastructure |
| **OSS (Aliyun)** | Image storage: uploaded photos, generated images, watermark variants | BFF (presign), Workers (upload/download) | Infrastructure |
| **Vision API** | Analyze demo images to produce descriptive tags (background, lighting, composition, style) | Workers only | External |
| **Image Gen API** | Generate product promotional images from text+reference | Workers only | External |

### Key Boundary Rules

1. **Frontend never touches AI APIs.** All AI calls go through BFF → Celery worker. API keys exist only server-side.
2. **Prompt assembly is server-side only.** The full prompt is never exposed to the client.
3. **Workers are the only callers of AI APIs.** BFF dispatches; workers execute.
4. **Task snapshots freeze rules at creation time.** Changing rules later does not affect existing jobs.

## Data Flow

### Primary Generation Flow

```
Step 1: Upload (async, before task creation)
  User → POST /api/v1/uploads/presign → BFF generates OSS presigned URL
  User → PUT photo to presigned URL → OSS stores original photo
  User → POST /api/v1/uploads/confirm → BFF records asset in DB

Step 2: Configuration Fetch
  User → GET /categories, /styles, /tags → BFF reads from DB/cache → returns options
  User selects: category + style + tags + demo_image + output_spec (ratio, resolution, watermark)

Step 3: Quota Preview
  User → POST /api/v1/quota/preview → BFF calculates consumption → returns estimate

Step 4: Task Creation (idempotent)
  User → POST /api/v1/jobs/image {client_request_id, category, style, tags, demo_image_id, spec}
  BFF:
    a. Check idempotency (client_request_id unique) → if exists, return existing job_id
    b. Validate combo (category+style+tags legal per rules)
    c. Freeze quota (or just check if plan B)
    d. Load rule → build snapshot (rule_version, assembled_prompt template, resolved terms)
    e. Create generation_job row (status=queued, snapshot embedded)
    f. Dispatch Celery task → Redis queue
    g. Return {job_id, status: "queued"}

Step 5: Async Execution (Celery Worker)
  Worker picks up task:
    a. Update job status → "running"
    b. Call Vision API: analyze demo image → get structured tags (JSON)
    c. Prompt Assembler: merge rule_snapshot + vision_tags + user selections → final prompt
    d. Call Image Gen API: send prompt + reference image → get generated image
    e. Upload result to OSS: raw image + watermarked variant
    f. Update job: status="succeeded", result URLs, vision_tags, final_prompt
    g. Confirm quota deduction (append ledger entry)
    On failure:
    - Update job: status="failed", error_code, error_detail
    - Release frozen quota (if plan A)

Step 6: Result Retrieval (polling)
  User → GET /api/v1/jobs/{id} → BFF returns status + result URLs (presigned)
  Frontend polls with exponential backoff (suggested: 2s → 4s → 8s → max 30s)
  On success: display preview, enable download/save-to-album
```

### Task State Machine

```
                    ┌──────────┐
         create ──→ │  queued  │
                    └────┬─────┘
                         │ worker picks up
                         ▼
                    ┌──────────┐
                    │ running  │
                    └────┬─────┘
                   ╱     │      ╲
            success   timeout   error
               ╱         │        ╲
              ▼          ▼         ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │succeeded │ │  failed  │ │  failed  │
        └──────────┘ └──────────┘ └──────────┘

  Additionally: queued → cancelled (user or admin action before worker starts)
```

**State transitions stored in `generation_job_event` table** for audit trail.

### Admin Config Flow

```
Admin → CRUD categories/styles/terms/rules/pricing → PostgreSQL
       → Changes take effect for NEW jobs only
       → Existing jobs use frozen snapshot from creation time
```

## Patterns to Follow

### Pattern 1: Provider Abstraction (Strategy Pattern)

**What:** Abstract AI API calls behind interfaces so providers are switchable without touching business logic.

**When:** Any external AI API call (Vision or Image Generation).

**Why:** The spec requires multi-model support (GPT-4o-mini for vision, Codex/Gemini for image gen). A clean abstraction makes adding new providers a config change, not a refactor.

```python
# python-bff/app/providers/vision/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class VisionResult:
    tags: dict          # structured description tags
    raw_response: str   # for debugging
    model: str          # which model was used
    tokens_used: int    # for cost tracking

class IVisionProvider(ABC):
    @abstractmethod
    async def analyze_image(self, image_url: str, prompt: str) -> VisionResult:
        """Analyze an image and return descriptive tags."""
        ...

# python-bff/app/providers/vision/openai_gpt4o_mini.py
class GPT4oMiniVisionProvider(IVisionProvider):
    async def analyze_image(self, image_url: str, prompt: str) -> VisionResult:
        # call OpenAI API with vision capability
        ...

# python-bff/app/providers/image_gen/base.py
@dataclass
class ImageGenResult:
    image_url: str      # URL of generated image
    model: str
    tokens_used: int

class IImageGenProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str, reference_image_url: str, params: dict) -> ImageGenResult:
        """Generate an image from prompt + reference."""
        ...

# Provider registry (config-driven)
PROVIDERS = {
    "vision": {
        "gpt4o-mini": GPT4oMiniVisionProvider,
        "gemini": GeminiVisionProvider,
    },
    "image_gen": {
        "codex": CodexImageGenProvider,
        "gemini": GeminiImageGenProvider,
    }
}

def get_vision_provider(name: str = None) -> IVisionProvider:
    name = name or settings.DEFAULT_VISION_PROVIDER
    return PROVIDERS["vision"][name]()
```

### Pattern 2: Task Snapshot Immutability

**What:** When a job is created, embed a frozen copy of all rule/version data into the job row itself.

**When:** Every job creation.

**Why:** The spec explicitly requires that changing rules does not affect existing jobs. This is critical for billing correctness and reproducibility.

```python
# At job creation time:
snapshot = {
    "rule_version": rule.version,
    "prompt_template": rule.prompt_template,
    "resolved_terms": [term.to_dict() for term in resolved_terms],
    "output_spec": {"ratio": "3:4", "resolution": "1024x1024", "watermark": True},
    "providers": {"vision": "gpt4o-mini", "image_gen": "codex"},
}
job = GenerationJob(
    client_request_id=client_request_id,
    tenant_id=tenant_id,
    rule_snapshot=snapshot,  # JSONB column, immutable after creation
    status="queued",
    ...
)
```

### Pattern 3: Celery Task with Retry + Timeout

**What:** Celery task that handles AI API flakiness with bounded retries and hard timeout.

**When:** Every AI API call in the worker pipeline.

```python
# python-bff/app/workers/generate_image.py
from celery import Task
from celery.exceptions import SoftTimeLimitExceeded

class GenerateImageTask(Task):
    autoretry_for = (TimeoutError, ConnectionError, RateLimitError)
    max_retries = 3
    retry_backoff = True        # exponential backoff
    retry_backoff_max = 60      # cap at 60s
    retry_jitter = True
    soft_time_limit = 120       # 2 min soft limit
    time_limit = 180            # 3 min hard limit

@app.task(base=GenerateImageTask, bind=True)
def generate_image_task(self, job_id: str):
    job = db.get_job(job_id)
    job.update_status("running")
    try:
        # Step 1: Vision
        vision_result = get_vision_provider().analyze_image(
            job.demo_image_url, job.rule_snapshot["prompt_template"]
        )
        # Step 2: Prompt assembly
        final_prompt = assemble_prompt(job.rule_snapshot, vision_result.tags)
        # Step 3: Image generation
        gen_result = get_image_gen_provider().generate(
            prompt=final_prompt,
            reference_image_url=job.original_image_url,
            params=job.rule_snapshot["output_spec"]
        )
        # Step 4: Upload to OSS
        raw_url, watermarked_url = upload_results(gen_result.image_url, job)
        # Step 5: Success
        job.update_status("succeeded", result_urls={...})
        confirm_quota_deduction(job)
    except SoftTimeLimitExceeded:
        job.update_status("failed", error_code="TASK_TIMEOUT")
        release_quota(job)
    except Exception as exc:
        job.update_status("failed", error_code="PROVIDER_ERROR", detail=str(exc))
        release_quota(job)
        raise  # let Celery retry if applicable
```

### Pattern 4: Idempotent Task Creation

**What:** Same `client_request_id` always returns the same job, never creates a duplicate or double-charges.

**When:** Every POST /api/v1/jobs/image request.

```python
@app.post("/api/v1/jobs/image")
async def create_job(req: CreateJobRequest, user: User = Depends(get_user)):
    # Idempotency check
    existing = db.find_job_by_client_request_id(req.client_request_id, user.tenant_id)
    if existing:
        return JobResponse(job_id=existing.id, status=existing.status)  # 200, not 201

    # ... validate, freeze quota, create job, enqueue ...
```

### Pattern 5: Presigned URL Upload Flow

**What:** Client uploads directly to OSS via presigned URL, not through BFF (avoids BFF memory/bandwidth bottleneck).

**When:** Every image upload (user photos, potentially admin template uploads).

```python
@app.post("/api/v1/uploads/presign")
async def get_upload_url(req: PresignRequest, user: User = Depends(get_user)):
    key = f"uploads/{user.tenant_id}/{uuid4()}.{req.extension}"
    url = oss_client.generate_presigned_url(
        "put_object",
        Params={"Bucket": BUCKET, "Key": key},
        ExpiresIn=300  # 5 min
    )
    return {"upload_url": url, "key": key}

@app.post("/api/v1/uploads/confirm")
async def confirm_upload(req: ConfirmUploadRequest, user: User = Depends(get_user)):
    # Verify object exists in OSS, create asset record
    asset = db.create_asset(tenant_id=user.tenant_id, oss_key=req.key, ...)
    return {"asset_id": asset.id}
```

### Pattern 6: Rule-Based Prompt Assembly Engine

**What:** Deterministic prompt construction from rule definitions + resolved terms + vision tags. Pure function, no external calls.

**When:** Used in BFF at task creation (for snapshot) and in worker (final assembly with vision tags).

```python
# python-bff/app/services/prompt_assembler.py
def assemble_prompt(
    rule_snapshot: dict,
    vision_tags: dict | None = None,
    user_selections: dict | None = None,
) -> str:
    """
    Assemble final prompt from frozen rule snapshot + live vision tags.
    Deterministic: same inputs → same output.
    """
    template = rule_snapshot["prompt_template"]
    terms = rule_snapshot["resolved_terms"]
    spec = rule_snapshot["output_spec"]

    # Build slot values from terms (prioritized, scoped)
    slots = {}
    for term in sorted(terms, key=lambda t: t["priority"], reverse=True):
        slot = term["slot"]
        if slot not in slots:  # first wins (highest priority)
            slots[slot] = term["text"]

    # Merge vision tags into slots (override/add)
    if vision_tags:
        slots.update(vision_tags)

    # Fill template
    prompt = template
    for slot_name, value in slots.items():
        prompt = prompt.replace(f"{{{slot_name}}}", value)

    # Append output constraints
    prompt += f"\n\nOutput: {spec['ratio']} ratio, {spec['resolution']} resolution."
    if spec.get("watermark"):
        prompt += " Include watermark placement area."

    return prompt
```

## Anti-Patterns to Avoid

### Anti-Pattern 1: Synchronous AI Calls in BFF Request Handlers

**What:** Calling Vision API or Image Gen API directly inside a FastAPI route handler.

**Why bad:** AI APIs take 10s+ seconds. This blocks the request thread, causes frontend timeouts, and cannot be retried reliably. The spec explicitly requires async task queue.

**Instead:** Always enqueue to Celery. Return job_id immediately. Frontend polls for status.

### Anti-Pattern 2: Storing Prompts in Client

**What:** Letting frontend assemble or send the AI prompt.

**Why bad:** Exposes internal prompt engineering to users, enables prompt injection, and violates the spec constraint "Prompt 仅在服务端组装."

**Instead:** Frontend sends only structured selections (category_code, style_code, tag_ids). Server assembles the full prompt.

### Anti-Pattern 3: Mutable Rule Snapshots on Jobs

**What:** Jobs referencing rule IDs that get updated, so historical jobs see new rule versions.

**Why bad:** Changing a rule retroactively changes what was promised to the user. Billing disputes, broken reproducibility.

**Instead:** Snapshot all rule data into the job at creation time (JSONB column). Rules are versioned; jobs reference snapshots, not live rules.

### Anti-Pattern 4: OSS URLs Without Expiry

**What:** Storing permanent OSS URLs in database and returning them to frontend.

**Why bad:** Security risk — anyone with the URL can access the image forever. Also, if buckets/policies change, links break.

**Instead:** Store OSS keys in DB. Generate presigned URLs on-demand with short TTL (e.g., 1 hour) when serving to frontend.

### Anti-Pattern 5: Single Provider Coupling

**What:** Hardcoding a specific AI API (e.g., only GPT-4o-mini) throughout the codebase.

**Why bad:** Vendor lock-in. If the provider has an outage, price hike, or deprecation, the entire system is affected.

**Instead:** Use the provider abstraction layer. Configure default provider in settings. Each provider implements the same interface.

## Scalability Considerations

| Concern | At 100 users/day | At 10K users/day | At 1M users/day |
|---------|-------------------|-------------------|-------------------|
| **API Calls** | Single Celery worker, 1 queue | Multiple workers, separate queues for vision vs image gen | Worker pool auto-scaling, priority queues, rate limiting per provider |
| **Database** | Single PostgreSQL instance | Read replicas for queries, connection pooling (PgBouncer) | Sharding by tenant_id, separate analytics DB |
| **OSS** | Single bucket | Single bucket, CDN in front (Aliyun CDN) | Multi-region buckets, CDN with aggressive caching |
| **Redis** | Single instance | Redis Sentinel for HA | Redis Cluster |
| **Image Serving** | Direct presigned URLs | CDN + presigned origin URLs | CDN edge cache, on-the-fly watermarking via OSS image processing |
| **Task Queue** | Default Celery concurrency (4) | 10-20 workers, separate queues | Worker pool per provider, circuit breakers per provider |

## Build Order (Dependency Analysis)

The build order is driven by **what depends on what**. Each component needs its dependencies ready before it can be tested.

```
Phase 1: Foundation (no dependencies)
  ├── Database schema + ORM models (PostgreSQL)
  ├── FastAPI project skeleton + config
  └── OSS connection + bucket setup

Phase 2: Data Layer (depends on Phase 1)
  ├── Category/Style/Tag CRUD (admin)
  ├── AI Term CRUD with scoping
  └── Promo Rule CRUD + versioning

Phase 3: Upload Flow (depends on Phase 1)
  ├── Presigned URL generation
  ├── Upload confirm + asset records
  └── Image serving with presigned download URLs

Phase 4: Auth + Tenant (depends on Phase 1)
  ├── WeChat login integration
  ├── User + tenant models
  └── JWT/token auth middleware

Phase 5: Prompt Assembly Engine (depends on Phase 2)
  ├── Rule evaluator (category+style+tag → matching rules)
  ├── Term resolver (scoped, prioritized)
  ├── Slot-based template filling
  └── Unit tests with frozen fixtures

Phase 6: Celery Task Infrastructure (depends on Phase 1)
  ├── Celery + Redis setup
  ├── Base task with retry/timeout
  ├── Job CRUD + state machine transitions
  └── Job event logging

Phase 7: AI Provider Abstraction (depends on Phase 6)
  ├── Vision provider interface + GPT-4o-mini impl
  ├── Image gen provider interface + Codex/Gemini impl
  └── Provider registry + config-driven selection

Phase 8: Full Generation Pipeline (depends on Phase 5, 6, 7)
  ├── Worker: vision → prompt assembly → image gen → OSS upload
  ├── Quota freeze/deduct/release lifecycle
  ├── Job creation endpoint (idempotent, with snapshot)
  └── Job polling endpoint

Phase 9: Quota + Billing (depends on Phase 4, 6)
  ├── Quota account + ledger models
  ├── Plan CRUD
  ├── Freeze/deduct/release logic
  └── Preview (trial calculation) endpoint

Phase 10: Frontend Integration (depends on Phase 3, 4, 8, 9)
  ├── Uni-app: login → wizard → task creation → polling → result
  └── Admin UI: full CRUD + task monitoring

Phase 11: Polish + Hardening (depends on all above)
  ├── Rate limiting
  ├── Error code standardization
  ├── Monitoring + observability
  └── Compliance (watermark, privacy agreement)
```

### Critical Path

```
Phase 1 → Phase 6 → Phase 7 → Phase 8 → Phase 10
                                       ↗
Phase 1 → Phase 2 → Phase 5 ────────
                                       ↘
Phase 1 → Phase 3 ──────────────────→ Phase 10
Phase 1 → Phase 4 → Phase 9 ────────→ Phase 10
```

**Phase 8 (Full Generation Pipeline) is the integration bottleneck.** It depends on the prompt engine, task infrastructure, and AI providers all being ready. Plan for extra integration testing time here.

## Sources

- `商品宣传图-产品与技术规格.md` — authoritative technical spec (v2.0, 2026-05-11)
- `PROJECT.md` — project constraints and confirmed tech stack
- Celery documentation: https://docs.celeryq.dev/
- FastAPI async patterns: https://fastapi.tiangolo.com/
- Aliyun OSS presigned URLs: https://www.alibabacloud.com/help/en/oss/
- HIGH confidence: architecture derived from validated spec + standard patterns for the confirmed stack
