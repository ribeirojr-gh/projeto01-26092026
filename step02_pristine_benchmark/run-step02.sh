#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
source "${PROJECT_ROOT}/scripts/env_manager.sh"

require_upb_environment mlip
require_upb_environment gpaw
require_upb_environment structures

cd "${SCRIPT_DIR}"

# Evita multiplicação involuntária de threads em cada rank MPI.
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1

{
    echo "=============================================================================="
    echo "STEP 02 — PRÉ-RELAXAÇÃO MLIP + CONVERGÊNCIA NUMÉRICA GPAW"
    echo "=============================================================================="
    echo "Data: $(date)"
    echo "Host: $(hostname)"
    echo "OMP_NUM_THREADS=${OMP_NUM_THREADS}"
    echo

    echo ">>> STEP 02A — CHGNet -> MACE (GPU, processo único)"
    run_in_upb_env mlip python 02A_mlip_prerelax.py

    echo
    echo ">>> STEP 02B — GPAW/PBEsol (4 processos MPI)"
    GPAW_ENV="$(upb_env_path gpaw)"
    "${UPB_MICROMAMBA}" run \
        -r "${UPB_MAMBA_ROOT_PREFIX}" \
        -p "${GPAW_ENV}" \
        mpiexec -n 4 gpaw python 02B_gpaw_convergence.py

    echo
    echo ">>> STEP 02C — Consolidação"
    run_in_upb_env structures python 02C_resumo.py

    echo
    echo "=============================================================================="
    echo "STEP 02 CONCLUÍDO"
    echo "=============================================================================="
} |& tee saida-step02.txt
