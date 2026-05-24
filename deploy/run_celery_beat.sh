#!/usr/bin/env bash
# Celery Beat 启动包装脚本 - 用于 systemd（定时 reconciliation）
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

mkdir -p /var/run/xxzx

export PYTHONPATH="${PROJECT_DIR}:${PYTHONPATH:-}"
load_env_file "${PROJECT_DIR}/.env"

exec "${PROJECT_DIR}/.venv/bin/python" -m celery -A app.workers.celery_app beat \
    --loglevel=info \
    --schedule=/var/run/xxzx/celerybeat-schedule
