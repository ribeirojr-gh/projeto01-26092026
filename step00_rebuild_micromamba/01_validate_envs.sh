#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
source "${PROJECT_ROOT}/scripts/env_manager.sh"
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1

echo "=============================================================================="
echo "VALIDAÇÃO DOS AMBIENTES RECRIADOS"
echo "=============================================================================="
run_in_upb_env structures python "${SCRIPT_DIR}/verify_structures.py"
run_in_upb_env analysis python "${SCRIPT_DIR}/verify_analysis.py"
run_in_upb_env mlip python "${SCRIPT_DIR}/verify_mlip.py"
run_in_upb_env gpaw gpaw info
GPAW_ENV="$(upb_env_path gpaw)"
"${UPB_MICROMAMBA}" run -r "${UPB_MAMBA_ROOT_PREFIX}" -p "${GPAW_ENV}"     mpiexec -n 4 gpaw python "${SCRIPT_DIR}/verify_gpaw_mpi.py"
run_in_upb_env gpaw gpaw -P 4 test

echo "=============================================================================="
echo "AMBIENTES MICROMAMBA VALIDADOS COM SUCESSO"
echo "=============================================================================="
