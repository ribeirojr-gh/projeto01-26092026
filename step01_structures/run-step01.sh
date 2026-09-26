#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

ENV_MANAGER="${PROJECT_ROOT}/scripts/env_manager.sh"

if [[ ! -f "${ENV_MANAGER}" ]]; then
    echo "ERRO: ${ENV_MANAGER} não encontrado." >&2
    echo "Copie o arquivo scripts/env_manager.sh deste pacote para a raiz do projeto." >&2
    exit 2
fi

source "${ENV_MANAGER}"

require_upb_environment structures

STRUCT_ENV="$(upb_env_path structures)"

echo "============================================================"
echo "ETAPA 01 — Busca e padronização de estruturas"
echo "============================================================"
echo "Projeto:    ${PROJECT_ROOT}"
echo "Ambiente:   ${STRUCT_ENV}"
echo "Python:     $("${UPB_MICROMAMBA}" run -r "${UPB_MAMBA_ROOT_PREFIX}" -p "${STRUCT_ENV}" which python)"
echo "Versão:     $("${UPB_MICROMAMBA}" run -r "${UPB_MAMBA_ROOT_PREFIX}" -p "${STRUCT_ENV}" python --version)"
echo "============================================================"

cd "${SCRIPT_DIR}"

run_in_upb_env structures \
    python 01_busca_estruturas.py \
    |& tee saida-step01.txt
