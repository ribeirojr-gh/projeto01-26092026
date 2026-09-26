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
    echo "STEP 02-R4 — CONVERGÊNCIA ESTRUTURAL PBE"
    echo "=============================================================================="
    echo "Data: $(date)"
    echo "Host: $(hostname)"
    echo "OMP_NUM_THREADS=${OMP_NUM_THREADS}"
    echo "CHGNet/MACE NÃO serão reexecutados."
    echo "Scans R2/R3 NÃO serão reexecutados."
    echo

    GPAW_ENV="$(upb_env_path gpaw)"

    "${UPB_MICROMAMBA}" run \
        -r "${UPB_MAMBA_ROOT_PREFIX}" \
        -p "${GPAW_ENV}" \
        mpiexec -n 4 gpaw python \
        "${SCRIPT_DIR}/02R4_relaxed_geometry_convergence.py"

    echo
    echo "=============================================================================="
    echo "STEP 02-R4 FINALIZADO"
    echo "=============================================================================="
} |& tee saida-step02-R4.txt
