#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# XX甄选 - Backend Startup Script (CentOS 8)
# ============================================================
# 启动 FastAPI 后端 + Celery Worker
# 用法: sudo bash start_backend.sh [start|stop|restart|status]
# ============================================================

# ---------- 配置区域 ----------

# 项目根目录 (脚本所在目录的上级)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="${PROJECT_ROOT}/python-bff"

# Python (自动检测，优先使用 python3.11，其次 python3)
PYTHON_BIN=""

# 虚拟环境路径
VENV_DIR="${BACKEND_DIR}/.venv"
VENV_BIN="${VENV_DIR}/bin"

# 服务配置
HOST="0.0.0.0"
PORT=8000
WORKERS=2
LOG_LEVEL="info"

# 日志目录
LOG_DIR="/var/log/xxzx"
BACKEND_LOG="${LOG_DIR}/backend.log"
CELERY_LOG="${LOG_DIR}/celery.log"
CELERY_BEAT_LOG="${LOG_DIR}/celery_beat.log"

# PID 文件
PID_DIR="/var/run/xxzx"
BACKEND_PID="${PID_DIR}/backend.pid"
CELERY_PID="${PID_DIR}/celery.pid"
CELERY_BEAT_PID="${PID_DIR}/celery_beat.pid"

# ---------- 工具函数 ----------

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info()    { echo -e "${GREEN}[INFO]${NC}  $1"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC}  $1"; }
log_error()   { echo -e "${RED}[ERROR]${NC} $1"; }

die() {
    log_error "$1"
    exit 1
}

# ---------- 环境检查 ----------

check_root() {
    if [[ "${EUID}" -ne 0 ]]; then
        die "请使用 root 权限运行此脚本: sudo bash $0"
    fi
}

detect_python() {
    # 按优先级查找: python3.11 -> python3.10 -> python3 -> python
    local candidates=("python3.11" "python3.10" "python3" "python")
    for cmd in "${candidates[@]}"; do
        if command -v "${cmd}" &>/dev/null; then
            local ver
            ver=$("${cmd}" -c "import sys; print('.'.join(map(str, sys.version_info[:3])))")
            # 检查版本 >= 3.10
            local major minor
            major=$(echo "${ver}" | cut -d. -f1)
            minor=$(echo "${ver}" | cut -d. -f2)
            if [[ "${major}" -ge 3 && "${minor}" -ge 10 ]]; then
                PYTHON_BIN="$(command -v "${cmd}")"
                log_info "找到 Python ${ver} (${PYTHON_BIN})"
                return 0
            fi
        fi
    done
    die "未找到 Python >= 3.10，请先运行 install_env_centos.sh 安装"
}

check_python() {
    detect_python
}

check_venv() {
    # 检查虚拟环境是否存在且完整
    if [[ ! -f "${VENV_BIN}/activate" ]]; then
        log_warn "虚拟环境不存在或不完整，正在创建..."
        rm -rf "${VENV_DIR}" 2>/dev/null || true
        "${PYTHON_BIN}" -m venv "${VENV_DIR}"
        
        # 验证创建成功
        if [[ ! -f "${VENV_BIN}/activate" ]]; then
            die "虚拟环境创建失败，请检查 Python 是否支持 venv 模块"
        fi
        log_info "虚拟环境已创建: ${VENV_DIR}"
    fi

    # 激活虚拟环境
    # shellcheck disable=SC1091
    source "${VENV_BIN}/activate"
    
    if [[ -z "${VIRTUAL_ENV:-}" ]]; then
        die "虚拟环境激活失败"
    fi
    log_info "虚拟环境已激活: ${VIRTUAL_ENV}"
}

check_dependencies() {
    cd "${BACKEND_DIR}"

    # 升级 pip
    pip install --upgrade pip setuptools wheel -q

    # 检查是否已安装依赖 (通过检查 fastapi 是否已安装)
    if ! python -c "import fastapi" &>/dev/null; then
        log_info "首次运行，安装项目依赖..."
        pip install -e . -q
        log_info "依赖安装完成"
    else
        log_info "依赖已安装，跳过"
    fi
}

