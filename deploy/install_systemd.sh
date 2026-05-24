#!/usr/bin/env bash
# Install xxzx-backend and xxzx-celery systemd units for the current checkout.
set -euo pipefail

DEPLOY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${DEPLOY_DIR}/.." && pwd)"
BACKEND_DIR="${PROJECT_ROOT}/python-bff"
# shellcheck disable=SC1091
source "${DEPLOY_DIR}/lib/env.sh"

if [[ "${EUID}" -ne 0 ]]; then
  echo "Please run as root: sudo bash $0"
  exit 1
fi

if [[ ! -f "${BACKEND_DIR}/.env" ]]; then
  echo "Missing ${BACKEND_DIR}/.env"
  exit 1
fi

mkdir -p /var/log/xxzx /var/run/xxzx
chmod 755 /var/log/xxzx /var/run/xxzx

render_unit() {
  local template="$1"
  local target="$2"
  sed \
    -e "s|/opt/xxzx|${PROJECT_ROOT}|g" \
    "${template}" > "${target}"
}

render_unit "${DEPLOY_DIR}/xxzx-backend.service" /etc/systemd/system/xxzx-backend.service
render_unit "${DEPLOY_DIR}/xxzx-celery.service" /etc/systemd/system/xxzx-celery.service
render_unit "${DEPLOY_DIR}/xxzx-celery-beat.service" /etc/systemd/system/xxzx-celery-beat.service

for script in \
  "${DEPLOY_DIR}/run_backend.sh" \
  "${DEPLOY_DIR}/run_celery.sh" \
  "${DEPLOY_DIR}/run_celery_beat.sh" \
  "${DEPLOY_DIR}/check_celery.sh" \
  "${DEPLOY_DIR}/install_systemd.sh" \
  "${DEPLOY_DIR}/lib/env.sh"; do
  if [[ -f "${script}" ]]; then
    sed -i 's/\r$//' "${script}"
    chmod +x "${script}"
  fi
done
strip_env_bom "${BACKEND_DIR}/.env"

systemctl daemon-reload
systemctl enable xxzx-backend xxzx-celery xxzx-celery-beat

echo "Installed systemd units for project root: ${PROJECT_ROOT}"
echo "Next:"
echo "  sudo bash ${DEPLOY_DIR}/start_backend.sh stop   # stop cron/nohup instances"
echo "  sudo systemctl start xxzx-backend xxzx-celery xxzx-celery-beat"
echo "  sudo systemctl status xxzx-backend xxzx-celery xxzx-celery-beat"
echo ""
echo "Note: run only ONE xxzx-celery-beat instance cluster-wide."
