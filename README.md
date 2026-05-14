# XX甄选

AIGC 商品宣传图生成平台 - 微信小程序

## 快速开始

### 前置要求

- Node.js >= 18
- Python >= 3.10
- MySQL
- Redis
- 微信开发者工具

### 一键启动

#### Windows PowerShell (推荐)

```powershell
.\start.ps1
```

#### Windows 命令提示符

```cmd
start.bat
```

#### npm 脚本

```bash
npm start
```

### 仅启动后端

```powershell
.\start.ps1 -BackendOnly
```

### 仅启动前端

```powershell
.\start.ps1 -FrontendOnly
```

## 启动后访问

| 服务 | 地址 |
|------|------|
| 后端 API | http://localhost:8000 |
| API 文档 | http://localhost:8000/docs |
| 健康检查 | http://localhost:8000/api/v1/health |
| 前端 | 微信开发者工具导入 `dist/dev/mp-weixin` |

## 手动启动

### 后端 (FastAPI)

```bash
cd python-bff

# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境 (Windows)
.venv\Scripts\activate

# 安装依赖
pip install -e .

# 配置环境变量
copy .env.example .env
# 编辑 .env 填入实际配置

# 启动服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 前端 (Uni-app)

```bash
cd wx-fe

# 安装依赖
npm install

# 启动微信小程序开发
npm run dev:mp-weixin

# 或启动 H5 版本
npm run dev:h5
```

## 项目结构

```
xxzx/
├── python-bff/     # FastAPI 后端
├── wx-fe/          # Uni-app 前端 (微信小程序)
├── .planning/      # 项目规划文档
├── start.ps1       # PowerShell 启动脚本
├── start.bat       # 批处理启动脚本
└── package.json    # 根项目配置
```

## 环境配置

复制 `python-bff/.env.example` 到 `python-bff/.env` 并配置:

- MySQL 连接信息
- Redis 连接信息
- MinIO/S3 存储配置
- 微信小程序 AppID/Secret
- AI API 密钥 (DashScope)

## 开发说明

- 后端支持热重载，修改代码自动重启
- 前端修改后自动重新编译
- 关闭终端窗口停止对应服务

## 技术栈

| 层次 | 技术 |
|------|------|
| 前端 | Uni-app (Vue 3 + TypeScript) |
| 后端 | FastAPI + SQLAlchemy + Celery |
| 数据库 | MySQL |
| 缓存/队列 | Redis |
| 对象存储 | MinIO/S3 |
| AI | GPT-4o-mini + DashScope |
