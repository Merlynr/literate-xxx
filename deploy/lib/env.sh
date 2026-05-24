#!/usr/bin/env bash

load_env_file() {
    local env_file="$1"
    if [[ ! -f "${env_file}" ]]; then
        echo "Missing env file: ${env_file}" >&2
        return 1
    fi

    set -a
    # Strip UTF-8 BOM and CRLF so Windows-edited .env files work under systemd/bash.
    # shellcheck disable=SC1090
    source <(sed '1s/^\xEF\xBB\xBF//' "${env_file}" | tr -d '\r')
    set +a
}

strip_env_bom() {
    local env_file="$1"
    if grep -q $'^\xEF\xBB\xBF' "${env_file}" 2>/dev/null || file "${env_file}" | grep -q "UTF-8 Unicode (with BOM)"; then
        sed -i '1s/^\xEF\xBB\xBF//' "${env_file}"
        echo "Removed UTF-8 BOM from ${env_file}"
    fi
}
