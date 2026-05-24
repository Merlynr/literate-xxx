#!/usr/bin/env bash

load_env_file() {
    local env_file="$1"
    local line key value

    if [[ ! -f "${env_file}" ]]; then
        echo "Missing env file: ${env_file}" >&2
        return 1
    fi

    set -a
    while IFS= read -r line || [[ -n "${line}" ]]; do
        line="${line%$'\r'}"
        line="${line#"${line%%[![:space:]]*}"}"
        [[ -z "${line}" || "${line}" == \#* ]] && continue

        if [[ "${line}" =~ ^([A-Za-z_][A-Za-z0-9_]*)=(.*)$ ]]; then
            key="${BASH_REMATCH[1]}"
            value="${BASH_REMATCH[2]}"
            if [[ "${value}" =~ ^\".*\"$ ]]; then
                value="${value:1:${#value}-2}"
            elif [[ "${value}" =~ ^\'.*\'$ ]]; then
                value="${value:1:${#value}-2}"
            fi
            printf -v "${key}" '%s' "${value}"
            export "${key}"
        fi
    done < <(sed '1s/^\xEF\xBB\xBF//' "${env_file}")
    set +a
}

strip_env_bom() {
    local env_file="$1"
    if grep -q $'^\xEF\xBB\xBF' "${env_file}" 2>/dev/null || file "${env_file}" | grep -q "UTF-8 Unicode (with BOM)"; then
        sed -i '1s/^\xEF\xBB\xBF//' "${env_file}"
        echo "Removed UTF-8 BOM from ${env_file}"
    fi
}