check_env_file() {
    if [[ ! -f "${BACKEND_DIR}/.env" ]]; then
        if [[ -f "${BACKEND_DIR}/.env.example" ]]; then
            log_warn ".env 文件不存在，请从 .env.example 创建:"
            log_warn "  cp ${BACKEND_DIR}/.env.example ${BACKEND_DIR}/.env"
            log_warn "  vim ${BACKEND_DIR}/.env"
            die "请配置 .env 文件后重新运行"
        else
            die ".env 和 .env.example 都不存在"
        fi
    fi
    log_info ".env 文件已就绪"
}

check_services() {
    # 检查 Redis
    if command -v redis-cli &>/dev/null; then
        if ! redis-cli ping &>/dev/null; then
            log_warn "Redis 未运行，正在启动..."
            systemctl start redis 2>/dev/null || redis-server --daemonize yes
            sleep 1
        fi
        log_info "Redis: OK"
    else
        log_warn "redis-cli 未找到，请确保 Redis 已安装并运行"
    fi

    # 检查 MySQL
    if command -v mysql &>/dev/null; then
        if ! systemctl is-active --quiet mysqld 2>/dev/null && \
           ! systemctl is-active --quiet mariadb 2>/dev/null; then
            log_warn "MySQL/MariaDB 未运行，正在启动..."
            systemctl start mysqld 2>/dev/null || systemctl start mariadb 2>/dev/null || true
        fi
        log_info "MySQL: OK"
    else
        log_warn "mysql 客户端未找到，请确保 MySQL/MariaDB 已安装并运行"
    fi
}

# ---------- 初始化 ----------

init_dirs() {
    mkdir -p "${LOG_DIR}" "${PID_DIR}"
    chown -R root:root "${LOG_DIR}" "${PID_DIR}"
    chmod 755 "${LOG_DIR}" "${PID_DIR}"
}

# ---------- 服务管理 ----------

is_running() {
    local pid_file="$1"
    if [[ -f "${pid_file}" ]]; then
        local pid
        pid=$(cat "${pid_file}")
        if kill -0 "${pid}" 2>/dev/null; then
            return 0
        fi
    fi
    return 1
}

start_backend() {
    if is_running "${BACKEND_PID}"; then
        log_warn "FastAPI 后端已在运行 (PID: $(cat "${BACKEND_PID}"))"
        return 0
    fi

    log_info "启动 FastAPI 后端..."
    cd "${BACKEND_DIR}"

    # 设置 PYTHONPATH 确保能找到 app 模块
    export PYTHONPATH="${BACKEND_DIR}:${PYTHONPATH:-}"

    nohup python -m uvicorn app.main:app \
        --host "${HOST}" \
        --port "${PORT}" \
        --workers "${WORKERS}" \
        --log-level "${LOG_LEVEL}" \
        --access-log \
        >> "${BACKEND_LOG}" 2>&1 &

    echo $! > "${BACKEND_PID}"
    log_info "FastAPI 后端已启动 (PID: $!)"
    log_info "  地址: http://${HOST}:${PORT}"
    log_info "  文档: http://${HOST}:${PORT}/docs"
}

start_celery_worker() {
    if is_running "${CELERY_PID}"; then
        log_warn "Celery Worker 已在运行 (PID: $(cat "${CELERY_PID}"))"
        return 0
    fi

    log_info "启动 Celery Worker..."
    cd "${BACKEND_DIR}"

    # 设置 PYTHONPATH
    export PYTHONPATH="${BACKEND_DIR}:${PYTHONPATH:-}"

    nohup python -m celery -A app.workers.celery_app worker \
        --loglevel="${LOG_LEVEL}" \
        --pool=solo \
        --concurrency=1 \
        >> "${CELERY_LOG}" 2>&1 &

    echo $! > "${CELERY_PID}"
    log_info "Celery Worker 已启动 (PID: $!)"
}

