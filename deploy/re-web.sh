#!/usr/bin/env bash
# 服务器上一键构建并发布 web-fe 静态资源
set -euo pipefail

DEPLOY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${DEPLOY_DIR}/.." && pwd)"
WEB_DIR="${PROJECT_ROOT}/web-fe"
WEB_ROOT="${WEB_ROOT:-/var/www/xxzx-web}"

if [[ ! -d "${WEB_DIR}" ]]; then
  echo "ERROR: missing ${WEB_DIR}" >&2
  exit 1
fi

if ! command -v node >/dev/null 2>&1; then
  echo "ERROR: node not found. Run: sudo bash ${DEPLOY_DIR}/install_env_centos.sh" >&2
  exit 1
fi

NODE_MAJOR="$(node -p "process.versions.node.split('.')[0]")"
if [[ "${NODE_MAJOR}" -lt 18 ]]; then
  echo "ERROR: Node.js >= 18 required (current: $(node -v))" >&2
  exit 1
fi

cd "${WEB_DIR}"

if [[ -f .env.production ]]; then
  echo "Using .env.production"
elif [[ -f .env.example ]]; then
  echo "WARN: no .env.production, copying from .env.example"
  cp .env.example .env.production
else
  echo "WARN: no .env.production — set VITE_API_BASE_URL before build"
fi

echo "==> git pull"
git pull

echo "==> npm install (includes devDependencies for vue-tsc)"
npm install

echo "==> npm run build"
npm run build

if [[ ! -d dist ]]; then
  echo "ERROR: build did not produce dist/" >&2
  exit 1
fi

echo "==> rsync to ${WEB_ROOT}"
sudo mkdir -p "${WEB_ROOT}"
sudo rsync -a --delete dist/ "${WEB_ROOT}/"

echo "Done. Open http://<your-host>/app/login (Ctrl+F5 to refresh)"
