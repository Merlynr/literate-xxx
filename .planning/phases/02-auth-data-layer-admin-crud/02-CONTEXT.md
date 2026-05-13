# Phase 2: Auth, Data Layer & Admin CRUD - Context

**Gathered:** 2026-05-12
**Status:** Ready for planning

<domain>
## Phase Boundary

认证与数据层阶段：微信登录 + JWT 双 token 认证、租户隔离中间件、用户表、商品类目/风格/词条/宣传规则 CRUD 管理 API（纯 API，不做管理端 Web 页面）、用户端选择 API。

本阶段不做 AI 生成流程、不做额度计费、不做前端向导 UI。

</domain>

<decisions>
## Implementation Decisions

### 认证与会话（AUTH-01, AUTH-02）
- **D-11:** JWT 双 token 策略：access_token 有效期 2 小时，refresh_token 有效期 30 天
- **D-12:** 微信登录流程：wx.login() 拿 code → 后端调微信 code2session 接口换取 openid + session_key → 首次登录创建 User + Tenant → 签发双 token
- **D-13:** 前端 token 刷新：access_token 过期时自动用 refresh_token 静默刷新，refresh_token 也过期则重新登录
- **D-14:** wx.checkSession 检测微信 session 是否过期，过期则调 wx.login 重新获取 code

### 用户与租户（AUTH-01, AUTH-03）
- **D-15:** 独立 User 表：id(openid)/nickname/avatar_url/tenant_id/created_at/updated_at
- **D-16:** 租户隔离：FastAPI 依赖注入中间件自动从 JWT 中提取 tenant_id，注入到 db 查询（不手动过滤）
- **D-17:** 首次微信登录自动创建 Tenant + User（一对一关系，一个用户 = 一个租户）

### 数据模型字段
- **D-18:** Category: id/tenant_id/category_code/name/sort_order/is_active/created_at/updated_at
- **D-19:** Style: id/tenant_id/name/cover_image_url/rule_version/sort_order/is_active/created_at/updated_at
- **D-20:** Term: id/tenant_id/type(positive/negative/prefix/brand)/content/weight/sort_order/scope(JSON)/is_active/created_at/updated_at
- **D-21:** PromoRule: id/tenant_id/name/slot_template(JSON)/term_selection_strategy/aspect_ratio/watermark_config(JSON)/version/is_active/created_at/updated_at

### 管理端
- **D-22:** 管理端只做纯 API，通过 Swagger UI 测试，不做 Web 管理页面（后续 Phase 5 可选补充）
- **D-23:** 管理端 API 需要认证（复用 JWT），但不做 RBAC 权限区分（P1 功能）

### Agent's Discretion
- refresh_token 存储方式（DB or Redis）
- JWT 签名密钥配置（env var）
- 微信 code2session 接口调用方式（httpx）
- Alembic migration 具体内容

</decisions>

<canonical_refs>
## Canonical References

### 技术规格
- `商品宣传图-产品与技术规格.md` — 完整数据模型（§10）、API 草案（§11）、状态机（§9）

### Phase 1 决策（继承）
- `.planning/phases/01-foundation-infrastructure/01-CONTEXT.md` — D-01 ~ D-10

### 项目文档
- `.planning/REQUIREMENTS.md` — AUTH-01~03, DATA-01~04, PROMO-01

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Patterns（Phase 1 已建立）
- `python-bff/app/models/base.py` — TenantModel 基类（id/tenant_id/created_at/updated_at），所有业务模型继承它
- `python-bff/app/core/config.py` — Settings 类，所有配置从 .env 读取
- `python-bff/app/api/deps.py` — get_db 异步依赖注入
- `python-bff/app/services/oss.py` — S3 服务模式
- `wx-fe/src/api/request.ts` — HTTP 请求封装，已支持 Bearer token
- `wx-fe/src/stores/user.ts` — Pinia 用户 store（基础结构，需扩展）

### 目录约定
- 新模型放 `python-bff/app/models/`，继承 TenantModel
- 新路由放 `python-bff/app/api/v1/`
- 新 schema 放 `python-bff/app/schemas/`
- 新 service 放 `python-bff/app/services/`
- Alembic migration 放 `python-bff/migrations/versions/`

</code_context>

<specifics>
## Specific Ideas

- access_token 2h + refresh_token 30d，前端 request.ts 需要拦截 401 并自动刷新
- Term 的 scope 用 JSON 字段（存 category_ids + style_ids 数组），不用关联表
- 管理端 CRUD 全部走 Swagger 测试，不做 Web UI

</specifics>

<deferred>
## Deferred Ideas

- RBAC 权限管理（Phase 1 P1）
- 管理端 Web 页面（Phase 5 可选）
- 微信支付集成

</deferred>

---
*Phase: 02-auth-data-layer-admin-crud*
*Context gathered: 2026-05-12*
