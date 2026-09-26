#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

source "${PROJECT_ROOT}/scripts/env_manager.sh"

GPAW_ENV="$(upb_env_path gpaw)"

echo "============================================================"
echo "ETAPA 00 — VALIDAÇÃO FINAL GPAW/MPI"
echo "============================================================"

echo
echo "[1/3] Informação da instalação"
"${UPB_MICROMAMBA}" run     -r "${UPB_MAMBA_ROOT_PREFIX}"     -p "${GPAW_ENV}"     gpaw info

echo
echo "[2/3] Mundo MPI interno do GPAW — 4 processos"
"${UPB_MICROMAMBA}" run     -r "${UPB_MAMBA_ROOT_PREFIX}"     -p "${GPAW_ENV}"     mpiexec -n 4 gpaw python "${SCRIPT_DIR}/test_gpaw_mpi.py"

echo
echo "[3/3] Teste oficial GPAW em paralelo — 4 processos"
"${UPB_MICROMAMBA}" run     -r "${UPB_MAMBA_ROOT_PREFIX}"     -p "${GPAW_ENV}"     gpaw -P 4 test

echo
echo "============================================================"
echo "ETAPA 00 VALIDADA COM SUCESSO"
echo "============================================================"
