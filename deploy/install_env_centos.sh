#!/usr/bin/env bash
set -euo pipefail

# CentOS 8 / EL9 deployment prerequisite installer.
# - Installs build tools and common runtime libraries
# - Installs Node.js 18 if missing or too old
# - Builds Python 3.11 from source when the system Python is below 3.10
# - Does not overwrite the system default python3

PYTHON_VERSION="3.11.9"
NODE_SETUP_URL="https://rpm.nodesource.com/setup_18.x"
PYTHON_TARBALL_URL="https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tgz"

log() { printf '\n[%s] %s\n' "$1" "$2"; }
info() { log INFO "$1"; }
warn() { log WARN "$1"; }
die() { log ERROR "$1" >&2; exit 1; }

require_root() {
  if [[ "${EUID}" -ne 0 ]]; then
    die "Please run this script as root."
  fi
}

detect_pkg_manager() {
  if command -v dnf >/dev/null 2>&1; then
    echo dnf
  elif command -v yum >/dev/null 2>&1; then
    echo yum
  else
    die "dnf/yum not found."
  fi
}

version_ge() {
  # true if $1 >= $2
  [[ "$(printf '%s\n%s\n' "$1" "$2" | sort -V | head -n1)" == "$2" ]]
}

have_python_310_plus() {
  if ! command -v python3 >/dev/null 2>&1; then
    return 1
  fi

  local py_ver
  py_ver="$(python3 - <<'PY'
import sys
print(".".join(map(str, sys.version_info[:3])))
PY
)"
  version_ge "$py_ver" "3.10.0"
}

have_node_18_plus() {
  if ! command -v node >/dev/null 2>&1; then
    return 1
  fi

  local node_ver
  node_ver="$(node -p 'process.versions.node' 2>/dev/null || true)"
  [[ -n "$node_ver" ]] && version_ge "$node_ver" "18.0.0"
}

enable_extra_repos() {
  local pm="$1"

  if [[ -f /etc/os-release ]]; then
    # shellcheck disable=SC1091
    source /etc/os-release
  fi

  if command -v dnf >/dev/null 2>&1; then
    if command -v dnf-plugins-core >/dev/null 2>&1 || "$pm" -y install dnf-plugins-core; then
      :
    fi

    if command -v dnf >/dev/null 2>&1; then
      # EL8: powertools, EL9: crb. Try both; ignore failures when a repo name is absent.
      dnf config-manager --set-enabled powertools >/dev/null 2>&1 || true
      dnf config-manager --set-enabled crb >/dev/null 2>&1 || true
    fi
  fi

  if command -v "$pm" >/dev/null 2>&1; then
    "$pm" -y install epel-release >/dev/null 2>&1 || true
  fi
}

install_base_packages() {
  local pm="$1"

  info "Installing base system packages"
  "$pm" -y install \
    ca-certificates \
    curl \
    wget \
    git \
    tar \
    unzip \
    xz \
    zip \
    rsync \
    which \
    make \
    gcc \
    gcc-c++ \
    patch \
    openssl-devel \
    bzip2-devel \
    libffi-devel \
    zlib-devel \
    readline-devel \
    sqlite-devel \
    xz-devel \
    tk-devel \
    libuuid-devel \
    libjpeg-turbo-devel \
    freetype-devel \
    redhat-rpm-config
}

install_python_from_source() {
  if have_python_310_plus; then
    info "System Python already satisfies 3.10+, skipping source build"
    return 0
  fi

  info "Installing Python ${PYTHON_VERSION} from source (does not replace system Python)"
  mkdir -p /usr/local/src
  pushd /usr/local/src >/dev/null
  curl -fSL "$PYTHON_TARBALL_URL" -o "Python-${PYTHON_VERSION}.tgz"
  tar -xzf "Python-${PYTHON_VERSION}.tgz"
  cd "Python-${PYTHON_VERSION}"

  ./configure --enable-optimizations --with-lto
  make -j"$(nproc)"
  make altinstall

  /usr/local/bin/python3.11 -m ensurepip --upgrade
  /usr/local/bin/python3.11 -m pip install --upgrade pip setuptools wheel
  popd >/dev/null
}

install_nodejs() {
  if have_node_18_plus; then
    info "Node.js already satisfies 18+, skipping installation"
    return 0
  fi

  info "Installing Node.js 18"
  curl -fsSL "$NODE_SETUP_URL" | bash -
  "$PM" -y install nodejs
  node -v
  npm -v
}

install_optional_services() {
  local pm="$1"

  warn "Optional: if you plan to host Redis / MariaDB locally, install and enable them separately."
  warn "  $pm -y install redis mariadb-server"
  warn "  systemctl enable --now redis mariadb"
}

main() {
  require_root

  if [[ -f /etc/os-release ]]; then
    # shellcheck disable=SC1091
    source /etc/os-release
    case "${ID:-}" in
      centos|rhel|rocky|almalinux)
        info "Detected OS: ${PRETTY_NAME:-unknown}"
        ;;
      *)
        warn "This is not a CentOS/RHEL family system. Continuing anyway: ${PRETTY_NAME:-unknown}"
        ;;
    esac
  fi

  PM="$(detect_pkg_manager)"
  info "Using package manager: ${PM}"

  enable_extra_repos "$PM"
  install_base_packages "$PM"
  install_python_from_source
  install_nodejs
  install_optional_services "$PM"

  cat <<EOF

Done.

Next steps:
1. Create the backend venv: cd python-bff && /usr/local/bin/python3.11 -m venv .venv
2. Install backend deps: .venv/bin/pip install -e .
3. Install frontend deps: cd wx-fe && npm install
4. If you use local MySQL / Redis, install and configure those services separately

EOF
}

main "$@"
