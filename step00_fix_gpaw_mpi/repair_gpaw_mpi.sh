#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

MICROMAMBA="${PROJECT_ROOT}/.tools/micromamba"
MAMBA_ROOT="${PROJECT_ROOT}/.micromamba"
GPAW_ENV="${PROJECT_ROOT}/.envs/gpaw"

export MAMBA_ROOT_PREFIX="${MAMBA_ROOT}"
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1

[[ -x "${MICROMAMBA}" ]] || {
    echo "ERRO: micromamba não encontrado em ${MICROMAMBA}" >&2
    exit 2
}

[[ -x "${GPAW_ENV}/bin/python" ]] || {
    echo "ERRO: ambiente GPAW não encontrado em ${GPAW_ENV}" >&2
    exit 3
}

echo "=============================================================================="
echo "CORREÇÃO GPAW MPI — TROCA DO BUILD nompi PELO mpi_openmpi"
echo "=============================================================================="
echo "Projeto: ${PROJECT_ROOT}"
echo "Ambiente: ${GPAW_ENV}"
echo

echo ">>> Pacotes GPAW/MPI ANTES da correção"
"${MICROMAMBA}" list -p "${GPAW_ENV}" | grep -E '^(gpaw|gpaw-data|mpi |mpi4py|openmpi)' || true

echo
echo ">>> Instalando build MPI explícito do GPAW 25.7.0"
echo "    gpaw=25.7.0=py311_mpi_openmpi_omp_3"
echo

"${MICROMAMBA}" install -y \
    -r "${MAMBA_ROOT}" \
    -p "${GPAW_ENV}" \
    -c conda-forge \
    --strict-channel-priority \
    "gpaw=25.7.0=py311_mpi_openmpi_omp_3" \
    "gpaw-data=1.0.1" \
    "mpi=1.0=openmpi" \
    openmpi \
    mpi4py

echo
echo ">>> Pacotes GPAW/MPI DEPOIS da correção"
"${MICROMAMBA}" list -p "${GPAW_ENV}" | grep -E '^(gpaw|gpaw-data|mpi |mpi4py|openmpi)' || true

echo
echo ">>> gpaw info"
"${MICROMAMBA}" run \
    -r "${MAMBA_ROOT}" \
    -p "${GPAW_ENV}" \
    gpaw info

echo
echo ">>> Teste MPI real com 4 processos"
"${MICROMAMBA}" run \
    -r "${MAMBA_ROOT}" \
    -p "${GPAW_ENV}" \
    mpiexec -n 4 gpaw python "${SCRIPT_DIR}/verify_gpaw_mpi.py"

echo
echo ">>> Teste oficial GPAW em paralelo"
"${MICROMAMBA}" run \
    -r "${MAMBA_ROOT}" \
    -p "${GPAW_ENV}" \
    gpaw -P 4 test

echo
echo "=============================================================================="
echo "GPAW MPI CORRIGIDO E VALIDADO"
echo "=============================================================================="