start_celery_beat() {
    if is_running "${CELERY_BEAT_PID}"; then
        log_warn "Celery Beat 已在运行 (PID: $(cat "${CELERY_BEAT_PID}"))"
        return 0
    fi

    log_info "启动 Celery Beat..."
    cd "${BACKEND_DIR}"

    # 设置 PYTHONPATH
    export PYTHONPATH="${BACKEND_DIR}:${PYTHONPATH:-}"

    nohup python -m celery -A app.workers.celery_app beat \
        --loglevel="${LOG_LEVEL}" \
        --schedule=/var/run/xxzx/celerybeat-schedule \
        >> "${CELERY_BEAT_LOG}" 2>&1 &

    echo $! > "${CELERY_BEAT_PID}"
    log_info "Celery Beat 已启动 (PID: $!)"
}

stop_service() {
    local name="$1"
    local pid_file="$2"

    if ! is_running "${pid_file}"; then
        log_info "${name} 未运行"
        return 0
    fi

    local pid
    pid=$(cat "${pid_file}")
    log_info "停止 ${name} (PID: ${pid})..."

    kill "${pid}" 2>/dev/null || true

    # 等待进程退出 (最多 10 秒)
    local count=0
    while kill -0 "${pid}" 2>/dev/null && (( count < 10 )); do
        sleep 1
        ((count++))
    done

    if kill -0 "${pid}" 2>/dev/null; then
        log_warn "强制终止 ${name}..."
        kill -9 "${pid}" 2>/dev/null || true
    fi

    rm -f "${pid_file}"
    log_info "${name} 已停止"
}

start_all() {
    log_info "=========================================="
    log_info "  XX甄选 - 后端服务启动"
    log_info "=========================================="

    check_root
    check_python
    check_venv
    check_dependencies
    check_env_file
    check_services
    init_dirs

    start_backend
    start_celery_worker
    # start_celery_beat  # 如需定时任务，取消此行注释

    echo ""
    log_info "=========================================="
    log_info "  所有服务已启动"
    log_info "=========================================="
    log_info "  后端 API:    http://localhost:${PORT}"
    log_info "  API 文档:    http://localhost:${PORT}/docs"
    log_info "  健康检查:    http://localhost:${PORT}/api/v1/health"
    log_info "  日志目录:    ${LOG_DIR}"
    log_info "=========================================="
}

stop_all() {
    log_info "=========================================="
    log_info "  XX甄选 - 停止服务"
    log_info "=========================================="

    stop_service "Celery Beat" "${CELERY_BEAT_PID}"
    stop_service "Celery Worker" "${CELERY_PID}"
    stop_service "FastAPI 后端" "${BACKEND_PID}"

    log_info "所有服务已停止"
}

status_all() {
    echo ""
    echo "=========================================="
    echo "  XX甄选 - 服务状态"
    echo "=========================================="

    # FastAPI
    if is_running "${BACKEND_PID}"; then
        log_info "FastAPI 后端:  运行中 (PID: $(cat "${BACKEND_PID}"))"
    else
        log_warn "FastAPI 后端:  未运行"
    fi

    # Celery Worker
    if is_running "${CELERY_PID}"; then
        log_info "Celery Worker: 运行中 (PID: $(cat "${CELERY_PID}"))"
    else
        log_warn "Celery Worker: 未运行"
    fi

    # Celery Beat
    if is_running "${CELERY_BEAT_PID}"; then
        log_info "Celery Beat:   运行中 (PID: $(cat "${CELERY_BEAT_PID}"))"
    else
        log_warn "Celery Beat:   未运行"
    fi

    echo "=========================================="
}

# ---------- 入口 ----------

case "${1:-start}" in
    start)
        start_all
        ;;
    stop)
        stop_all
        ;;
    restart)
        stop_all
        sleep 2
        start_all
        ;;
    status)
        status_all
        ;;
    *)
        echo "用法: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac
