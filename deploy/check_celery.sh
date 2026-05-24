#!/usr/bin/env bash
# 诊断 Celery Worker / Beat 与 Redis 队列（在服务器上以 root 或项目目录执行）
set -euo pipefail

DEPLOY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${DEPLOY_DIR}/.." && pwd)"
BACKEND_DIR="${PROJECT_ROOT}/python-bff"
# shellcheck disable=SC1091
source "${DEPLOY_DIR}/lib/env.sh"

if [[ ! -f "${BACKEND_DIR}/.env" ]]; then
  echo "ERROR: missing ${BACKEND_DIR}/.env"
  exit 1
fi

load_env_file "${BACKEND_DIR}/.env"
export PYTHONPATH="${BACKEND_DIR}:${PYTHONPATH:-}"
PY="${BACKEND_DIR}/.venv/bin/python"

echo "========== 1. systemd 状态 =========="
for unit in xxzx-celery xxzx-celery-beat xxzx-backend; do
  if systemctl list-unit-files "${unit}.service" &>/dev/null; then
    systemctl is-active "${unit}" 2>/dev/null || true
    systemctl show "${unit}" -p ActiveState -p SubState -p MainPID --no-pager 2>/dev/null || true
  else
    echo "${unit}: not installed"
  fi
  echo "---"
done

echo "========== 2. 进程 =========="
pgrep -af 'celery.*app.workers.celery_app' || echo "(no celery process found)"

echo "========== 3. .env 中的 broker =========="
grep -E '^(CELERY_BROKER_URL|CELERY_RESULT_BACKEND|REDIS_URL)=' "${BACKEND_DIR}/.env" | sed 's/:\/\/:[^@]*@/:\/\//:***@/'

echo "========== 4. Redis 队列长度（broker 在 DB 1，勿用默认 DB 0）=========="
BROKER="${CELERY_BROKER_URL:-}"
if [[ "${BROKER}" =~ redis://:([^@]+)@([^:/]+):([0-9]+)/([0-9]+) ]]; then
  REDIS_PASS="${BASH_REMATCH[1]}"
  REDIS_HOST="${BASH_REMATCH[2]}"
  REDIS_PORT="${BASH_REMATCH[3]}"
  REDIS_DB="${BASH_REMATCH[4]}"
  echo "Parsing broker -> host=${REDIS_HOST} port=${REDIS_PORT} db=${REDIS_DB}"
  redis-cli -h "${REDIS_HOST}" -p "${REDIS_PORT}" -a "${REDIS_PASS}" -n "${REDIS_DB}" LLEN celery || true
else
  echo "Could not parse CELERY_BROKER_URL; run manually:"
  echo "  redis-cli -a 'PASSWORD' -n 1 LLEN celery"
fi

echo "========== 5. 本机代码里已注册的任务（无需 Worker 在线）=========="
"${PY}" - <<'PY'
from app.workers.celery_app import celery_app
import app.workers.tasks  # noqa: F401

names = sorted(
    t for t in celery_app.tasks.keys()
    if not t.startswith("celery.")
)
print("Registered task names:", names)
required = {"generation.process", "generation.reconcile"}
missing = required - set(names)
if missing:
    print("ERROR: missing tasks:", missing)
else:
    print("OK: generation.process and generation.reconcile are registered")
PY

echo "========== 6. inspect ping（仅当 Worker 在线时有回复）=========="
if "${PY}" -m celery -A app.workers.celery_app inspect ping --timeout=5 2>/dev/null; then
  echo "Worker responded to inspect."
else
  echo "No nodes replied -> Worker 未连上 broker 或未启动。请看日志:"
  echo "  tail -n 80 /var/log/xxzx/celery.log"
  echo "  journalctl -u xxzx-celery -n 50 --no-pager"
fi

echo "========== 7. 最近 Worker 日志 =========="
if [[ -f /var/log/xxzx/celery.log ]]; then
  tail -n 40 /var/log/xxzx/celery.log
else
  echo "(no /var/log/xxzx/celery.log)"
fi
