# Phase 3 手动验收清单

> 适用于本阶段已完成后，人工核对当前实现是否可用。

## 一、当前已实现功能

### 1. 后端基础接口

- 健康检查接口：
  - `GET /api/v1/health/liveness`
  - `GET /api/v1/health/readiness`
- 用途：
  - 验证 FastAPI 服务是否启动
  - 验证数据库、Redis、MinIO/S3 是否连通

### 2. 上传资产流程

- `POST /api/v1/uploads/presign`
- `POST /api/v1/generation-assets/confirm`
- 用途：
  - 先申请 OSS 预签名上传地址
  - 文件上传到 OSS 后，再确认成业务资产
- 结果：
  - 返回 `asset_id`
  - 返回资产签名下载 URL

### 3. 生成任务流程

- `POST /api/v1/generation-jobs`
- `GET /api/v1/generation-jobs/{job_id}`
- 用途：
  - 创建生成任务
  - 查询任务状态
  - 支持 `client_request_id` 幂等
- 状态流转：
  - `queued`
  - `running`
  - `succeeded`
  - `failed`

### 4. AI 生成流水线

- 默认接阿里云万相
- 视觉分析和图像生成都已经接到 worker pipeline
- 用途：
  - 读取上传的商品图
  - 生成冻结的 prompt snapshot
  - 调用图像生成
  - 生成结果图

### 5. 结果图存储

- 原图和水印图都单独存 OSS
- 结果任务响应里会带：
  - `raw_result_download_url`
  - `watermarked_result_download_url`
- 用途：
  - 可以直接下载原图和水印图

### 6. 数据库表

- 已有表：
  - `tenants`
  - `users`
  - `categories`
  - `styles`
  - `terms`
  - `promo_rules`
  - `generation_assets`
  - `generation_jobs`
  - `generation_job_events`

### 7. 前端生成页

- 已替换成完整生成流程页面
- 页面能力：
  - 选择类目
  - 选择风格
  - 上传商品图
  - 输入补充提示词
  - 发起生成
  - 展示进度
  - 展示结果

### 8. 前端接口层

- 已接好生成相关 API
- 支持：
  - 拉取类目
  - 拉取风格
  - 预签名上传
  - 确认资产
  - 创建任务
  - 查询任务

## 二、手动验收步骤

### 1. 启动后端

- 目录：`F:\project\xxx\python-bff`
- 命令：

```powershell
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- 期望：
  - 终端显示启动成功，没有报错

### 2. 验证健康检查

- 打开：
  - `http://127.0.0.1:8000/api/v1/health/liveness`
  - `http://127.0.0.1:8000/api/v1/health/readiness`

- 期望：
  - liveness 返回 `{"status":"ok"}`
  - readiness 返回 `status=ok` 或至少能看到数据库、Redis、MinIO 的检查结果

### 3. 验证基础数据接口

- 打开：
  - `http://127.0.0.1:8000/api/v1/categories/?is_active=true&limit=100`
  - `http://127.0.0.1:8000/api/v1/styles/?is_active=true&limit=100`

- 期望：
  - 能返回类目列表
  - 能返回风格列表

### 4. 启动前端 H5

- 目录：`F:\project\xxx\wx-fe`
- 命令：

```powershell
npm run dev:h5
```

- 期望：
  - 终端给出本地 H5 地址，通常是 `http://localhost:5173`

### 5. 打开生成页

- 打开前端页面后进入生成页

- 期望：
  - 页面能正常渲染
  - 能看到步骤条、类目、风格、上传区域、生成按钮、结果区域

### 6. 验证类目和风格展示

- 在生成页里查看类目和风格是否自动加载

- 期望：
  - 至少能看到 1 个类目
  - 至少能看到 1 个风格
  - 默认选中第一项

### 7. 验证上传确认流程

- 选择一张本地图片上传

- 期望：
  - 页面先申请 `presign`
  - 文件上传到 OSS
  - 再调用 `generation-assets/confirm`
  - 页面显示“已确认”或类似状态

### 8. 验证生成任务创建

- 在页里选好类目、风格，点击生成

- 期望：
  - 成功创建 `generation job`
  - 返回 `job_id`
  - `status` 初始是 `queued`

### 9. 验证任务状态轮询

- 任务创建后，观察页面进度

- 期望：
  - 状态会从 `queued` 过渡到 `running`
  - 最终到 `succeeded` 或 `failed`
  - 如果没有配置万相 Key，失败也应该返回可读错误信息

### 10. 验证结果链接

- 当任务成功后，查看结果区域

- 期望：
  - 有原图下载链接
  - 有水印图下载链接
  - 两者都是独立 OSS 对象的签名 URL

### 11. 验证幂等性

- 用同一个 `client_request_id` 重复提交一次任务

- 期望：
  - 返回同一个任务
  - 不会重复创建新任务

### 12. 验证数据库落表

- 在数据库里检查这几张表：
  - `generation_assets`
  - `generation_jobs`
  - `generation_job_events`

- 期望：
  - 上传后有 `generation_assets`
  - 提交任务后有 `generation_jobs`
  - 过程事件会写到 `generation_job_events`

## 三、建议的验收顺序

1. 健康检查
2. 类目/风格接口
3. 上传确认
4. 创建任务
5. 看状态轮询
6. 看结果 URL
7. 查数据库

## 四、已知前置条件

- `python-bff/.env` 里的数据库、Redis、MinIO 必须能连通
- 真正走到 AI 生成，需要 `DASHSCOPE_API_KEY`
- 如果只是验证前端页面和上传链路，可以先不等真实生成成功

