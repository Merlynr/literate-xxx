@echo off
setlocal

echo.
echo ========================================
echo   Database Init Script
echo ========================================
echo.

set PROJECT_ROOT=%~dp0
set BACKEND_DIR=%PROJECT_ROOT%python-bff

cd /d "%BACKEND_DIR%"

echo [1/3] Creating database xxzx...
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS xxzx CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
if %errorlevel% neq 0 (
    echo [ERROR] Failed to create database. Make sure MySQL is running and password is correct.
    pause
    exit /b 1
)
echo [OK] Database created.

echo.
echo [2/3] Running Alembic migrations...
call .venv\Scripts\activate.bat
alembic upgrade head
if %errorlevel% neq 0 (
    echo [ERROR] Migration failed.
    pause
    exit /b 1
)
echo [OK] Migrations applied.

echo.
echo [3/3] Seeding default data...
python scripts/seed_default_data.py
if %errorlevel% neq 0 (
    echo [ERROR] Seed failed.
    pause
    exit /b 1
)
echo [OK] Default data seeded.

echo.
echo ========================================
echo   Database Init Complete!
echo ========================================
echo.
echo Database: xxzx
echo Tables: Created via Alembic
echo Data: Default categories, styles, terms, promo rules
echo.
pause
