# XX甄选 Web 端 — UI Design Contract

**Status:** Ready for planning  
**Scope:** User portal + Admin console + optional marketing landing  
**Baseline:** Mini program at `wx-fe/` (3 tabs: 首页 / 生成 / 我的)  
**Backend:** FastAPI BFF at `python-bff/` (JWT auth, generation pipeline, admin CRUD APIs exist)  
**Brand reference:** Phase 3 UI-SPEC — warm cream, deep green, solar gold; premium agricultural  
**Primary design reference:** [鹿鸣服饰 AI 视觉工作台](http://116.62.193.174:3001/index.html)（第一阶段 HTML 原型，2026.05）  
**Secondary references:** Pic Copilot、即梦AI — 大画布预览与电商 SaaS 交互补充

---

## 0. Reference Site Analysis（鹿鸣服饰原型）

> **说明：** 上一版设计时用户未提供该 URL，默认参考 Pic Copilot。现已实地访问并对齐本规范。

### 0.1 站点概况

| 项 | 内容 |
|----|------|
| URL | `http://116.62.193.174:3001/index.html`（未登录会跳转 `login.html`） |
| 产品名 | 鹿鸣服饰 · 商品图 AI 工作台 / AI 视觉工作台 |
| 形态 | 单页 HTML 原型（Client Portal + 运营账号分离） |
| 测试账号 | 客户 `client@luming.test` / `123456`；运营 `admin@luming.test` / `123456` |

### 0.2 信息架构（应对齐 XX甄选 Web）

左侧固定导航（SPA 锚点切换，桌面可改为独立路由）：

| 导航项 | 功能 | XX甄选 映射 |
|--------|------|-------------|
| **工作台** | 仪表盘：进行中生产、统计卡、最近任务、上传/打开图库 CTA | `/app/dashboard` |
| **发起生成** | 创建任务表单 + 拖拽上传 + Smart Preview + 交付规格 | `/app/generate` |
| **生成任务** | 任务队列 / Generation Queue | `/app/works?tab=tasks` 或生成页底部队列 |
| **成品图库** | 成品网格、按系列下载提示（淘宝/抖店/小红书） | `/app/works` |
| **可定制模块** | 增值能力卡片（资料整理、即梦 API、分析、工具链、SOP） | Web 独有 `/app/modules`（P1） |
| **客户配置中心** | 品牌专属说明、演示周期、额度说明 | `/app/account` |

### 0.3 登录页模式

- 居中白卡片 + 品牌 Logo（层叠图标）+ 登录/注册 Tab
- 邮箱 + 密码；页脚展示测试账号
- **XX甄选 采纳：** 保留邮箱登录（Web）；小程序侧继续微信；运营账号进 `/admin`

### 0.4 工作台（Dashboard）要点

- 顶栏：`CLIENT PORTAL` 英文标签 + 中文主标题 + 一句话价值主张
- **Production 卡：** 当前批次状态（如「春夏新品视觉正在生成」）+ 主体增强动效 + 识别准确率等进度文案
- **统计：** 张商品图 / 已完成任务 / 当前交付速度
- **Recent Jobs：** 最近任务列表
- **主 CTA：**「上传商品」「打开图库」
- **XX甄选 采纳：** 结构照搬；文案改为农产品 SKU；动效区展示真实 `generation-jobs` 轮询状态（排队/生成中/成功）

### 0.5 发起生成（核心表单）

| 字段 | 鹿鸣原型 | XX甄选 实现 |
|------|----------|-------------|
| 商品名称 | 文本，如「夏季法式连衣裙」 | 保留为「商品/批次名称」（可选，写入 `prompt_hint` 或 job 备注） |
| 出图类型 | 单选：白底主图 / 场景图 / 详情页图 | 映射为 **类目 + 风格**（后端已有）；或增加 `output_type` 枚举（P1） |
| 画面要求 | 多行文本 | 对齐小程序「补充提示」`prompt_hint` |
| 上传区 | 拖拽 +「正面、侧面、细节图」提示 | OSS 预签名多图上传（Web 增强） |
| 交付规格 | 右侧说明卡 | 显示预计消耗额度、画幅、水印策略（读 promo_rule 摘要） |
| Smart Preview | 右侧预览区 | 源图预览 + 生成结果画布（放大 XX 差异化） |
| 主按钮 | 「开始 AI 生成」 | 「开始生成」→ `POST /generation-jobs` |

### 0.6 成品图库 & 可定制模块

- **图库：** 成品卡片网格 +「创建更多成品」；引导文案提及多平台上架
- **可定制模块（Paid Add-ons）：** 五张能力卡 — 资料整理/文案、即梦·豆包 API、店铺分析、工具链连接、视觉规则 SOP
- **XX甄选：** 图库对接真实 `listGenerationHistory`；增值模块作为 Web 扩展路线图（与小程序能力差异点），不要求 MVP 全部实现

### 0.7 视觉风格 — 借鉴 vs 差异化

| 维度 | 鹿鸣原型 | XX甄选 |
|------|----------|--------|
| 布局 | 左栏导航 + 右主内容、大圆角卡片、黑白主按钮 | **采纳布局与组件层级** |
| 配色 | 白/灰/黑 + 紫色激活条 | **改用** 奶油底 `#fbf7ef` + 深绿 `#1f5d3a` + 金色 `#b98b2a`（农业品牌） |
| 文案 | 中英混排（Client Portal、Production） | 中文为主，英文仅作次要 label（可选） |
| 行业 | 服饰电商 | 农产品 / 光伏农业 |

---

## 1. Executive Summary

XX甄选 Web 端是小程序的**桌面级增强版**，面向两类用户：

1. **商家/运营人员（End User Portal）** — 布局与流程**以鹿鸣服饰原型为主参考**，在 PC 上批量上传、对比结果、管理历史；预览区与对比能力可再参考 Pic Copilot。
2. **平台运营（Admin Console）** — 配置类目、风格、词条、宣传规则、定价套餐，监控生成任务与额度流水。后端 CRUD API 已就绪，缺 UI。

**技术选型：Vue 3 + Vite + Element Plus + Tailwind CSS**

| 选项 | 结论 |
|------|------|
| React + Vite + Tailwind | 生态强，但与 `wx-fe/` 无代码复用 |
| **Vue 3 + Element Plus + Tailwind** | **推荐** — 团队已在 Uni-app/Vue3 栈；Pinia store、API 类型、生成流程状态机可直接迁移；Element Plus 提供 Admin 所需的 Table/Drawer/Form 模式 |

**产品气质：** 可信、实用、农业品质感 — 不是 playful 消费 App，也不是 generic 紫色渐变 SaaS。暖奶油底 + 深绿主色 + 金色点缀，大画布预览，步骤清晰。

**交付形态：** 单仓库 `web-fe/`（建议），路由分区：

- `/` — 公开营销页（可选 MVP 后）
- `/app/*` — 用户工作台（需登录）
- `/admin/*` — 运营后台（需登录，v1 单角色全权限）

---

## 2. Personas

### 2.1 商家用户 — 李姐（End User）

| 属性 | 描述 |
|------|------|
| 角色 | 农产品电商店主，负责商品上架与主图 |
| 设备 | 办公室 PC（主）+ 手机浏览器（辅） |
| 目标 | 把实拍图快速变成可投放的宣传海报，一次多张、对比选优 |
| 痛点 | 小程序屏小、单任务、难批量下载；相册保存不便 |
| 成功标准 | 5 分钟内完成上传→生成→下载 ZIP，能看清细节 |

### 2.2 平台运营 — 小王（Operator）

| 属性 | 描述 |
|------|------|
| 角色 | XX甄选 内部运营，维护类目/风格/词条/规则 |
| 设备 | 桌面浏览器 |
| 目标 | 不改代码即可调整 AI 出图策略；排查失败任务 |
| 痛点 | 目前只能调 API，无可视化配置与监控 |
| 成功标准 | 表格+抽屉完成 CRUD；任务列表可筛失败原因 |

### 2.3 访客 — 潜在客户（Landing，P1）

| 属性 | 描述 |
|------|------|
| 角色 | 了解产品的农业/电商从业者 |
| 目标 | 理解价值主张，引导至小程序或 Web 注册 |
| 成功标准 | 30 秒内看懂「实拍→海报」价值，有明确 CTA |

---

## 3. Information Architecture

### 3.1 User Portal (`/app`)

> 导航命名与顺序对齐鹿鸣原型：`工作台 → 发起生成 → 生成任务 → 成品图库 → 可定制模块`；账户/配置收在侧栏底部或「客户配置中心」。

```
/app
├── /login              登录（邮箱密码 / 微信扫码 / Dev）— 对齐 login.html
├── /dashboard          工作台 — Production 卡 + 统计 + 最近任务
├── /generate           发起生成 — 表单 + Smart Preview + 交付规格
├── /works              成品图库 — 网格 + 批量下载
├── /works/tasks        生成任务 — 队列列表（可与图库 Tab 合并）
├── /modules            可定制模块（P1，Web-only 路线图）
├── /works/:jobId       作品详情 — 大图对比 + 元数据
├── /account            客户配置中心 — 额度、隐私、品牌说明
└── /privacy            隐私协议全文（静态）
```

**Primary nav（Desktop sidebar，对齐鹿鸣）：**

| Icon | Label | Route |
|------|-------|-------|
| Home | 工作台 | `/app/dashboard` |
| Plus | 发起生成 | `/app/generate` |
| Clock | 生成任务 | `/app/works/tasks` |
| Grid | 成品图库 | `/app/works` |
| Sparkles | 可定制模块 | `/app/modules` (P1) |
| Settings | 客户配置 | `/app/account` |

**Mobile web：** 底部 Tab 栏对齐小程序三 Tab（首页 / 生成 / 我的），账户入口在「我的」页内。

### 3.2 Admin Console (`/admin`)

```
/admin
├── /login              运营登录（v1 与用户共用 JWT + 后续 RBAC）
├── /dashboard          概览 — 今日任务数、成功率、额度消耗
├── /catalog
│   ├── /categories     类目 CRUD
│   └── /styles         风格 CRUD（含封面上传）
├── /content
│   ├── /terms          词条库 CRUD
│   └── /promo-rules    宣传规则 + 版本
├── /billing
│   ├── /pricing-plans  定价套餐 CRUD
│   └── /quota-ledger   额度流水
├── /jobs               生成任务监控
└── /settings           租户设置（P1）
```

**Admin nav pattern：** 左侧固定 Sidebar（240px）+ 顶栏面包屑 + 内容区 Table 列表 + 右侧 Drawer 编辑。

### 3.3 Marketing Landing (`/`, P1)

```
/                       Hero + 三步流程 + 示例对比 + CTA
/features               功能详情（可选）
/pricing                套餐说明（UI 壳，支付 P1 后接入）
```

---

## 4. Page-by-Page Wireframe Descriptions

### 4.1 Login — `/app/login` & `/admin/login`

**Layout:** 居中卡片（max-width 420px），左侧可选品牌插画（Desktop ≥1024px 分栏）。

**Elements:**
- Logo + 「XX甄选」+ 副标题「AI 商品宣传图生成」
- **Tab 切换：** 微信扫码 | 邮箱/手机（P1 API 扩展）| 开发模式（仅 dev）
- 微信扫码：QR code 区域 + 「请使用微信扫一扫」+ 轮询登录状态
- Dev 模式：`dev-login` API，昵称输入（对齐 `wx-fe` 调试流）
- 底部链接：隐私协议、用户条款
- Footer：「光伏板下优质农产品 · 红皮土豆 · 黑珍珠土豆」

**States:** QR 过期刷新、登录中 spinner、失败 toast「登录失败，请重试」

---

### 4.2 Dashboard — `/app/dashboard`

**Layout:** 内容区 max-width 1200px，居中。

**Sections（自上而下）：**
1. **Hero strip** — 欢迎语 + 租户/昵称；右侧「开始生成」主 CTA（green gradient）
2. **QuotaCard（增强版）** — 可用 / 冻结 / 总量三指标 + 当前套餐名 + 「刷新额度」；对齐小程序 `QuotaCard.vue`
3. **Quick actions 三卡** — 拍照上传 → AI 生成 → 下载使用（复用小程序 copy，图标换 SVG）
4. **Recent works 横向滚动** — 最近 6 条，缩略图 + 状态 badge，「查看全部 →」链至 `/app/works`

**Empty:** 无作品时显示引导卡「完成第一次生成，作品会出现在这里」

---

### 4.3 Generate Workbench — `/app/generate` ★ Core

**Layout（Desktop ≥1280px）：** 经典 SaaS 三栏

```
┌─────────────────────────────────────────────────────────────┐
│ Top bar: 步骤条 GenerateStepper + 额度摘要 chip              │
├──────────────────┬──────────────────────────────────────────┤
│ Left panel       │ Main canvas (false
│ 320px fixed      │ flex-1                                   │
│                  │                                          │
│ · 隐私协议 gate  │  [ Large preview / result canvas ]       │
│ · 类目 chips     │  zoom controls (+/-) fit/100%            │
│ · 风格卡片网格   │  compare toggle: 原图 | 水印 | 并排      │
│ · 上传区         │                                          │
│ · 补充提示       │  ─────────────────────────────────────   │
│ · 预计消耗       │  ProgressPanel / ResultPanel / Queue     │
│ · CTA 开始生成   │                                          │
└──────────────────┴──────────────────────────────────────────┘
│ Bottom queue strip (collapsible): 进行中的任务 1/3           │
└─────────────────────────────────────────────────────────────┘
```

**Left panel sections（对齐小程序 generate 页）：**

1. **PrivacyAgreementCard** — 未同意时置顶阻断；已同意折叠为 badge
2. **GenerateStepper** — 三步：上传实拍图 → 选择类目/风格 → 输出原图/水印图
3. **类目** — 水平 chip 组（Element Plus `el-check-tag` 或自定义 pill）；选中 deep green fill
4. **风格** — 2 列卡片网格，封面图 + 名称；选中 border + shadow
5. **UploadCard** — 拖拽区（`drag-over` 高亮 gold border）；支持多文件队列（Web-only）；显示文件名、大小、上传进度；「重新上传」secondary
6. **补充提示** — textarea，placeholder 对齐小程序：「例如：突出新鲜感、保留包装标签、整体更高级」，max 300 字
7. **Quota estimate** — 调用 `POST /quota/estimate`，显示「预计消耗 N 张」
8. **Actions** — 「清空结果」secondary + 「开始生成 ⌘↵」primary（disabled until canGenerate）

**Main canvas states:**
- **Idle:** 虚线占位 + 「上传实拍图或从历史选择」
- **Source preview:** 上传后的源图，fit-to-container
- **Generating:** 骨架 shimmer + ProgressPanel（排队中 / 生成中 / 进度条）
- **Result:** 默认水印图；Tab 切换「水印图 | 原图 | 并排对比」；zoom 100%–400%；滚轮缩放
- **Error:** 红色 alert card + 「重新生成」「返回编辑」

**Web-only — Generation Queue Panel:**
- 支持同时提交最多 3 个 job（可配置）
- 底部可折叠条显示各 job 状态、缩略图、取消（若 API 支持）
- 完成 job 桌面通知（Notification API，需授权）

**Keyboard shortcuts:**
| Key | Action |
|-----|--------|
| `⌘/Ctrl + Enter` | 开始生成 |
| `Esc` | 关闭预览 lightbox |
| `+` / `-` | 画布缩放 |
| `1` / `2` | 切换水印/原图 |
| `D` | 下载当前预览 |

**Mobile web（<768px）：** 回退为小程序式纵向堆叠；sticky bottom CTA；canvas 全宽

---

### 4.4 Works — `/app/works`

**Layout:** 顶栏筛选 + 主内容网格/列表切换。

**Filter bar（Web-only）：**
- 日期范围 picker
- 类目 select
- 状态 select（queued / running / succeeded / failed）
- 搜索 job_id（P1）
- 视图切换：网格 | 列表
- 「批量选择」→ 批量下载 ZIP

**Grid view:** 3–4 列卡片，缩略图（水印图优先）+ 状态 badge + 时间 + 类目/风格 label（P1 API 扩展）

**List view:** 对齐小程序 `WorksList` — 左图右文，状态 + 时间 + 描述

**Empty:** 「暂无作品」+ 「完成一次生成后，这里会显示你的历史作品。」+ CTA「去生成」

**Pagination:** 每页 20/50/100，offset 分页对齐现有 API

---

### 4.5 Work Detail — `/app/works/:jobId`

**Layout:** 全宽详情，左右分栏（Desktop）。

**Left:** 并排对比组件 — slider 或 50/50 split（原图 vs 水印图）  
**Right:** 元数据面板 — job_id、状态、创建时间、类目、风格、prompt_hint、error_message（若失败）  
**Actions:** 下载原图、下载水印图、下载 ZIP、重新生成（保留配置）、复制 job_id

---

### 4.6 Account — `/app/account`

**Sections:**
- 用户头像占位 + 昵称 + 租户 ID（截断显示，hover 全量）
- QuotaCard + 额度历史链接（P1）
- 隐私协议状态 + 「查看全文」+ 重新确认（若政策更新）
- 退出登录

**Fix from mini program:** 我的页 header 用了 `#1aad19 → #12b7f5` 微信绿蓝渐变，与品牌不符；Web 统一为 `#1f5d3a → #2d7d4d` 深绿渐变。

---

### 4.7 Admin Dashboard — `/admin/dashboard`

**Layout:** 4 列 stat cards + 2 列 chart 区（P1 接 chart 库）。

| Card | Metric |
|------|--------|
| 今日任务 | count + vs 昨日 |
| 成功率 | % + sparkline |
| 额度消耗 | units |
| 失败任务 | count + 链接至 /admin/jobs?status=failed |

**Recent failures table:** 最近 10 条失败 job，job_id、error_message、时间、「查看详情」

---

### 4.8 Admin CRUD Pages — Table + Drawer Pattern

**统一模式（categories / styles / terms / promo-rules / pricing-plans）：**

```
┌─────────────────────────────────────────────────┐
│ Page title          [+ 新建]  [搜索]  [筛选]     │
├─────────────────────────────────────────────────┤
│ el-table                                        │
│ · 名称 · 状态 · 排序 · 更新时间 · 操作(编辑/删除) │
├─────────────────────────────────────────────────┤
│ pagination                                      │
└─────────────────────────────────────────────────┘

Drawer (480px, right):
  Form fields
  [取消] [保存]
```

**Categories (`/admin/catalog/categories`):**
- 字段：name, slug/code, sort_order, is_active, cover_image（可选）
- API: `GET/POST/PUT/DELETE /categories`

**Styles (`/admin/catalog/styles`):**
- 字段：name, category_id（关联）, cover_image_url（OSS 上传）, demo_asset, sort_order, is_active
- 封面预览列
- API: `GET/POST/PUT/DELETE /styles`

**Terms (`/admin/content/terms`):**
- 字段：term_type（正向/负向/前缀/品牌）, content, weight, scope, sort_order
- API: `GET/POST/PUT/DELETE /terms`

**Promo Rules (`/admin/content/promo-rules`):**
- 字段：name, category_id, style_id, version, slot_config（JSON 编辑器）, is_published
- 版本历史 sub-table（P1）
- API: `GET/POST/PUT/DELETE /promo-rules`

**Pricing Plans (`/admin/billing/pricing-plans`):**
- 字段：name, total_units, validity_days, applicable_categories, is_active
- API: `GET/POST/PUT/DELETE /admin/pricing-plans`

**Quota Ledger (`/admin/billing/quota-ledger`):**
- 只读表格：tenant, delta, reason, job_id, created_at
- API: `GET /quota/admin/quota-ledger`

**Jobs Monitor (`/admin/jobs`):**
- 筛选：status, date range, tenant_id, category_id
- 列：job_id, status, tenant, category, style, created_at, duration, error_message
- 行点击 → Drawer 详情：源图、结果图、完整 error、LEX trace（P1）
- API: 需扩展 admin jobs list（当前仅有单 job `GET /generation-jobs/{id}` 与 history）

---

### 4.9 Marketing Landing — `/` (P1)

**Sections:**
1. **Hero** — 「把实物图，变成能直接投放的宣传海报」+ before/after 滑动对比 + CTA「免费体验」→ `/app/login`
2. **三步流程** — 上传 → 选风格 → 下载（对齐小程序 feature cards）
3. **品质背书** — 光伏板下种植、红皮/黑珍珠土豆 SKU 展示
4. **竞品差异化** — Vision 自动学 Demo、运营可配词条、水印自动贴合
5. **Footer** — 隐私协议、联系我们、小程序码

**Visual:** 全宽 cream 背景，hero 区 subtle green/gold radial gradients（对齐 generate 页 backdrop）

---

## 5. Component Library

### 5.1 Design Tokens

```css
/* Brand — extend wx-fe generate page */
--color-cream-50:   #fbf7ef;
--color-cream-100:  #f3ead8;
--color-cream-200:  #eef3ee;
--color-green-900:  #10291b;   /* text primary */
--color-green-700:  #1f5d3a;   /* accent / CTA */
--color-green-500:  #2d7d4d;   /* gradient end */
--color-gold-600:   #b98b2a;   /* highlight / step dot idle */
--color-gold-400:   #d9b563;
--color-error:      #9e331b;
--color-muted:      rgba(16, 41, 27, 0.68);

/* 60/30/10 */
/* 60% cream backgrounds | 30% green text/borders | 10% gold accents + CTA gradients */
```

### 5.2 Spacing Scale (Tailwind-aligned)

| Token | Value | Usage |
|-------|-------|-------|
| xs | 4px | icon gaps |
| sm | 8px | inline spacing |
| md | 16px | card padding mobile |
| lg | 24px | section gaps |
| xl | 32px | page padding |
| 2xl | 48px | hero vertical |

**Avoid arbitrary values** except canvas max-height viewport calculations.

### 5.3 Typography

| Role | Size | Weight | Color |
|------|------|--------|-------|
| Display | 36–44px | 900 | green-900 |
| H1 | 28–32px | 800 | green-900 |
| H2 | 20–24px | 700 | green-700 |
| Body | 14–16px | 400 | green-900 / muted |
| Caption | 12–13px | 400 | muted |
| Eyebrow | 11–12px | 700 | green-700, letter-spacing 0.1em |

**Font stack:** `"PingFang SC", "Microsoft YaHei", system-ui, sans-serif`  
**Max distinct sizes per page:** 4  
**Max weights:** 2 (400, 700/800)

### 5.4 Core Components

| Component | Source | Web enhancements |
|-----------|--------|------------------|
| `AppShell` | New | Sidebar + topbar + responsive collapse |
| `QuotaCard` | Port from `wx-fe` | Add trend sparkline (P1) |
| `GenerateStepper` | Port | Horizontal on desktop |
| `CategoryChips` | Port | Wrap grid on narrow |
| `StyleCardGrid` | Port | 2–3 col responsive |
| `UploadDropzone` | Port `UploadCard` | Drag-drop, multi-file, progress bars |
| `PromptHintField` | Port | Auto-resize textarea |
| `ProgressPanel` | Port | Elapsed timer, cancel button |
| `ResultCanvas` | Port `ResultPanel` | Zoom, compare slider, lightbox |
| `CompareSlider` | New | Before/after draggable divider |
| `AlbumActions` → `DownloadActions` | Port | ZIP bulk, direct download (no album API) |
| `WorksGrid` / `WorksList` | Port | Filters, bulk select |
| `PrivacyAgreementCard` | Port | Link to full text page |
| `GenerationQueueStrip` | New | Multi-job status |
| `AdminDataTable` | New | Table + Drawer CRUD wrapper |
| `AdminFormDrawer` | New | Element Plus drawer form |
| `ImageUploader` | New | Presign OSS flow |
| `EmptyState` | New | Icon + title + desc + CTA |
| `ErrorAlert` | New | Actionable recovery links |
| `LoginQrPanel` | New | WeChat scan login |
| `StatCard` | New | Admin dashboard metrics |

### 5.5 Element Plus Theme Override

- `--el-color-primary: #1f5d3a`
- `--el-color-primary-light-3: #2d7d4d`
- `--el-border-radius-base: 12px`
- Table header background: `cream-100`
- Drawer width: 480px (forms), 720px (job detail)

---

## 6. States (Empty / Loading / Error)

### 6.1 Global Rules

- **Never blank during polling** — always show ProgressPanel or skeleton
- **Primary CTA disabled** until: source uploaded + category + style + privacy accepted + not busy
- **Retry preserves** category/style/prompt selections (align `generation.ts` store behavior)

### 6.2 State Matrix

| Context | Empty | Loading | Error | Success |
|---------|-------|---------|-------|---------|
| Dashboard works | 「暂无作品」+ CTA | Skeleton cards × 3 | 「加载失败，点击重试」 | Grid of thumbnails |
| Generate catalog | 「暂无类目/风格，请联系运营」 | Skeleton chips + style cards | Toast + inline alert | Interactive selectors |
| Upload | Dashed dropzone + 「拖拽或点击上传」 | Progress bar + 「上传并确认中...」 | 「图片上传失败」+ 重试 | Preview thumbnail + 「已确认」 |
| Generate job | — | Stepper step 3 active + progress | Red card「生成失败」+ error_message + 「重新生成」 | Result canvas + download actions |
| Works list | 「暂无作品」 | Table/ grid skeleton | 「加载失败」 | Populated list |
| Admin table | 「暂无数据」+ 新建 CTA | `v-loading` | 「保存失败：{reason}」 | Toast「已保存」 |
| Login QR | — | Spinner「等待扫码」 | 「二维码已过期，点击刷新」 | Redirect to dashboard |

### 6.3 Copywriting Contract

**Tone:** 短句中文、明确状态、无技术黑话。

| Context | Copy |
|---------|------|
| Primary CTA | 开始生成 |
| Secondary | 清空结果 / 重新上传实拍图 |
| Upload idle | 拖拽图片到此处，或点击选择文件 |
| Upload busy | 上传并确认中... |
| Generate queued | 任务排队中... |
| Generate running | AI 正在生成中... |
| Generate success | 生成完成 |
| Generate failed | 生成失败 |
| Privacy gate | 首次生成前需要确认你已阅读并同意隐私协议与用户条款 |
| Quota eyebrow | 剩余额度 |
| Works empty title | 暂无作品 |
| Works empty desc | 完成一次生成后，这里会显示你的历史作品。 |
| Admin save | 保存 / 取消 |
| Admin delete confirm | 确定删除「{name}」？此操作不可恢复。 |

**Avoid:** Submit, OK, Click Here, No data, Error occurred, 通用「确认」

**Status labels (explicit):** 排队中 / 生成中 / 已完成 / 失败 — map from API `queued|running|succeeded|failed`

---

## 7. Web-Only Feature Matrix vs Mini Program

| Feature | Mini Program (`wx-fe`) | Web (`web-fe`) | Priority |
|---------|------------------------|----------------|----------|
| Login | 微信 OAuth only | 微信扫码 + 邮箱/手机 (P1) + Dev | MVP: 扫码 + Dev |
| Upload | 相册/拍照单张 | 拖拽 + 多文件队列 | MVP |
| Generate layout | 纵向滚动 | 左 panel + 右 canvas | MVP |
| Result preview | `uni.previewImage` | In-page zoom + lightbox + compare slider | MVP |
| Download | 保存到相册 | 直接下载 + ZIP 批量 | MVP |
| Multi-job | 单任务 | 生成队列 panel（最多 3 并行） | P1 |
| History filters | 下拉刷新 only | 日期/类目/状态筛选 + 搜索 | P1 |
| Keyboard shortcuts | — | ⌘↵ 生成, +/- 缩放, 1/2 切换 | P1 |
| Quota estimate | 未展示 UI | 生成前「预计消耗 N 张」 | MVP |
| Admin CRUD | 无 | 全量后台 | MVP (parallel track) |
| Job monitor | 无 | Admin 任务列表 + 失败诊断 | MVP |
| Marketing landing | 无 | 公开 `/` 页 | P1 |
| Desktop notifications | 无 | Job 完成通知 | P2 |
| Side-by-side compare | 切换预览 | 50/50 slider + 同步 zoom | MVP |
| Bulk select works | 无 | 多选 + ZIP 下载 | P1 |

---

## 8. Responsive Breakpoints

| Breakpoint | Width | Layout behavior |
|------------|-------|-----------------|
| Mobile S | <375px | 单列，bottom tab nav，canvas 100vw |
| Mobile | 375–767px | 单列，sticky CTA，chip 横向 scroll |
| Tablet | 768–1023px | 可选 collapsible sidebar；generate 可 40/60 split |
| Desktop | 1024–1279px | Full sidebar；generate 320px + canvas |
| Desktop L | ≥1280px | Max content 1440px；works grid 4 col；admin table full |

**Generate page responsive rule:** ≥1024px 启用左右分栏；<1024px 回退小程序式纵向（功能不删减，布局堆叠）。

**Admin:** ≥768px 固定 sidebar；<768px 汉堡菜单（可用但非主要场景）。

**Touch targets:** Minimum 44×44px on mobile web.

---

## 9. Accessibility Basics

| Requirement | Implementation |
|-------------|----------------|
| Color contrast | green-900 on cream-50 ≥ 4.5:1；primary button white on green-700 verified |
| Focus visible | `:focus-visible` ring 2px gold-400 on interactive elements |
| Keyboard nav | All CTAs, chips, style cards focusable；generate shortcuts documented in `?` help modal |
| Alt text | 上传预览 `alt="商品实拍图"`；结果图 `alt="生成的水印宣传图"` |
| Icon buttons | aria-label 必填：「放大」「下载原图」「关闭预览」 |
| Form labels | Element Plus form labels linked；textarea 有 visible label「补充提示」 |
| Status announcements | `aria-live="polite"` on ProgressPanel status text |
| Reduced motion | `prefers-reduced-motion` 禁用 canvas zoom animation |
| Language | `<html lang="zh-CN">` |

---

## 10. Implementation Phases

### Phase A — MVP User Portal (2–3 weeks)

**Goal:** Web 端完成与小程序 parity + 核心 desktop 增强

- [ ] Project scaffold: Vue 3 + Vite + Element Plus + Tailwind + Pinia + Vue Router
- [ ] Auth: Dev login + JWT refresh（复用 `auth` API）
- [ ] Port stores: `user.ts`, `generation.ts`（适配 web file picker）
- [ ] Pages: login, dashboard, generate (split layout), works, account
- [ ] Components: QuotaCard, Stepper, Upload dropzone, Progress, Result canvas, Download
- [ ] Quota estimate display
- [ ] Compare slider + zoom
- [ ] Direct download (single image)

**Exit criteria:** 用户可在 Desktop 完成 上传→生成→下载 全流程；视觉对齐 brand tokens

### Phase B — MVP Admin Console (2 weeks, parallel)

**Goal:** 运营可配置 catalog + 查看任务

- [ ] Admin shell + login
- [ ] CRUD: categories, styles, terms, promo-rules, pricing-plans
- [ ] Quota ledger 只读
- [ ] Jobs list（需 backend admin list endpoint 或 paginated history）
- [ ] OSS image upload in style form

**Exit criteria:** 运营无需 Postman 即可维护类目/风格/词条

### Phase C — P1 Enhancements (2 weeks)

- [ ] WeChat QR scan login for web
- [ ] Works filters + bulk ZIP download
- [ ] Generation queue (multi-job)
- [ ] Keyboard shortcuts + help modal
- [ ] Marketing landing page `/`
- [ ] Email/phone login (backend + UI)
- [ ] Admin dashboard charts

### Phase D — P2 Polish

- [ ] RBAC roles
- [ ] Desktop notifications
- [ ] Tenant settings UI
- [ ] Rule version diff / preview
- [ ] Mobile web PWA manifest

---

## Appendix A: API Mapping (Existing BFF)

| UI Action | Endpoint |
|-----------|----------|
| Login | `POST /auth/login`, `POST /auth/dev-login`, `POST /auth/refresh`, `GET /auth/me` |
| Categories list | `GET /categories` |
| Styles list | `GET /styles` |
| Upload | `POST /uploads/presign` or `POST /uploads/direct` |
| Confirm asset | `POST /generation-assets/confirm` |
| Create job | `POST /generation-jobs` |
| Poll job | `GET /generation-jobs/{job_id}` |
| History | `GET /generation-history?offset&limit` |
| Quota | `GET /quota/summary`, `POST /quota/estimate` |
| Privacy | `GET /privacy/agreement-status`, `POST /privacy/accept` |
| Admin CRUD | `/categories`, `/styles`, `/terms`, `/promo-rules`, `/admin/pricing-plans` |
| Admin ledger | `GET /quota/admin/quota-ledger` |

**Gap to backend:** Admin jobs list with filters; generation history category/style metadata; web QR login session endpoint.

---

## Appendix B: Registry Safety

**shadcn/ui:** Not used — Element Plus is the component library. No third-party block registry audit required.

---

*Document version: 1.0 — 2026-05-24*  
*Authors: GSD UI phase — derived from `wx-fe/` implementation + `03-UI-SPEC.md` brand contract*
