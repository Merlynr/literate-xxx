# Phase 1: Foundation & Infrastructure - Research

**Researched:** 2026-05-12
**Domain:** FastAPI scaffolding, PostgreSQL + Alembic, Celery + Redis, S3-compatible storage (MinIO), Uni-app WeChat Mini Program
**Confidence:** MEDIUM-HIGH

## Summary

Phase 1 establishes the full technical backbone for XX甄选 — a WeChat Mini Program AIGC product image generation platform. The backend is a FastAPI BFF with PostgreSQL (via SQLAlchemy 2.0 async + asyncpg), Celery + Redis for async task processing, and MinIO for S3-compatible object storage. The frontend is a Uni-app Vue3+TypeScript project targeting mp-weixin. This phase delivers infrastructure-only: health checks, presigned URL scaffolding, Celery worker skeleton, and a functional Mini Program shell — no business logic.

Both `python-bff/` and `wx-fe/` directories exist but are empty. The environment has Python 3.10, Node.js, npm, but **no PostgreSQL, Redis, MinIO, or Docker installed** — these must be installed as part of Phase 1 planning. `uv` is not available; use `pip` for dependency management.

**Primary recommendation:** Scaffold `python-bff/` using an app-factory pattern with `pyproject.toml` (not `requirements.txt`), install PostgreSQL 16 + Redis 7 + MinIO via Windows installers or Chocolatey, and create the Uni-app project via `npx degit dcloudio/uni-preset-vue#vite-ts wx-fe`.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** 按层分目录 (api/, services/, models/, schemas/, core/, workers/, providers/)
- **D-02:** 本地直接安装 PostgreSQL + Redis，不用 Docker Compose
- **D-03:** Windows 上 Celery 使用 `--pool=threads` 开发
- **D-04:** 生产环境必须是 Linux（Celery 5.x 不支持 Windows）
- **D-05:** 开发阶段使用本地 MinIO 模拟 S3 兼容存储
- **D-06:** 后端统一用 `boto3` 对接 S3 协议
- **D-07:** 存储抽象通过环境变量驱动，不硬编码任何云厂商
- **D-08:** CLI 创建 Uni-app: `npx degit dcloudio/uni-preset-vue#vite wx-fe`（Vue3 + Vite + TypeScript）
- **D-09:** 状态管理用 Pinia
- **D-10:** 页面结构：首页 / 生成向导 / 我的（TabBar 三页）

### Claude's Discretion
- 具体 Python 依赖版本号（由 planner 根据当前最新版选择）
- Celery 配置参数（soft_time_limit, hard_time_limit, 重试次数等）
- Alembic 初始 migration 内容
- OSS bucket 命名规则

### Deferred Ideas (OUT OF SCOPE)
- Docker Compose 环境 — 后续可作为可选开发方式补充
- 微信小程序域名白名单配置 — 虽然是 Phase 1 的坑点提醒，但实际操作在部署阶段
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| INFRA-01 | 后端基础：FastAPI 骨架 + PostgreSQL Schema + Alembic 迁移 + ORM 模型 + 环境配置 | Standard Stack → FastAPI + SQLAlchemy 2.0 + asyncpg + Alembic + pydantic-settings; Architecture → app factory, async session, layer-based structure |
| INFRA-02 | 异步任务基础设施：Redis broker + Celery worker 骨架 + 重试/超时配置 + 健康检查 | Standard Stack → Celery + Redis; Architecture → Celery app factory, task base class with retry/timeout, health check endpoint |
| INFRA-03 | 对象存储：OSS bucket 配置 + 预签名上传/下载服务 | Standard Stack → boto3 + MinIO; Architecture → presigned URL generation, S3 abstraction layer |
| INFRA-04 | 微信小程序项目脚手架 + 域名白名单注册 + 构建管线（mp-weixin 编译） | Standard Stack → Uni-app Vue3+Vite+TS+Pinia; Architecture → TabBar pages, build pipeline |
</phase_requirements>

## Standard Stack

