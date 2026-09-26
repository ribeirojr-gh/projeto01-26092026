#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
source "${PROJECT_ROOT}/scripts/env_manager.sh"

{
    echo "=============================================================================="
    echo "STEP 04B1B2-R3 — REANÁLISE STRESS–STRAIN UO2"
    echo "=============================================================================="
    echo "Data: $(date)"
    echo "Host: $(hostname)"
    echo "Projeto: ${PROJECT_ROOT}"
    echo

    run_in_upb_env analysis python \
        "${SCRIPT_DIR}/04B1B2_R3_stress_gate.py"

} |& tee "${SCRIPT_DIR}/saida-step04B1B2-R3.txt"
