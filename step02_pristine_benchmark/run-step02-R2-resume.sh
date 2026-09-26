#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
source "${PROJECT_ROOT}/scripts/env_manager.sh"

require_upb_environment gpaw
require_upb_environment structures

cd "${SCRIPT_DIR}"

export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export PYTHONPATH="${SCRIPT_DIR}${PYTHONPATH:+:${PYTHONPATH}}"

MLIP_SUMMARY="${SCRIPT_DIR}/resultados_mlip/resumo_mlip.csv"

if [[ ! -f "${MLIP_SUMMARY}" ]]; then
    echo "ERRO: ${MLIP_SUMMARY} não encontrado." >&2
    echo "O Step 02A precisa estar concluído antes desta retomada." >&2
    exit 3
fi

{
    echo "=============================================================================="
    echo "STEP 02-R2 — RETOMADA GPAW COM DATASETS PAW PBE OFICIAIS"
    echo "=============================================================================="
    echo "Data: $(date)"
    echo "Host: $(hostname)"
    echo "Step 02A detectado: ${MLIP_SUMMARY}"
    echo "Step 02A NÃO será reexecutado."
    echo "XC da convergência numérica: PBE"
    echo "PAW datasets: PBE oficiais do GPAW"
    echo

    echo ">>> STEP 02B-R2 — GPAW/PBE (4 MPI)"
    GPAW_ENV="$(upb_env_path gpaw)"
    "${UPB_MICROMAMBA}" run \
        -r "${UPB_MAMBA_ROOT_PREFIX}" \
        -p "${GPAW_ENV}" \
        mpiexec -n 4 gpaw python "${SCRIPT_DIR}/02B_gpaw_convergence.py"

    echo
    echo ">>> STEP 02C — Consolidação"
    run_in_upb_env structures python "${SCRIPT_DIR}/02C_resumo.py"

    echo
    echo "=============================================================================="
    echo "STEP 02-R2 CONCLUÍDO"
    echo "=============================================================================="
} |& tee saida-step02-R2.txt