### Core — Backend (python-bff/)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| **FastAPI** | 0.136.1 | BFF web framework | [VERIFIED: PyPI 2026-05-12] Async-native, auto OpenAPI docs |
| **SQLAlchemy** | 2.0.49 | ORM | [VERIFIED: PyPI 2026-05-12] 2.0 async mode with asyncpg driver |
| **asyncpg** | 0.31.0 | PostgreSQL async driver | [VERIFIED: PyPI 2026-05-12] 3-5x faster than psycopg2 for async |
| **Alembic** | 1.18.4 | DB migrations | [VERIFIED: PyPI 2026-05-12] SQLAlchemy-standard migration tool |
| **pydantic-settings** | 2.14.1 | Env config management | [VERIFIED: PyPI 2026-05-12] Pydantic v2 native Settings for .env |
| **uvicorn** | 0.46.0 | ASGI server | [VERIFIED: PyPI 2026-05-12] FastAPI-recommended ASGI server |
| **Celery** | 5.6.3 | Async task queue | [VERIFIED: PyPI 2026-05-12] Industry standard Python task queues |
| **redis** | 7.4.0 | Redis client | [VERIFIED: PyPI 2026-05-12] redis[hiredis] for 10x parse perf |
| **boto3** | 1.43.6 | S3-compatible storage client | [VERIFIED: PyPI 2026-05-12] Works with MinIO/Aliyun/Qiniu via S3 |
| **python-multipart** | 0.0.28 | File upload support | [VERIFIED: PyPI 2026-05-12] Required by FastAPI for UploadFile |
| **Pillow** | 12.2.0 | Image processing | [VERIFIED: PyPI 2026-05-12] Watermark overlay, image validation |
| **loguru** | 0.7.3 | Structured logging | [VERIFIED: PyPI 2026-05-12] Better DX than stdlib logging |
| **tenacity** | 9.1.4 | Retry library | [VERIFIED: PyPI 2026-05-12] Exponential backoff for API calls |
| **httpx** | 0.28.1 | Async HTTP client | [VERIFIED: PyPI 2026-05-12] For non-OpenAI API calls |

### Core — Dev/Test

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| **pytest** | latest | Test framework | All tests |
| **pytest-asyncio** | latest | Async test support | FastAPI endpoint tests |

### Core — Frontend (wx-fe/)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| **Uni-app** (Vue3+Vite+TS) | latest template | Cross-platform → mp-weixin | [VERIFIED: npm] degit 2.8.4 available |
| **Pinia** | 3.0.4 | State management | [VERIFIED: npm 2026-05-12] Vue3 official recommendation |

### Installation — Backend

```bash
cd python-bff
python -m venv .venv
.venv\Scripts\activate
pip install "fastapi>=0.136,<0.137" "uvicorn[standard]>=0.46,<0.47" python-multipart
pip install "sqlalchemy[asyncio]>=2.0.49,<2.1" asyncpg alembic
pip install "pydantic-settings>=2.14,<2.15"
pip install "celery[redis]>=5.6,<5.7" "redis>=7.4,<7.5"
pip install boto3 pillow loguru tenacity httpx python-jose[cryptography]
pip install -D pytest pytest-asyncio
```

**Note:** `uv` is not installed. Use `pip`. Consider installing `uv` for faster deps in future.

### Installation — Frontend

```bash
cd wx-fe
npx degit dcloudio/uni-preset-vue#vite-ts .
npm install
npm install pinia
npm install -D @types/node
```

**Caution:** If `degit` fails, fallback is to clone `https://github.com/dcloudio/uni-preset-vue` and checkout `vite-ts` branch.

### Installation — Infrastructure (D-02: local install, no Docker)

