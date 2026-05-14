@echo off
setlocal

echo.
echo ========================================
echo   XX Selection - Full Stack Startup
echo ========================================
echo.

set PROJECT_ROOT=%~dp0
set BACKEND_DIR=%PROJECT_ROOT%python-bff
set FRONTEND_DIR=%PROJECT_ROOT%wx-fe

if not exist "%BACKEND_DIR%" (
    echo [ERROR] Backend directory not found: %BACKEND_DIR%
    pause
    exit /b 1
)

if not exist "%FRONTEND_DIR%" (
    echo [ERROR] Frontend directory not found: %FRONTEND_DIR%
    pause
    exit /b 1
)

if not exist "%BACKEND_DIR%\.venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found. Please create it first:
    echo   cd python-bff
    echo   python -m venv .venv
    echo   .venv\Scripts\activate
    echo   pip install -e .
    pause
    exit /b 1
)

echo [1/4] Checking Redis...
where redis-cli >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARN] redis-cli not found in PATH. Make sure Redis is running.
    echo       Download: https://github.com/tporadowski/redis/releases
) else (
    redis-cli ping >nul 2>&1
    if %errorlevel% neq 0 (
        echo [INFO] Starting Redis server...
        start "Redis Server" redis-server
        timeout /t 2 /nobreak >nul
    ) else (
        echo [OK] Redis is already running.
    )
)

echo [2/4] Starting Celery Worker...
start "Celery Worker" cmd /k "cd /d "%BACKEND_DIR%" && call .venv\Scripts\activate.bat && echo Starting Celery worker... && celery -A app.workers.celery_app worker --loglevel=info --pool=solo"

timeout /t 2 /nobreak >nul

echo [3/4] Starting FastAPI Backend...
start "FastAPI Backend" cmd /k "cd /d "%BACKEND_DIR%" && call .venv\Scripts\activate.bat && echo Starting FastAPI backend... && echo API Docs: http://localhost:8000/docs && echo. && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

timeout /t 2 /nobreak >nul

echo [4/4] Starting Uni-app Frontend...
start "Uni-app Frontend" cmd /k "cd /d "%FRONTEND_DIR%" && echo Starting Uni-app dev server... && echo. && npm run dev:mp-weixin"

echo.
echo ========================================
echo   All Services Started!
echo ========================================
echo.
echo [Redis]     localhost:6379
echo [Celery]    Worker running (solo pool)
echo [Backend]   http://localhost:8000
echo               - API Docs: http://localhost:8000/docs
echo               - Health: http://localhost:8000/api/v1/health
echo [Frontend]  WeChat DevTools: dist\dev\mp-weixin
echo.
echo Tips:
echo   - Close terminal window to stop that service
echo   - Backend supports hot reload
echo   - Frontend auto-recompiles on changes
echo   - Use Ctrl+C in Celery window to stop worker
echo.
pause
