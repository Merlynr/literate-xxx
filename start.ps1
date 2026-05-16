# XX甄选 - 一键启动脚本
param(
    [switch]$BackendOnly,
    [switch]$FrontendOnly,
    [switch]$Help
)

$ProjectRoot = $PSScriptRoot
$BackendDir = Join-Path $ProjectRoot "python-bff"
$FrontendDir = Join-Path $ProjectRoot "wx-fe"

# 显示帮助
if ($Help) {
    Write-Host ""
    Write-Host "XX甄选 启动脚本帮助" -ForegroundColor Cyan
    Write-Host "===================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "用法:" -ForegroundColor Yellow
    Write-Host "  .\start.ps1              # 同时启动前后端"
    Write-Host "  .\start.ps1 -BackendOnly # 仅启动后端"
    Write-Host "  .\start.ps1 -FrontendOnly # 仅启动前端"
    Write-Host "  .\start.ps1 -Help        # 显示此帮助"
    Write-Host ""
    Write-Host "启动后访问:" -ForegroundColor Yellow
    Write-Host "  后端 API: http://localhost:8000/docs"
    Write-Host "  前端 H5:  http://localhost:5173 (如使用 dev:h5)"
    Write-Host ""
    exit 0
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  XX甄选 - 一键启动" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# 检查目录是否存在
if (-not (Test-Path $BackendDir)) {
    Write-Host "[ERROR] 后端目录不存在: $BackendDir" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $FrontendDir)) {
    Write-Host "[ERROR] 前端目录不存在: $FrontendDir" -ForegroundColor Red
    exit 1
}

$backendStarted = $false
$frontendStarted = $false

# 启动后端
if (-not $FrontendOnly) {
    Write-Host "启动后端服务 (FastAPI)..." -ForegroundColor Green
    
    $venvActivate = Join-Path $BackendDir ".venv\Scripts\Activate.ps1"
    
    if (-not (Test-Path $venvActivate)) {
        Write-Host "[ERROR] 虚拟环境不存在，请先创建:" -ForegroundColor Red
        Write-Host "  cd python-bff" -ForegroundColor Yellow
        Write-Host "  python -m venv .venv" -ForegroundColor Yellow
        Write-Host "  .\.venv\Scripts\Activate.ps1" -ForegroundColor Yellow
        Write-Host "  pip install -e ." -ForegroundColor Yellow
    } else {
        Write-Host "[INFO] 激活虚拟环境并启动 uvicorn..." -ForegroundColor Green
        
        # 在新终端窗口中启动后端
        $backendCmd = "cd '$BackendDir'; . .\.venv\Scripts\Activate.ps1; Write-Host 'Starting FastAPI backend...' -ForegroundColor Green; Write-Host 'API Docs: http://localhost:8000/docs' -ForegroundColor Cyan; Write-Host ''; uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
        Start-Process powershell -ArgumentList "-NoExit -Command `"$backendCmd`""
        
        Write-Host "[OK] 后端服务启动中..." -ForegroundColor Green
        Write-Host "  API 文档: http://localhost:8000/docs" -ForegroundColor Cyan
        $backendStarted = $true
    }
}

# 启动前端
if (-not $BackendOnly) {
    Write-Host ""
    Write-Host "启动前端服务 (Uni-app)..." -ForegroundColor Green
    
    $nodeModules = Join-Path $FrontendDir "node_modules"
    
    if (-not (Test-Path $nodeModules)) {
        Write-Host "[INFO] node_modules 不存在，正在安装依赖..." -ForegroundColor Yellow
        Push-Location $FrontendDir
        npm install
        Pop-Location
    }
    
    Write-Host "[INFO] 启动 Uni-app 开发服务器..." -ForegroundColor Green
    
    # 在新终端窗口中启动前端
    $frontendCmd = "cd '$FrontendDir'; Write-Host 'Starting Uni-app dev server...' -ForegroundColor Green; Write-Host ''; npm run dev:mp-weixin"
    Start-Process powershell -ArgumentList "-NoExit -Command `"$frontendCmd`""
    
    Write-Host "[OK] 前端服务启动中..." -ForegroundColor Green
    Write-Host "  微信小程序编译输出: dist/dev/mp-weixin" -ForegroundColor Cyan
    $frontendStarted = $true
}

Write-Host ""

if ($backendStarted -or $frontendStarted) {
    Write-Host "================================================" -ForegroundColor Cyan
    Write-Host "  启动完成" -ForegroundColor Cyan
    Write-Host "================================================" -ForegroundColor Cyan
    Write-Host ""
    
    if ($backendStarted) {
        Write-Host "[后端] http://localhost:8000" -ForegroundColor Green
        Write-Host "  - API 文档: http://localhost:8000/docs" -ForegroundColor Cyan
        Write-Host "  - 健康检查: http://localhost:8000/api/v1/health" -ForegroundColor Cyan
    }
    
    if ($frontendStarted) {
        Write-Host "[前端] 微信开发者工具导入 dist/dev/mp-weixin" -ForegroundColor Green
    }
    
    Write-Host ""
    Write-Host "提示:" -ForegroundColor Yellow
    Write-Host "  - 关闭终端窗口停止对应服务"
    Write-Host "  - 后端支持热重载，修改代码自动重启"
    Write-Host "  - 前端修改后自动重新编译"
    Write-Host ""
}
