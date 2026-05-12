# Phase 1: Foundation & Infrastructure - Context

**Gathered:** 2026-05-12
**Status:** Ready for planning

<domain>
## Phase Boundary

基础设施搭建阶段：后端 FastAPI 骨架 + MySQL + Celery/Redis + MinIO 对象存储 + Uni-app 微信小程序脚手架。目标是让整个技术栈跑通"健康检查"级别的一轮闭环——BFF 能响应请求、Celery 能处理异步任务、OSS 能上传下载、小程序能在真机上渲染页面。

本阶段不做业务逻辑，不接 AI API，不做认证。

</domain>

<decisions>
## Implementation Decisions

### 后端目录结构（python-bff/）
- **D-01:** 采用按层分目录方案
```
python-bff/
├── api/            # FastAPI 路由（按资源分文件）
├── services/       # 业务逻辑层
├── models/         # SQLAlchemy ORM 模型
├── schemas/        # Pydantic 请求/响应模型
├── core/           # 配置、数据库连接、Redis 连接
├── workers/        # Celery 任务定义
├── providers/      # AI Provider 抽象层（Phase 3 用）
├── migrations/     # Alembic 迁移脚本
└── tests/          # 测试
```

### 本地开发环境
- **D-02:** 本地直接安装 MySQL + Redis，不用 Docker Compose
- **D-03:** Windows 上 Celery 使用 `--pool=threads` 开发
- **D-04:** 生产环境必须是 Linux（Celery 5.x 不支持 Windows）

### 对象存储
- **D-05:** 开发阶段使用本地 MinIO 模拟 S3 兼容存储
- **D-06:** 后端统一用 `boto3` 对接 S3 协议，切换到阿里云/七牛云只需改配置（endpoint + bucket + credentials）
- **D-07:** 存储抽象通过环境变量驱动，不硬编码任何云厂商

### 前端初始化（wx-fe/）
- **D-08:** CLI 创建：`npx degit dcloudio/uni-preset-vue#vite wx-fe`（Vue3 + Vite + TypeScript）
- **D-09:** 状态管理用 Pinia
- **D-10:** 页面结构：首页 / 生成向导 / 我的（TabBar 三页）

### Agent's Discretion
- 具体 Python 依赖版本号（由 planner 根据当前最新版选择）
- Celery 配置参数（soft_time_limit, hard_time_limit, 重试次数等）
- Alembic 初始 migration 内容
- OSS bucket 命名规则

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### 技术规格
- `商品宣传图-产品与技术规格.md` — 完整技术规格，包含 API 草案、数据模型、状态机、架构图
- `.planning/research/STACK.md` — 技术栈详细推荐（库版本、目录结构、安装命令）
- `.planning/research/ARCHITECTURE.md` — 架构组件边界、数据流、构建顺序
- `.planning/research/PITFALLS.md` — 16 个关键陷阱，特别是：
  - #3 Celery + Redis on Windows 问题
  - #1 微信小程序域名白名单
  - #11 Redis SPOF 缓解

### 项目文档
- `.planning/PROJECT.md` — 项目上下文、约束、核心价值
- `.planning/REQUIREMENTS.md` — INFRA-01 ~ INFRA-04 四个需求
- `.planning/research/SUMMARY.md` — 研究综合报告

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `python-bff/` — 空目录，从零搭建
- `wx-fe/` — 空目录，从零搭建

### Established Patterns
- 无已有代码，所有模式从研究阶段推荐方案开始
- S3 协议（boto3）作为存储抽象层，确保后续切换云厂商无代码改动

### Integration Points
- FastAPI BFF 是所有交互的中心：前端 ↔ BFF ↔ 数据库/Redis/MinIO
- Celery Worker 通过 Redis broker 接收任务
- Uni-app 前端通过 HTTP 请求调用 BFF API

</code_context>

<specifics>
## Specific Ideas

- "先用本地 MinIO，后续会用阿里云或者七牛云的" — 存储层必须抽象，不绑定任何厂商
- Windows 本地开发环境（非 Docker），但生产必须 Linux
- Uni-app CLI 创建，Vue3 + Vite + TypeScript

</specifics>

<deferred>
## Deferred Ideas

- Docker Compose 环境 — 后续可作为可选开发方式补充
- 微信小程序域名白名单配置 — 虽然是 Phase 1 的坑点提醒，但实际操作在部署阶段

</deferred>

---

*Phase: 01-foundation-infrastructure*
*Context gathered: 2026-05-12*

