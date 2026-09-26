#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

source "${PROJECT_ROOT}/scripts/env_manager.sh"
require_upb_environment gpaw

cd "${SCRIPT_DIR}"

export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export PYTHONPATH="${SCRIPT_DIR}${PYTHONPATH:+:${PYTHONPATH}}"

{
    echo "=============================================================================="
    echo "STEP 03 — VALIDAÇÃO PAW + BENCHMARK PBE/PBEsol"
    echo "=============================================================================="
    echo "Data: $(date)"
    echo "Host: $(hostname)"
    echo "OMP_NUM_THREADS=${OMP_NUM_THREADS}"
    echo

    echo ">>> STEP 03A — Geração dos PAWs PBE/PBEsol"
    "${SCRIPT_DIR}/03A_generate_paw.sh"

    echo
    echo ">>> STEP 03B — Validação PBE gerado + benchmark PBEsol"
    GPAW_ENV="$(upb_env_path gpaw)"

    "${UPB_MICROMAMBA}" run \
        -r "${UPB_MAMBA_ROOT_PREFIX}" \
        -p "${GPAW_ENV}" \
        mpiexec -n 4 gpaw python \
        "${SCRIPT_DIR}/03B_benchmark_paw_functionals.py"

    echo
    echo "=============================================================================="
    echo "STEP 03 FINALIZADO"
    echo "=============================================================================="
} |& tee saida-step03.txt
