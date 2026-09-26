#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
source "${PROJECT_ROOT}/scripts/env_manager.sh"

{
  echo "=============================================================================="
  echo "STEP 05A-R1 — CORREÇÃO DO DESIGN DE SUPERCÉLULAS"
  echo "=============================================================================="
  echo "Data: $(date)"
  echo "Host: $(hostname)"
  echo "Projeto: ${PROJECT_ROOT}"
  echo
  echo "Nenhum DFT novo será executado."
  echo

  run_in_upb_env structures python \
    "${SCRIPT_DIR}/05A_R1_rebuild_supercells.py"

} |& tee "${SCRIPT_DIR}/saida-step05A-R1.txt"