| Service | Windows Install Method | Default Port |
|---------|----------------------|--------------|
| **PostgreSQL 16** | [EnterpriseDB installer](https://www.enterprisedb.com/downloads/postgres-postgresql-downloads) or `choco install postgresql16` | 5432 |
| **Redis 7** | [Memurai](https://www.memurai.com/) or `choco install redis-64` or WSL2 | 6379 |
| **MinIO** | [MinIO binary](https://min.io/download) → `minio.exe server ./data` | 9000 (API), 9001 (Console) |

## Architecture Patterns

### Recommended Project Structure

```text
python-bff/
├── pyproject.toml              # Project metadata + deps
├── alembic.ini                 # Alembic config
├── alembic/
│   ├── env.py                  # Alembic env (async mode)
│   └── versions/               # Migration scripts
├── app/
│   ├── __init__.py
│   ├── main.py                 # App factory: create_app()
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py             # Shared deps (get_db)
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── health.py       # Health check endpoints
│   │   │   ├── uploads.py      # Presigned URL endpoints
│   │   │   └── router.py       # v1 router aggregation
│   │   └── router.py           # Root API router
│   ├── models/
│   │   ├── __init__.py
│   │   └── base.py             # Base model (id, created_at, updated_at)
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── health.py
│   ├── services/
│   │   ├── __init__.py
│   │   └── oss.py              # S3/OSS presigned URL service
│   ├── workers/
│   │   ├── __init__.py
│   │   └── celery_app.py       # Celery app factory
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py           # pydantic-settings Settings
│   │   ├── database.py         # Async SQLAlchemy engine + session
│   │   └── redis_client.py     # Redis connection pool
│   └── providers/
│       └── __init__.py          # Placeholder for Phase 3
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_health.py
│   └── test_oss.py
├── .env.example
└── Dockerfile
```

```text
wx-fe/
├── src/
│   ├── pages/
│   │   ├── index/index.vue     # 首页 Tab
│   │   ├── generate/index.vue  # 生成向导 Tab
│   │   └── my/index.vue        # 我的 Tab
│   ├── stores/index.ts         # Pinia store setup
│   ├── api/request.ts          # HTTP request wrapper
│   ├── static/
│   ├── App.vue
│   ├── main.ts
│   ├── manifest.json
│   ├── pages.json              # TabBar + page routes
│   └── uni.scss
├── package.json
├── tsconfig.json
└── vite.config.ts
```

### Pattern 1: App Factory (create_app)

**What:** FastAPI application created via a factory function, not module-level global.
**When:** Always — enables multiple instances for testing.
**Example:**

```python
# app/main.py
from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.database import engine
from app.api.router import api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: verify DB, Redis, MinIO connections
    yield
    # Shutdown: dispose engine, close Redis pool
    await engine.dispose()

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        lifespan=lifespan,
    )
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)
    return app

app = create_app()
```

### Pattern 2: Async Database Session (SQLAlchemy 2.0)

**What:** AsyncSession dependency injected via Depends().
**When:** Every database operation.

```python
# app/core/database.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)

# app/api/deps.py
from typing import AsyncGenerator
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

**Critical:** Must use `create_async_engine` with `postgresql+asyncpg://` driver. Sync driver blocks event loop.

### Pattern 3: pydantic-settings Configuration

**What:** Single Settings class loads from .env + environment variables.

```python
# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)
    PROJECT_NAME: str = "XX甄选 BFF"
    VERSION: str = "0.1.0"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = False
    DATABASE_URL: str  # postgresql+asyncpg://user:pass@localhost:5432/xxzx
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    S3_ENDPOINT: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_BUCKET: str = "xxzx-assets"
    S3_REGION: str = ""
    S3_USE_SSL: bool = False

settings = Settings()
```

**Key insight (D-07):** `S3_*` naming means switching MinIO to Aliyun OSS only requires .env changes — zero code changes. boto3 S3 protocol works with all S3-compatible storage.

### Pattern 4: Celery App Factory

```python
# app/workers/celery_app.py
from celery import Celery
from app.core.config import settings

celery_app = Celery("xxzx_worker", broker=settings.CELERY_BROKER_URL, backend=settings.CELERY_RESULT_BACKEND)
celery_app.conf.update(
    task_serializer="json", accept_content=["json"], result_serializer="json",
    timezone="Asia/Shanghai", enable_utc=False,
    task_track_started=True, task_acks_late=True, task_reject_on_worker_lost=True,
    task_soft_time_limit=90, task_time_limit=120,
    task_default_retry_delay=10, task_max_retries=3,
    broker_transport_options={"visibility_timeout": 3600},
    worker_prefetch_multiplier=1,
)
celery_app.autodiscover_tasks(["app.workers"])
```

**Windows (D-03):** `celery -A app.workers.celery_app worker --pool=threads --concurrency=4 -l info`

### Pattern 5: Health Check Endpoints

```python
# app/api/v1/health.py
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis
from app.api.deps import get_db
from app.core.config import settings

router = APIRouter()

@router.get("/health/liveness")
async def liveness():
    return {"status": "ok"}

@router.get("/health/readiness")
async def readiness(db: AsyncSession = Depends(get_db)):
    checks = {}
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {e}"
    try:
        r = aioredis.from_url(settings.REDIS_URL)
        await r.ping()
        checks["redis"] = "ok"
        await r.close()
    except Exception as e:
        checks["redis"] = f"error: {e}"
    all_ok = all(v == "ok" for v in checks.values())
    return {"status": "ok" if all_ok else "degraded", "checks": checks}
```

### Pattern 6: Presigned URL Service (boto3 + MinIO)

```python
# app/services/oss.py
import boto3
from botocore.config import Config
from app.core.config import settings

def get_s3_client():
    return boto3.client("s3",
        endpoint_url=settings.S3_ENDPOINT,
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY,
        region_name=settings.S3_REGION or None,
        config=Config(signature_version="s3v4"),
    )

def generate_presigned_upload_url(key: str, content_type: str = "image/jpeg", expires_in: int = 300) -> str:
    return get_s3_client().generate_presigned_url("put_object",
        Params={"Bucket": settings.S3_BUCKET, "Key": key, "ContentType": content_type},
        ExpiresIn=expires_in,
    )

def generate_presigned_download_url(key: str, expires_in: int = 3600) -> str:
    return get_s3_client().generate_presigned_url("get_object",
        Params={"Bucket": settings.S3_BUCKET, "Key": key},
        ExpiresIn=expires_in,
    )
```

**Critical:** Always `signature_version="s3v4"` — MinIO requires V4 signatures.

### Anti-Patterns to Avoid

- **Module-level `app = FastAPI()`**: Use app factory for testability.
- **Sync DB driver (psycopg2)**: Must use asyncpg with create_async_engine.
- **Hardcoded S3 credentials**: All config via Settings → env vars (D-07).
- **requirements.txt**: Use pyproject.toml with pinned versions.
- **`--pool=prefork` on Windows**: Must use `--pool=threads` (D-03).
- **Creating buckets at app startup**: Bucket creation is a setup step, not runtime.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| S3 presigned URLs | Custom HTTP signing | boto3.generate_presigned_url() | V4 signatures, edge cases, URL encoding |
| DB migrations | Manual SQL scripts | Alembic | Schema versioning, rollback, auto-generation |
| Async DB pool | Custom pool | create_async_engine | Battle-tested, connection recycling |
| Environment config | os.getenv() scattered | pydantic-settings.BaseSettings | Type validation, .env support |
| HTTP validation | Manual JSON parsing | Pydantic in FastAPI | Auto validation, OpenAPI schema |
| Celery setup | Bare Celery() inline | Factory with conf.update() | Testable, configurable per env |
| Logging | print() / stdlib logging | loguru | Better formatting, file rotation |

## Common Pitfalls

### Pitfall 1: SQLAlchemy Async URL Must Use postgresql+asyncpg://
**What goes wrong:** Using postgresql:// with create_async_engine raises NoSuchModuleError or silently blocks event loop.
**How to avoid:** Always `postgresql+asyncpg://` prefix. Validate at startup.

### Pitfall 2: Celery Tasks Cannot Be async def
**What goes wrong:** Defining `async def` Celery tasks — Celery does not run coroutines natively.
**How to avoid:** Tasks must be synchronous `def`. Use `asyncio.run()` inside to call async code. For Phase 1 skeleton, simple `def` tasks suffice.

### Pitfall 3: Alembic Async Mode Requires Special env.py
**What goes wrong:** Default env.py uses sync engine. Migrations run but async column types fail.
**How to avoid:** Use `run_async_migrations()` pattern with `async with` connectable. [CITED: alembic.sqlalchemy.org/en/latest/cookbook.html]

### Pitfall 4: MinIO Bucket Must Exist Before Presigned URLs
**What goes wrong:** generate_presigned_url succeeds but actual PUT fails with NoSuchBucket.
**How to avoid:** Create bucket via MinIO Console (localhost:9001) or setup script before testing.

### Pitfall 5: WeChat Template Branch Name
**What goes wrong:** `#vite` lacks TypeScript. Need `#vite-ts`.
**How to avoid:** Use `npx degit dcloudio/uni-preset-vue#vite-ts wx-fe`. If branch missing, fall back to `#vite` + manual TS config.

### Pitfall 6: Python 3.10 Compatibility
**What goes wrong:** Some Python 3.12+ syntax features unavailable.
**How to avoid:** All recommended libs support 3.10+. Use `from __future__ import annotations` if needed.

### Pitfall 7: Redis DB Index Isolation for Celery
**What goes wrong:** Using same Redis DB for Celery broker and app cache — Celery overwrites cached data.
**How to avoid:** Separate DBs: /0 for app cache, /1 for broker, /2 for result backend.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | Backend runtime | ✓ | 3.10.0 | — |
| pip | Package manager | ✓ | 21.2.3 | — |
| Node.js | Frontend build | ✓ | 11.13.0 | ⚠️ May need upgrade to 16+ |
| npm | Frontend packages | ✓ | 20.20.2 | — |
| uv | Fast package mgr | ✗ | — | Use pip |
| PostgreSQL | Database | ✗ | — | Must install |
| Redis | Cache/broker | ✗ | — | Must install |
| MinIO | Object storage | ✗ | — | Must install |
| Docker | Containerization | ✗ | — | Not needed (D-02) |

**Missing dependencies with no fallback:**
- **PostgreSQL** — Must install before backend work. Blocker for INFRA-01.
- **Redis** — Must install before Celery starts. Blocker for INFRA-02.
- **MinIO** — Must install before presigned URL testing. Blocker for INFRA-03.

**Missing dependencies with fallback:**
- **uv** — pip works fine, just slower.

**Node.js version concern:** Version 11.13.0 is very old. Uni-app Vite tooling requires Node.js 16+. **Planner must verify/upgrade before INFRA-04 execution.**

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest + pytest-asyncio (latest) |
| Config file | `python-bff/pyproject.toml` `[tool.pytest.ini_options]` |
| Quick run command | `cd python-bff && python -m pytest tests/ -x -q` |
| Full suite command | `cd python-bff && python -m pytest tests/ -v --tb=short` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| INFRA-01 | FastAPI starts, DB connects, Alembic runs, ORM model importable | integration | `pytest tests/test_health.py::test_readiness -x` | ❌ Wave 0 |
| INFRA-02 | Celery worker starts, ping_task executes, redis=ok in health | integration | `pytest tests/test_health.py::test_celery_ping -x` | ❌ Wave 0 |
| INFRA-03 | Presigned upload URL generated, PUT to MinIO succeeds, download returns file | integration | `pytest tests/test_oss.py::test_presigned_roundtrip -x` | ❌ Wave 0 |
| INFRA-04 | Uni-app compiles to mp-weixin, pages render, TabBar works | manual-only | N/A (requires WeChat DevTools) | — |

### Sampling Rate
- **Per task commit:** `cd python-bff && python -m pytest tests/ -x -q`
- **Per wave merge:** `cd python-bff && python -m pytest tests/ -v --tb=short`
- **Phase gate:** Full suite green + frontend `npm run build:mp-weixin` succeeds

### Wave 0 Gaps
- [ ] `python-bff/tests/conftest.py` — shared fixtures: test DB session, test FastAPI client
- [ ] `python-bff/tests/test_health.py` — liveness + readiness endpoint tests
- [ ] `python-bff/tests/test_oss.py` — presigned URL generation + round-trip test
- [ ] `python-bff/pyproject.toml` `[tool.pytest.ini_options]` — asyncio_mode = "auto"
- [ ] pytest + pytest-asyncio installation in dev dependencies

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| requirements.txt | pyproject.toml (PEP 621) | ~2023 | Single source of truth, supports tool configs |
| psycopg2 (sync) | asyncpg (async) | SQLAlchemy 2.0 (2023) | Non-blocking DB in async frameworks |
| Celery() global import | Factory with conf.update() | Best practice evolution | Testable, configurable per env |
| os.getenv() | pydantic-settings.BaseSettings | Pydantic v2 (2023) | Type safety, validation, .env auto-load |
| oss2 (Aliyun SDK) | boto3 (S3 protocol) | 2025+ ecosystem | Vendor-agnostic, MinIO/AWS/Qiniu compatible |
| Vuex | Pinia | Vue3 era (2022+) | Better TypeScript, simpler API |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `dcloudio/uni-preset-vue#vite-ts` branch exists | Standard Stack — Frontend | If missing, need manual TS setup after #vite clone |
| A2 | Python 3.10.0 compatible with all recommended libs | Standard Stack | All verified versions support 3.10+ |
| A3 | Node.js 11.13.0 is sufficient for Uni-app Vite | Environment | Likely INSUFFICIENT — Vite requires Node 16+ |
| A4 | PostgreSQL 16 available via Chocolatey or direct download | Environment | Chocolatey may not be installed; direct download works |
| A5 | Redis for Windows available as Memurai or redis-64 | Environment | Memurai free tier works for dev |
| A6 | MinIO binary runs standalone on Windows without Docker | Environment | Official docs confirm Windows binary available |

## Open Questions

1. **Node.js version sufficiency**
   - What we know: Node.js 11.13.0 installed, npm 20.20.2 is very new
   - What's unclear: Uni-app Vite template works with Node 11 (unlikely — Vite requires 16+)
   - Recommendation: Upgrade Node.js to 18 LTS or 20 LTS before frontend work.

2. **PostgreSQL/Redis/MinIO installation approach**
   - What we know: D-02 says local install, no Docker. None currently installed.
   - What's unclear: Whether Chocolatey is available, user preference for GUI vs CLI installers
   - Recommendation: Include installation steps with multiple methods (Chocolatey if available, direct download fallback).

3. **Alembic initial migration content**
   - What we know: INFRA-01 requires ORM models but no specific tables defined in Phase 1
   - What's unclear: Which tables to create initially
   - Recommendation: Minimal initial migration with base Alembic version table. Real tables added in later phases.

4. **OSS bucket naming convention**
   - What we know: D-07 says env-driven, D-05 says local MinIO
   - What's unclear: Bucket name convention
   - Recommendation: Use `xxzx-assets` as default in .env.example.

## Sources

### Primary (HIGH confidence)
- PyPI package registry — All version numbers verified 2026-05-12 via pypi.org/pypi/{package}/json
- CONTEXT.md — Locked decisions D-01 through D-10
- REQUIREMENTS.md — INFRA-01 through INFRA-04
- ARCHITECTURE.md — Component boundaries, data flow, build order
- PITFALLS.md — 16 documented pitfalls

### Secondary (MEDIUM confidence)
- STACK.md — Technology recommendations (cross-verified with PyPI)
- [CITED: fastapi.tiangolo.com] — App factory, lifespan, async sessions
- [CITED: docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html] — Async patterns
- [CITED: alembic.sqlalchemy.org/en/latest/cookbook.html] — Async migrations
- [CITED: docs.celeryq.dev/en/stable/userguide/configuration.html] — Celery config
- [CITED: boto3.amazonaws.com/v1/documentation/api/latest/guide/s3-presigned-urls.html] — Presigned URLs

### Tertiary (LOW confidence)
- [ASSUMED] Uni-app #vite-ts branch existence — template repos change
- [ASSUMED] Node.js 11 compatibility with Vite — based on Vite docs

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — All versions verified against PyPI on 2026-05-12
- Architecture: HIGH — Patterns from official docs + validated project spec
- Pitfalls: HIGH — Cross-referenced with ARCHITECTURE.md, PITFALLS.md, official docs
- Environment: MEDIUM — Runtime probing done, Node.js version concern unresolved

**Research date:** 2026-05-12
**Valid until:** 2026-06-12 (30 days — stable stack)

