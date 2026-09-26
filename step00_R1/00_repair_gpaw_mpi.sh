#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

MICROMAMBA="${PROJECT_ROOT}/.tools/micromamba"
MAMBA_ROOT_PREFIX="${PROJECT_ROOT}/.micromamba"
ENVS_ROOT="${PROJECT_ROOT}/.envs"
GPAW_ENV="${ENVS_ROOT}/gpaw"

export MAMBA_ROOT_PREFIX

log() {
    printf '[STEP00-R1] %s\n' "$*"
}

die() {
    printf '[STEP00-R1][ERRO] %s\n' "$*" >&2
    exit 1
}

[[ -x "${MICROMAMBA}" ]] || die \
    "micromamba não encontrado em ${MICROMAMBA}. Execute primeiro a Etapa 00 original."

log "Esta correção NÃO reinstala structures, mlip ou analysis."
log "Somente o ambiente GPAW será reconstruído para garantir suporte MPI real."

if [[ -d "${GPAW_ENV}" ]]; then
    log "Removendo ambiente GPAW anterior: ${GPAW_ENV}"
    rm -rf "${GPAW_ENV}"
fi

log "Criando GPAW com variante MPI/OpenMPI..."
"${MICROMAMBA}" create -y \
    -r "${MAMBA_ROOT_PREFIX}" \
    -p "${GPAW_ENV}" \
    -c conda-forge \
    --strict-channel-priority \
    "python=3.11" \
    "gpaw=*=*mpi_openmpi*" \
    gpaw-data \
    ase \
    numpy \
    scipy \
    matplotlib \
    "mpi=1.0=openmpi" \
    openmpi \
    mpi4py

log "Ambiente GPAW MPI criado."
log "Executando diagnóstico detalhado..."

"${MICROMAMBA}" run -r "${MAMBA_ROOT_PREFIX}" -p "${GPAW_ENV}" gpaw info

echo
log "Teste do mundo MPI interno do GPAW com 4 processos:"
"${MICROMAMBA}" run -r "${MAMBA_ROOT_PREFIX}" -p "${GPAW_ENV}" \
    mpiexec -n 4 python - <<'PY'
from gpaw.mpi import world

print(f"GPAW rank={world.rank}/{world.size}", flush=True)

if world.size != 4:
    raise SystemExit(
        f"ERRO: GPAW foi iniciado com world.size={world.size}; esperado 4. "
        "A instalação ainda não possui MPI funcional."
    )
PY

echo
log "Executando teste oficial serial do GPAW..."
"${MICROMAMBA}" run -r "${MAMBA_ROOT_PREFIX}" -p "${GPAW_ENV}" \
    gpaw test

echo
log "Executando teste oficial paralelo do GPAW com 4 processos..."
"${MICROMAMBA}" run -r "${MAMBA_ROOT_PREFIX}" -p "${GPAW_ENV}" \
    mpiexec -n 4 gpaw test

echo
log "Validação final do GPAW MPI concluída com sucesso."
