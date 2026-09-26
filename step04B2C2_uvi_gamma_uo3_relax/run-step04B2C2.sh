#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
source "${PROJECT_ROOT}/scripts/env_manager.sh"

{
  echo "=============================================================================="
  echo "STEP 04B2C2-R2 — REANÁLISE ESTRUTURAL SEM NOVO DFT"
  echo "=============================================================================="
  echo "Data: $(date)"
  echo "Host: $(hostname)"
  echo "Projeto: ${PROJECT_ROOT}"
  echo

  run_in_upb_env analysis python \
    "${SCRIPT_DIR}/04B2C2_R2_reanalyze.py"

} |& tee "${SCRIPT_DIR}/saida-step04B2C2-R2.txt"
