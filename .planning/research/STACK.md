# Technology Stack

**Project:** XX甄选 — AI 商品宣传图生成微信小程序
**Researched:** 2026-05-12
**Overall confidence:** MEDIUM (training data + project specs; no live Context7 verification available)

---

## Recommended Stack

### Frontend — Uni-app 微信小程序

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **Uni-app (Vue3 + Composition API)** | Vue 3.4+, uni-app 3.x | 跨端框架，编译到微信小程序 | PROJECT.md 已确认选型；Vue3 Composition API 比 Options API 更适合复杂状态管理；uni-app 是国内微信小程序生态主流跨端方案，社区成熟 |
| **uv-ui** | latest | UI 组件库（适合电商场景） | DCloud 官方推荐的 uni-app Vue3 组件库；含 Grid、Swiper、Form、Upload 等电商常用组件；与 uni-app 深度集成 |
| **pinia** | 2.x | 状态管理 | Vue3 官方推荐；比 vuex 更轻量、TypeScript 支持好；uni-app Vue3 模式原生支持 |
| **z-paging** | latest | 分页列表（下拉刷新 + 上拉加载） | 任务列表、作品列表场景必备；uni-app 生态中评价最好的分页组件 |

**不要用什么：**
- ❌ uni-app Vue2 模式 — Vue2 已 EOL，新项目不应使用
- ❌ uView UI — 作者已停止维护 Vue3 版本，生态断裂
- ❌ Taro — 本项目已选定 uni-app，Taro 是 React 生态的替代方案，不混用

### Backend — FastAPI BFF

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **FastAPI** | 0.115+ | BFF 后端框架 | PROJECT.md 已确认；async/await 原生支持，处理多个外部 API 调用性能最优；自带 OpenAPI 文档，降低前后端联调成本 |
| **Pydantic v2** | 2.x | 数据校验 & 序列化 | FastAPI 原生依赖；v2 性能比 v1 快 5-50 倍；用于 request/response schema、配置管理 |
| **SQLAlchemy 2.0** | 2.0+ | ORM | Python 生态最成熟的 ORM；2.0 版 async 支持完善；与 FastAPI async 模式契合 |
| **alembic** | latest | 数据库迁移 | SQLAlchemy 标配迁移工具 |
| **uvicorn** | latest | ASGI 服务器 | FastAPI 推荐的 ASGI 服务器，性能优于 gunicorn（对于 async 场景） |
| **python-multipart** | latest | 文件上传支持 | FastAPI 处理 multipart/form-data 所需 |

### Task Queue — Celery + Redis

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **Celery** | 5.4+ | 分布式任务队列 | PROJECT.md 已确认；AI API 调用 10s+ 超时，必须后台异步；支持重试、超时、任务状态追踪 |
| **Redis** | 7.x | Celery broker + result backend + cache | 轻量、高性能；同时承担 broker、result backend、缓存三个角色 |
| **celery-redbeat** | latest | 动态定时任务（可选） | 如后续需要定时清理过期任务等场景 |

**Celery 配置要点（高优先级）：**
- 	ask_acks_late=True — 任务确认延迟到执行完成后，防止 worker 崩溃丢任务
- 	ask_reject_on_worker_lost=True — worker 异常终止时任务重新入队
- 	ask_time_limit=120 — 单任务硬超时 120s（AI API 调用通常 30-60s）
- 	ask_soft_time_limit=90 — 软超时 90s，触发 SoftTimeLimitExceeded 异常
- roker_transport_options={'visibility_timeout': 3600} — Redis broker 可见性超时
- 	ask_default_retry_delay=10 — 默认重试间隔 10s
- 	ask_max_retries=3 — 最大重试 3 次

**不要用什么：**
- ❌ Celery + RabbitMQ — RabbitMQ 功能更强但运维复杂，本项目规模 Redis 足够
- ❌ Dramatiq — 社区小于 Celery，生态不如 Celery 成熟
- ❌ asyncio.Task 替代 Celery — 进程重启会丢失任务，无持久化，不适合生产环境

### Database — MySQL

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **MySQL** | 16+ | 主数据库 | PROJECT.md 已确认；JSONB 字段适合存储 AI 标签/规则快照等半结构化数据；成熟稳定 |
| **aiomysql** | latest | 异步 MySQL 驱动 | 比 psycopg2 异步模式快 3-5 倍；FastAPI async 模式推荐搭配 |
| **SQLAlchemy + aiomysql** | — | 异步 ORM 组合 | SQLAlchemy 2.0 + aiomysql 是 FastAPI 项目的标准异步数据库方案 |

**不要用什么：**
- ❌ MySQL — JSONB 支持不如 MySQL；本项目有大量半结构化数据（Prompt 快照、标签列表、规则版本）
- ❌ MongoDB — 关系型数据（用户、任务、额度流水）用 RDBMS 更合适；MongoDB 在事务和一致性方面不如 MySQL
- ❌ SQLite — 不支持并发写入，不适合生产环境

