#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

source "${PROJECT_ROOT}/scripts/env_manager.sh"
require_upb_environment structures

cd "${SCRIPT_DIR}"

echo "============================================================"
echo "ETAPA 01-R2 — Referências cristalográficas finais"
echo "Ambiente automático: structures"
echo "============================================================"

run_in_upb_env structures \
    python 01R2_finalizar_referencias.py \
    |& tee saida-step01-R2.txt
