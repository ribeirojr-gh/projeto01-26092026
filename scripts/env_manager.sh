#!/usr/bin/env bash
# Biblioteca comum de ambientes do projeto U-Pb em carbonatos.
# Este arquivo é carregado com "source" e NÃO altera as opções do shell.

_upb_this_file="${BASH_SOURCE[0]}"
UPB_PROJECT_ROOT="$(cd "$(dirname "${_upb_this_file}")/.." && pwd)"

UPB_MICROMAMBA="${UPB_PROJECT_ROOT}/.tools/micromamba"
UPB_MAMBA_ROOT_PREFIX="${UPB_PROJECT_ROOT}/.micromamba"
UPB_ENVS_ROOT="${UPB_PROJECT_ROOT}/.envs"

export MAMBA_ROOT_PREFIX="${UPB_MAMBA_ROOT_PREFIX}"

upb_env_path() {
    local env_name="${1:-}"
    [[ -n "${env_name}" ]] || { echo "ERRO: nome do ambiente não informado." >&2; return 2; }

    case "${env_name}" in
        structures) echo "${UPB_ENVS_ROOT}/structures" ;;
        mlip)       echo "${UPB_ENVS_ROOT}/mlip" ;;
        gpaw)       echo "${UPB_ENVS_ROOT}/gpaw" ;;
        analysis)   echo "${UPB_ENVS_ROOT}/analysis" ;;
        *) echo "ERRO: ambiente desconhecido: ${env_name}" >&2; return 2 ;;
    esac
}

require_upb_environment() {
    local env_name="${1:-}"
    local env_path
    env_path="$(upb_env_path "${env_name}")" || return $?

    [[ -x "${UPB_MICROMAMBA}" ]] || {
        echo "ERRO: micromamba não encontrado em ${UPB_MICROMAMBA}" >&2
        return 3
    }

    [[ -x "${env_path}/bin/python" ]] || {
        echo "ERRO: ambiente '${env_name}' não encontrado em ${env_path}" >&2
        return 4
    }
}

run_in_upb_env() {
    local env_name="${1:-}"
    shift || true
    local env_path
    env_path="$(upb_env_path "${env_name}")" || return $?
    require_upb_environment "${env_name}" || return $?

    "${UPB_MICROMAMBA}" run \
        -r "${UPB_MAMBA_ROOT_PREFIX}" \
        -p "${env_path}" \
        "$@"
}