### Object Storage — OSS

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **阿里云 OSS** | — | 图片存储（实物图、生成图、模板图） | 国内微信小程序生态首选；支持 STS 临时凭证 + presigned URL 直传，降低 BFF 带宽压力 |
| **oss2 (Python SDK)** | latest | 服务端 OSS 操作 | 阿里云官方 Python SDK；生成 presigned URL、管理 bucket、签名上传 |

**OSS 直传模式（推荐）：**
`
前端 → BFF 请求 presigned URL → 前端直传 OSS → 返回 object key → 前端把 key 提交给 BFF
`
优势：图片不经过 BFF 服务器，节省带宽，降低后端压力。

**替代方案：腾讯云 COS** — 如果项目已在腾讯云体系内（微信生态常用），COS 也是可行选择。SDK 模式类似。

### AI API Integration

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **openai** (Python SDK) | 1.50+ | Vision API + Image Gen API 统一调用 | 官方 SDK，封装了重试、流式、错误处理；GPT-4o-mini vision 和 GPT-image/DALL-E 均通过此 SDK 调用 |
| **httpx** | latest | 备用 HTTP 客户端（Gemini API 等） | 非 OpenAI 的 API 通过 httpx async 调用；FastAPI 原生推荐 |

**Vision API（GPT-4o-mini）调用模式：**
`python
from openai import AsyncOpenAI

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

response = await client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": demo_image_url}}
        ]
    }],
    max_tokens=500
)
tags = response.choices[0].message.content
`

**Image Gen API 调用模式：**
- **DALL-E 3**：client.images.generate(model="dall-e-3", prompt=..., size="1024x1024")
- **GPT-image-1**：client.images.edit(model="gpt-image-1", image=..., prompt=...) — 支持图片编辑（更适合"基于实物图生成"场景）
- **Gemini API**：通过 httpx 调用 Google 的 Imagen API

**不要用什么：**
- ❌ langchain — 本项目 AI 调用简单直接（Vision + Image Gen），langchain 引入不必要的抽象层和依赖
- ❌ 自建推理服务 — PROJECT.md 明确"API 驱动型架构，不处理模型权重和推理环境"

### Watermark / Image Processing

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **Pillow** | 10.x | 水印贴合、图片裁剪 | Python 图像处理标准库；Logo/水印叠加是轻量操作，不需要 OpenCV 级别的工具 |
| **Pillow-SIMD** | — | 性能优化（可选） | 如果 Pillow 处理成为瓶颈，可替换为 SIMD 加速版本 |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| **python-jose[cryptography]** | latest | JWT token 签发/验证 | 微信登录后的 session token 管理 |
| **redis[hiredis]** | 5.x | Redis Python 客户端 | hiredis 解析器性能提升 10x |
| **python-dotenv** | latest | 环境变量管理 | 本地开发 .env 文件 |
| **loguru** | latest | 结构化日志 | 比标准 logging 更好用；适合任务状态追踪 |
| **tenacity** | latest | 重试库 | AI API 调用的指数退避重试逻辑 |
| **sentry-sdk[fastapi]** | latest | 错误监控 | 生产环境异常追踪，FastAPI + Celery 双覆盖 |
| **pytest + pytest-asyncio** | latest | 测试框架 | FastAPI async 测试必备 |

---

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| 前端框架 | Uni-app Vue3 | Taro (React) | 项目已选 Uni-app；国内小程序生态 Uni-app 社区更大 |
| 前端框架 | Uni-app Vue3 | 原生微信小程序 | 原生开发效率低，无跨端能力，无 Vue 生态支持 |
| 后端框架 | FastAPI | Django REST | Django 太重；FastAPI async 原生支持更好；本项目是 API-only BFF 不需要 Django admin 等 |
| 后端框架 | FastAPI | Flask | Flask 无原生 async 支持；处理并发外部 API 调用不如 FastAPI |
| 任务队列 | Celery + Redis | Celery + RabbitMQ | Redis 同时做 broker + cache + result backend，减少运维组件 |
| 任务队列 | Celery + Redis | Huey / Dramatiq | 社区小，生产案例少，遇到问题难以排查 |
| 数据库 | MySQL | MySQL | JSONB 支持差；本项目半结构化数据多 |
| 对象存储 | 阿里云 OSS | 腾讯云 COS | 都可行；选 OSS 因为通用性更强，COS 适合全栈腾讯云场景 |
| AI SDK | openai SDK | langchain | 本项目 AI 调用简单直接，不需要 langchain 的抽象 |
| 图像处理 | Pillow | OpenCV | 水印叠加用 Pillow 够了，OpenCV 太重 |

---

## Recommended Directory Structure

