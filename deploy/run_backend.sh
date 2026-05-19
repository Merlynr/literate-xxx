#!/usr/bin/env bash
# FastAPI 启动包装脚本 - 用于 systemd
set -euo pipefail

DEPLOY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${DEPLOY_DIR}/../python-bff"
cd "${PROJECT_DIR}"

# 激活虚拟环境
source .venv/bin/activate

# 设置 PYTHONPATH
export PYTHONPATH="${PROJECT_DIR}:${PYTHONPATH:-}"

# 加载环境变量
set -a
source .env
set +a

exec python -m uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 2 \
    --log-level info \
    --log-config "${DEPLOY_DIR}/log_config.yaml"
