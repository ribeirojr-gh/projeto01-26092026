#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

MICROMAMBA="${PROJECT_ROOT}/.tools/micromamba"
GPAW_ENV="${PROJECT_ROOT}/.envs/gpaw"

if [[ ! -x "${MICROMAMBA}" ]]; then
    echo "ERRO: micromamba não encontrado em ${MICROMAMBA}"
    exit 10
fi

if [[ ! -d "${GPAW_ENV}" ]]; then
    echo "ERRO: ambiente GPAW não encontrado em ${GPAW_ENV}"
    exit 11
fi

echo "=============================================================================="
echo "STEP 04B2C2-R1 — CORREÇÃO DA DEPENDÊNCIA spglib NO AMBIENTE GPAW"
echo "=============================================================================="
echo "Data: $(date)"
echo "Host: $(hostname)"
echo "Projeto: ${PROJECT_ROOT}"
echo

echo ">>> Verificando spglib no ambiente GPAW"

if "${MICROMAMBA}" run -p "${GPAW_ENV}" python -c 'import spglib; print("spglib", spglib.__version__)'; then
    echo "spglib já disponível no ambiente GPAW."
else
    echo
    echo "spglib ausente. Instalando via micromamba/conda-forge..."
    "${MICROMAMBA}" install -y         -p "${GPAW_ENV}"         -c conda-forge         spglib

    echo
    echo ">>> Validando instalação"
    "${MICROMAMBA}" run -p "${GPAW_ENV}" python -c 'import spglib; print("spglib", spglib.__version__)'
fi

echo
echo ">>> Iniciando Step04B2C2 original após correção do ambiente"
bash "${SCRIPT_DIR}/04B2C2_run.sh"