`
F:\project\xxx\
├── wx-fe/                          # Uni-app 前端
│   ├── src/
│   │   ├── pages/                  # 页面
│   │   │   ├── index/              # 首页
│   │   │   ├── generate/           # 生成向导（类目→风格→标签→参考图→规格→确认）
│   │   │   ├── result/             # 结果展示
│   │   │   └── my/                 # 我的作品
│   │   ├── components/             # 公共组件
│   │   ├── stores/                 # Pinia stores
│   │   ├── api/                    # API 请求封装
│   │   ├── utils/                  # 工具函数
│   │   ├── static/                 # 静态资源
│   │   ├── App.vue
│   │   ├── main.js
│   │   ├── manifest.json
│   │   ├── pages.json
│   │   └── uni.scss
│   ├── package.json
│   └── vite.config.js
│
├── python-bff/                     # FastAPI BFF 后端
│   ├── app/
│   │   ├── main.py                 # FastAPI app 入口
│   │   ├── api/                    # 路由
│   │   │   ├── v1/
│   │   │   │   ├── categories.py
│   │   │   │   ├── styles.py
│   │   │   │   ├── uploads.py
│   │   │   │   ├── jobs.py
│   │   │   │   └── quota.py
│   │   │   └── deps.py             # 依赖注入
│   │   ├── models/                 # SQLAlchemy models
│   │   ├── schemas/                # Pydantic schemas
│   │   ├── services/               # 业务逻辑
│   │   │   ├── ai_vision.py        # Vision API 调用
│   │   │   ├── ai_image_gen.py     # Image Gen API 调用
│   │   │   ├── rule_engine.py      # 规则引擎 & Prompt 组装
│   │   │   ├── quota.py            # 额度管理
│   │   │   └── oss.py              # OSS 操作
│   │   ├── tasks/                  # Celery tasks
│   │   │   ├── __init__.py
│   │   │   └── generation.py       # 图片生成任务
│   │   ├── core/                   # 核心配置
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   └── celery_app.py
│   │   └── db/                     # 数据库连接
│   │       ├── session.py
│   │       └── base.py
│   ├── alembic/                    # 数据库迁移
│   ├── tests/
│   ├── requirements.txt
│   ├── pyproject.toml
│   └── Dockerfile
│
└── .planning/                      # 项目规划
`

---

## Installation

### Frontend (wx-fe/)
`ash
cd wx-fe
npx degit dcloudio/uni-preset-vue#vite-ts .   # Vue3 + Vite + TypeScript 模板
npm install
npm install pinia uv-ui z-paging
npm install -D @types/node sass
`

### Backend (python-bff/)
`ash
cd python-bff
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install fastapi uvicorn[standard] sqlalchemy[asyncio] aiomysql alembic
pip install celery[redis] redis[hiredis]
pip install oss2 openai httpx
pip install python-jose[cryptography] python-multipart python-dotenv
pip install pillow loguru tenacity
pip install -D pytest pytest-asyncio httpx
`

### Redis (development)
`ash
# Docker (推荐)
docker run -d --name redis-dev -p 6379:6379 redis:7-alpine

# 或 Windows: 使用 Memurai 或 WSL2
`

### MySQL (development)
`ash
# Docker (推荐)
docker run -d --name pg-dev -p 5432:5432 -e POSTGRES_PASSWORD=dev -e POSTGRES_DB=xxzx postgres:16-alpine
`

---

## Key Technical Decisions & Rationale

### 1. 为什么用 Celery 而不是 FastAPI BackgroundTasks？
FastAPI 的 BackgroundTasks 在进程内执行，进程重启会丢失任务。AI API 调用耗时 10s+，需要：
- ✅ 任务持久化（Redis broker）
- ✅ 自动重试（指数退避）
- ✅ 超时控制（soft/hard limit）
- ✅ 状态追踪（queued/running/succeeded/failed）
- ✅ 并发控制（worker 并发数配置）

Celery 完整覆盖这些需求。

### 2. 为什么用 OSS presigned URL 直传？
小程序用户上传图片时：
- ❌ 经过 BFF 上传：BFF 成为带宽瓶颈，增加延迟
- ✅ presigned URL 直传：前端 → OSS，BFF 只做签名，带宽零压力

### 3. 为什么同时支持 DALL-E 和 GPT-image-1？
- **DALL-E 3**：纯文生图，质量高，适合从零生成
- **GPT-image-1**：支持图片编辑（image-to-image），更适合"基于实物图 + 参考风格生成"的业务场景
- PROJECT.md 说"Codex / Gemini API"，实际对应 OpenAI 的 image gen 系列和 Google 的 Imagen

### 4. 为什么 SQLAlchemy 而不是直接用 aiomysql？
直接用 aiomysql 写 SQL 太原始，SQLAlchemy 2.0 的 async 模式：
- 提供 ORM 和 migration 工具链
- 类型提示完善
- 复杂查询（任务过滤、额度统计）写起来更简洁

---

## Sources

- PROJECT.md — 项目已确认的技术栈选型
- 商品宣传图-产品与技术规格.md — 详细技术规格
- AI_IMAGE_PIPELINE_CLARIFICATION.md — AI 流程说明
- Confidence: HIGH for "已确认选型"（来自项目文档），MEDIUM for 具体版本号和库推荐（基于训练数据，需验证最新版本）


