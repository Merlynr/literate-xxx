# Requirements: XX甄选 — AIGC Product Image Generation Platform

**Version:** v1.0
**Created:** 2026-05-12
**Source:** PROJECT.md + research/FEATURES.md + research/ARCHITECTURE.md

---

## Overview

35 v1 requirements across 8 categories. Every requirement maps to exactly one phase.

Categories:
- AUTH (3) — WeChat login, session management, multi-tenant isolation
- DATA (4) — Category, style, term CRUD + user-facing selection APIs
- PROMO (3) — Promo rule CRUD, rule engine, task snapshot immutability
- GEN (9) — Upload flow, Vision API, Image Gen, Celery pipeline, task lifecycle, provider abstraction
- QUOTA (4) — Quota account/lifecycle, pricing plans, cost estimation, quota display
- UX (4) — Wizard flow, task history, save to album, privacy compliance
- ADMIN (3) — Task monitoring, error standardization, job reconciliation
- INFRA (5) — Backend skeleton, Celery/Redis, OSS, WeChat MP scaffold, monitoring

---

## Requirements

### AUTH: Authentication & Tenant

| REQ-ID | Requirement | Priority | Phase |
|--------|-------------|----------|-------|
| AUTH-01 | 微信登录 + JWT 认证 + 租户绑定（首次登录创建 tenant_id） | Must | Phase 2 |
| AUTH-02 | 会话管理：wx.checkSession 检测过期 + 静默重新登录 | Must | Phase 2 |
| AUTH-03 | 多租户数据隔离：所有查询自动注入 tenant_id 过滤 | Must | Phase 2 |

### DATA: Data Layer & Configuration

| REQ-ID | Requirement | Priority | Phase |
|--------|-------------|----------|-------|
| DATA-01 | 商品类目 CRUD（管理端 API + UI：创建、编辑、删除、列表） | Must | Phase 2 |
| DATA-02 | 风格模板 CRUD（管理端 API + UI：含封面图、关联规则版本） | Must | Phase 2 |
| DATA-03 | AI 词条库 CRUD（管理端 API + UI：类型、权重、排序、作用范围） | Must | Phase 2 |
| DATA-04 | 用户端类目与风格选择 API（返回租户范围内的可选项列表） | Must | Phase 2 |

### PROMO: Promotion Rules & Prompt Engine

| REQ-ID | Requirement | Priority | Phase |
|--------|-------------|----------|-------|
| PROMO-01 | 宣传规则 CRUD + 版本管理（管理端：槽位模板、词条选取策略、画幅/水印配置） | Must | Phase 2 |
| PROMO-02 | 规则引擎 + Prompt 槽位组装（服务端纯函数：规则快照 + Vision 标签 → 最终 Prompt） | Must | Phase 3 |
| PROMO-03 | 任务快照不可变性：创建任务时固化规则版本 + 组装后的 Prompt + 词条，后续规则变更不影响已有任务 | Must | Phase 3 |

### GEN: Image Generation Pipeline

| REQ-ID | Requirement | Priority | Phase |
|--------|-------------|----------|-------|
| GEN-01 | 图片上传流程：OSS 预签名 URL + 客户端压缩（≤2048px/80%）+ 上传确认 + 资产记录 | Must | Phase 3 |
| GEN-02 | Vision API 自动分析 Demo 图：GPT-4o-mini 分析参考海报生成结构化描述标签（背景、光影、构图、风格） | Must | Phase 3 |
| GEN-03 | Image Gen API 图片生成：基于 Prompt + 实物参考图生成宣传图 | Must | Phase 3 |
| GEN-04 | 完整 Celery 异步管线：Vision 分析 → Prompt 组装 → Image Gen 出图 → OSS 上传 → DB 更新 | Must | Phase 3 |
| GEN-05 | 任务创建幂等性：client_request_id 唯一约束，重复提交返回同一任务 | Must | Phase 3 |
| GEN-06 | 任务状态轮询 API：前端轮询任务状态（queued → running → succeeded/failed），指数退避 | Must | Phase 3 |
| GEN-07 | 结果交付：预签名下载 URL，同时提供水印图和高清原图两种变体 | Must | Phase 3 |
| GEN-08 | 多 AI 引擎 Provider 抽象层：IVisionProvider / IImageGenProvider 接口 + 配置驱动注册表 | Should | Phase 3 |
| GEN-09 | 水印自动贴合：服务端 Pillow 水印叠加，百分比定位，等比缩放 | Must | Phase 3 |

### QUOTA: Quota & Billing

