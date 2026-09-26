#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
STEP03="${PROJECT_ROOT}/step03_paw_pbesol_benchmark/run-step03.sh"
if [[ ! -x "${STEP03}" ]]; then
    [[ -f "${STEP03}" ]] || { echo "ERRO: Step 03 não encontrado: ${STEP03}" >&2; exit 2; }
    chmod +x "${STEP03}"
fi
cd "${PROJECT_ROOT}"
"${STEP03}"
