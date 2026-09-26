#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
source "${PROJECT_ROOT}/scripts/env_manager.sh"

GPAW_ENV="$(upb_env_path gpaw)"

echo "============================================================"
echo "ETAPA 00-R2 — Validação corrigida do GPAW/MPI"
echo "============================================================"

echo
echo "[1/4] gpaw info"
"${UPB_MICROMAMBA}" run \
    -r "${UPB_MAMBA_ROOT_PREFIX}" \
    -p "${GPAW_ENV}" \
    gpaw info

echo
echo "[2/4] Teste MPI interno do GPAW com 4 processos"
# IMPORTANTE:
# não usar "python -" + heredoc sob mpiexec.
# Open MPI encaminha stdin, por padrão, apenas ao rank 0.
# Todos os ranks leem o mesmo arquivo físico abaixo.
"${UPB_MICROMAMBA}" run \
    -r "${UPB_MAMBA_ROOT_PREFIX}" \
    -p "${GPAW_ENV}" \
    mpiexec -n 4 gpaw python "${SCRIPT_DIR}/00_test_gpaw_mpi.py"

echo
echo "[3/4] Teste GPAW serial"
"${UPB_MICROMAMBA}" run \
    -r "${UPB_MAMBA_ROOT_PREFIX}" \
    -p "${GPAW_ENV}" \
    gpaw test

echo
echo "[4/4] Teste GPAW paralelo com 4 processos"
"${UPB_MICROMAMBA}" run \
    -r "${UPB_MAMBA_ROOT_PREFIX}" \
    -p "${GPAW_ENV}" \
    mpiexec -n 4 gpaw python -m pytest --pyargs gpaw -q

echo
echo "============================================================"
echo "ETAPA 00-R2 CONCLUÍDA"
echo "============================================================"