| REQ-ID | Requirement | Priority | Phase |
|--------|-------------|----------|-------|
| QUOTA-01 | 额度账户 + 流水模型 + 冻结/扣减/释放生命周期（方案 A） | Must | Phase 4 |
| QUOTA-02 | 定价套餐 CRUD（管理端：张数、有效期、适用类目） | Must | Phase 4 |
| QUOTA-03 | 生成前试算 API：返回本次生成预计消耗额度 | Should | Phase 4 |
| QUOTA-04 | 额度展示：用户端首页/我的页面余额展示 + 管理端扣减流水查询 | Must | Phase 4 |

### UX: Frontend & User Experience

| REQ-ID | Requirement | Priority | Phase |
|--------|-------------|----------|-------|
| UX-01 | 完整生成向导流程：登录 → 类目 → 风格 → 上传 → 确认 → 轮询 → 结果 → 保存 | Must | Phase 4 |
| UX-02 | 我的作品：任务历史列表（左图右文、状态徽章、时间戳）+ 下拉刷新 | Must | Phase 4 |
| UX-03 | 保存到相册：wx.authorize 预检查 + 系统设置引导 + 长按保存降级方案 | Must | Phase 4 |
| UX-04 | 隐私协议与用户条款 UI：首次生成前强制勾选，接受状态持久化 | Must | Phase 4 |

### ADMIN: Admin & Operations

| REQ-ID | Requirement | Priority | Phase |
|--------|-------------|----------|-------|
| ADMIN-01 | 生成任务监控与查询（管理端：按状态/日期/类目筛选，失败原因详情） | Must | Phase 5 |
| ADMIN-02 | 错误码标准化：统一错误码体系，前端映射为用户友好中文提示 | Must | Phase 5 |
| ADMIN-03 | 任务对账看门狗：定时扫描超时 running 状态任务并自动标记失败 | Should | Phase 5 |

### INFRA: Infrastructure & DevOps

| REQ-ID | Requirement | Priority | Phase |
|--------|-------------|----------|-------|
| INFRA-01 | 后端基础：FastAPI 骨架 + PostgreSQL Schema + Alembic 迁移 + ORM 模型 + 环境配置 | Must | Phase 1 |
| INFRA-02 | 异步任务基础设施：Redis broker + Celery worker 骨架 + 重试/超时配置 + 健康检查 | Must | Phase 1 |
| INFRA-03 | 对象存储：OSS bucket 配置 + 预签名上传/下载服务 | Must | Phase 1 |
| INFRA-04 | 微信小程序项目脚手架 + 域名白名单注册 + 构建管线（mp-weixin 编译） | Must | Phase 1 |
| INFRA-05 | 监控与可观测性：Sentry 错误追踪 + Celery Flower 任务监控 + 结构化日志 | Should | Phase 5 |

---

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| AUTH-01 | Phase 2 | Pending |
| AUTH-02 | Phase 2 | Pending |
| AUTH-03 | Phase 2 | Pending |
| DATA-01 | Phase 2 | Pending |
| DATA-02 | Phase 2 | Pending |
| DATA-03 | Phase 2 | Pending |
| DATA-04 | Phase 2 | Pending |
| PROMO-01 | Phase 2 | Pending |
| PROMO-02 | Phase 3 | Pending |
| PROMO-03 | Phase 3 | Pending |
| GEN-01 | Phase 3 | Pending |
| GEN-02 | Phase 3 | Pending |
| GEN-03 | Phase 3 | Pending |
| GEN-04 | Phase 3 | Pending |
| GEN-05 | Phase 3 | Pending |
| GEN-06 | Phase 3 | Pending |
| GEN-07 | Phase 3 | Pending |
| GEN-08 | Phase 3 | Pending |
| GEN-09 | Phase 3 | Pending |
| QUOTA-01 | Phase 4 | Pending |
| QUOTA-02 | Phase 4 | Pending |
| QUOTA-03 | Phase 4 | Pending |
| QUOTA-04 | Phase 4 | Pending |
| UX-01 | Phase 4 | Pending |
| UX-02 | Phase 4 | Pending |
| UX-03 | Phase 4 | Pending |
| UX-04 | Phase 4 | Pending |
| ADMIN-01 | Phase 5 | Pending |
| ADMIN-02 | Phase 5 | Pending |
| ADMIN-03 | Phase 5 | Pending |
| INFRA-01 | Phase 1 | Pending |
| INFRA-02 | Phase 1 | Pending |
| INFRA-03 | Phase 1 | Pending |
| INFRA-04 | Phase 1 | Pending |
| INFRA-05 | Phase 5 | Pending |

---
*Total: 35 v1 requirements across 8 categories*
