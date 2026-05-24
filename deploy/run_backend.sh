#!/usr/bin/env bash
# FastAPI 启动包装脚本 - 用于 systemd
set -euo pipefail

DEPLOY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${DEPLOY_DIR}/../python-bff"
# shellcheck disable=SC1091
source "${DEPLOY_DIR}/lib/env.sh"

cd "${PROJECT_DIR}"

if [[ ! -x "${PROJECT_DIR}/.venv/bin/python" ]]; then
    echo "Missing virtualenv python: ${PROJECT_DIR}/.venv/bin/python" >&2
    exit 127
fi

export PYTHONPATH="${PROJECT_DIR}:${PYTHONPATH:-}"
load_env_file "${PROJECT_DIR}/.env"

exec "${PROJECT_DIR}/.venv/bin/python" -m uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 2 \
    --log-level info \
    --log-config "${DEPLOY_DIR}/log_config.yaml"
