# XX甄选

## What This Is

XX甄选 是一个微信小程序电商项目，核心卖点是 AI 生成商品宣传图。用户上传一张实物照片，选择风格模板，系统自动通过 Vision API 分析 Demo 图生成描述性标签，再调用 Image Gen API 生成可直接上架的商品宣传图。目前产品线聚焦光伏板下种植的优质农产品（红皮土豆、黑珍珠土豆）。

## Core Value

用 AI 将一张普通实物照片，自动转化为可直接挂在商品页的成品级宣传图，替代传统美工/摄影流程。

## Architecture

**API 驱动型架构** — 后端是中转与任务调度中心，不处理模型权重和推理环境。

### 核心流程
1. 用户上传实物图 → 存储到 OSS
2. 选择风格模板 / Demo 图 + 标签
3. Vision API（默认 GPT-4o-mini，可切换多模型）分析 Demo 图，生成描述性标签（背景、光影、构图、风格等）
4. Image Gen API 结合实物图 + 视觉描述 + 控制参数，生成宣传图
5. 结果图存储到 OSS，水印/Logo 自动贴合，返回给前端展示

### 技术栈（已确认）
| 层次 | 选型 | 说明 |
|------|------|------|
| 前端 | **Uni-app** | 跨端框架，编译到微信小程序 |
| 后端框架 | **FastAPI** | 纯异步，处理多个 API 回调性能最优 |
| 异步队列 | **Celery + Redis** | API 调用 10s+，必须后台异步执行 |
| Vision API | **GPT-4o-mini**（默认，可切换） | 学习 Demo 图，生成描述性标签 |
| Image Gen API | **Codex / Gemini API**（图片预处理暂不做） | 核心出图引擎 |
| 数据库 | **PostgreSQL** | 存储任务状态、配置、用户数据 |
| 缓存/队列 | **Redis** | 任务队列 broker、缓存、会话 |
| 对象存储 | **OSS** | 实物图、生成图、模板图存储 |

### 项目结构
```
F:\project\xxx/
├── wx-fe/          # Uni-app 前端（编译到微信小程序）
├── python-bff/     # FastAPI BFF 后端
└── .planning/      # 项目规划文档
```

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] 用户上传实物照片（相册/拍照），图片存储到 OSS
- [ ] 选择商品类目（红皮土豆、黑珍珠土豆等）
- [ ] 选择风格模板 / Demo 图（运营配置的参考海报）
- [ ] Vision API 分析 Demo 图生成描述性标签
- [ ] Image Gen API 生成商品宣传图
- [ ] 生成结果展示（预览、下载、保存到相册）
- [ ] 任务状态管理（排队中、生成中、成功、失败）
- [ ] 微信登录与用户体系
- [ ] 后台：类目、风格、词条、宣传规则 CRUD
- [ ] 后台：生成任务查询与监控
- [ ] 计费前端预留（方案 A 冻结模式，后端暂不实现）

### Out of Scope

- 图片预处理/抠图（rembg 等）— 后续再加
- LEX-AI 直连 — 暂用 Codex/Gemini API
- 微信支付 — P1 再接入
- 电商平台 API 对接 — P2
- ERP 集成 — P2
- 人工审核队列 — P1
- 分销拼团等复杂营销 — 非目标

## Context

- **技术可行性已验证**：AI 生成商品海报方案已跑通，测试结论"理论没啥问题"
- **品牌定位**：光伏板下种植的优质农产品，强调品质与健康
- **产品线**：4 个 SKU — 红皮土豆(5斤/9斤)、黑珍珠土豆(5斤/9斤)
- **规格文档**：`商品宣传图-产品与技术规格.md` 是完整的技术规格参考（含 API 草案、数据模型、状态机、界面规格等），可作为实现参考但以本 PROJECT.md 为准
- **AI 流程说明**：`AI_IMAGE_PIPELINE_CLARIFICATION.md` 记录了核心 AI 流程理解

## Constraints

- **小程序 & 后台不直连 AI API**：所有 AI 调用通过 BFF 后端，密钥仅服务端
- **Prompt 仅在服务端组装**：规则引擎在后端组装完整 Prompt
- **任务快照**：创建任务时固化规则版本 + Prompt，历史任务不受后续改规则影响
- **计费暂不做**：后端不实现计费逻辑，前端按方案 A（冻结）做 UI 预留
- **图片预处理暂不做**：直接调用 Vision API + Image Gen API，不做独立抠图步骤

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| AI 引擎用 Codex/Gemini API | 图片预处理暂不做，直接调用 AI API 出图 | ⏳ Pending |
| 前端用 Uni-app | 跨端框架，编译到微信小程序 | ⏳ Pending |
| Vision API 默认 GPT-4o-mini | 性价比好，支持多模型切换 | ⏳ Pending |
| 计费方案选 A（冻结） | 后端暂不实现，前端做 UI 预留 | ⏳ Pending |
| 异步队列用 Celery + Redis | AI 调用耗时 10s+，必须异步处理 | ⏳ Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-05-12 after initialization*
