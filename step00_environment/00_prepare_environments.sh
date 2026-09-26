#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

TOOLS_DIR="${PROJECT_ROOT}/.tools"
MICROMAMBA="${TOOLS_DIR}/micromamba"
MAMBA_ROOT_PREFIX="${PROJECT_ROOT}/.micromamba"
ENVS_ROOT="${PROJECT_ROOT}/.envs"

export MAMBA_ROOT_PREFIX

FORCE=0
for arg in "$@"; do
    case "${arg}" in
        --force) FORCE=1 ;;
        *)
            echo "Uso: $0 [--force]" >&2
            exit 2
            ;;
    esac
done

log() {
    printf '[STEP00] %s\n' "$*"
}

die() {
    printf '[STEP00][ERRO] %s\n' "$*" >&2
    exit 1
}

download_micromamba() {
    if [[ -x "${MICROMAMBA}" ]]; then
        log "micromamba já instalado: ${MICROMAMBA}"
        return
    fi

    mkdir -p "${TOOLS_DIR}"

    local arch platform tmpdir
    arch="$(uname -m)"
    case "${arch}" in
        x86_64|amd64) platform="linux-64" ;;
        aarch64|arm64) platform="linux-aarch64" ;;
        *) die "Arquitetura Linux não suportada automaticamente: ${arch}" ;;
    esac

    command -v tar >/dev/null 2>&1 || die "O comando 'tar' é necessário."

    tmpdir="$(mktemp -d)"
    trap 'rm -rf "${tmpdir}"' RETURN

    log "Instalando micromamba localmente (${platform})..."

    if command -v curl >/dev/null 2>&1; then
        curl -Ls "https://micro.mamba.pm/api/micromamba/${platform}/latest" \
            | tar -xj -C "${tmpdir}" bin/micromamba
    elif command -v wget >/dev/null 2>&1; then
        wget -qO- "https://micro.mamba.pm/api/micromamba/${platform}/latest" \
            | tar -xj -C "${tmpdir}" bin/micromamba
    else
        die "É necessário ter 'curl' ou 'wget' disponível para baixar o micromamba."
    fi

    install -m 0755 "${tmpdir}/bin/micromamba" "${MICROMAMBA}"
    log "micromamba instalado em ${MICROMAMBA}"
}

maybe_remove_env() {
    local env_path="${1:?}"
    if [[ "${FORCE}" -eq 1 && -d "${env_path}" ]]; then
        log "--force: removendo ${env_path}"
        rm -rf "${env_path}"
    fi
}

create_conda_env() {
    local name="${1:?}"
    shift
    local env_path="${ENVS_ROOT}/${name}"

    maybe_remove_env "${env_path}"

    if [[ -x "${env_path}/bin/python" ]]; then
        log "Ambiente '${name}' já existe; mantendo instalação atual."
        return
    fi

    log "Criando ambiente '${name}'..."
    "${MICROMAMBA}" create -y -r "${MAMBA_ROOT_PREFIX}" -p "${env_path}" \
        -c conda-forge --strict-channel-priority "$@"
}

pip_in_env() {
    local name="${1:?}"
    shift
    local env_path="${ENVS_ROOT}/${name}"
    "${MICROMAMBA}" run -r "${MAMBA_ROOT_PREFIX}" -p "${env_path}" \
        python -m pip "$@"
}

install_structures_env() {
    create_conda_env structures \
        "python=3.11" pip \
        ase pymatgen mp-api requests \
        spglib seekpath \
        numpy scipy pandas pyyaml

    pip_in_env structures install --upgrade pip setuptools wheel
}

install_analysis_env() {
    create_conda_env analysis \
        "python=3.11" pip \
        ase numpy scipy pandas matplotlib \
        h5py pyyaml tqdm uncertainties \
        phonopy spglib seekpath

    pip_in_env analysis install --upgrade pip setuptools wheel
}

install_gpaw_env() {
    create_conda_env gpaw \
        "python=3.11" \
        gpaw gpaw-data ase \
        numpy scipy matplotlib \
        mpi4py openmpi \
        libxc fftw

    # O pacote conda-forge de GPAW traz a pilha binária e os dados PAW.
    # Não misturamos pip/conda no núcleo do GPAW para reduzir problemas ABI.
}

install_mlip_env() {
    create_conda_env mlip \
        "python=3.11" pip \
        ase pymatgen \
        numpy scipy pandas

    pip_in_env mlip install --upgrade pip setuptools wheel

    # PyTorch: o wheel estável atual é instalado via pip.
    # Em máquinas sem GPU NVIDIA funcional, ele continua utilizável em CPU.
    log "Instalando/atualizando PyTorch no ambiente MLIP..."
    pip_in_env mlip install --upgrade torch

    log "Instalando/atualizando CHGNet e MACE..."
    pip_in_env mlip install --upgrade chgnet mace-torch
}

main() {
    if [[ "$(uname -s)" != "Linux" ]]; then
        die "Este instalador foi preparado para Linux. Sistema detectado: $(uname -s)"
    fi

    mkdir -p "${TOOLS_DIR}" "${MAMBA_ROOT_PREFIX}" "${ENVS_ROOT}"

    log "Projeto: ${PROJECT_ROOT}"
    log "Python padrão dos ambientes: 3.11"
    log "Os ambientes serão instalados dentro do próprio projeto."
    log "Nenhuma instalação Conda global é necessária."

    if command -v nvidia-smi >/dev/null 2>&1; then
        log "GPU/driver NVIDIA detectados:"
        nvidia-smi --query-gpu=name,driver_version,memory.total \
            --format=csv,noheader || true
    else
        log "nvidia-smi não encontrado. O ambiente MLIP será instalado, mas a GPU não poderá ser validada agora."
    fi

    download_micromamba

    install_structures_env
    install_mlip_env
    install_gpaw_env
    install_analysis_env

    log "Todos os ambientes foram preparados."
    log "Executando validação..."
    "${SCRIPT_DIR}/00_check_environments.sh"

    cat <<EOF

======================================================================
ETAPA 00 CONCLUÍDA
======================================================================
Ambientes:
  structures : ${ENVS_ROOT}/structures
  mlip       : ${ENVS_ROOT}/mlip
  gpaw       : ${ENVS_ROOT}/gpaw
  analysis   : ${ENVS_ROOT}/analysis

Os scripts run-stepXX.sh carregarão os ambientes automaticamente via:
  ${PROJECT_ROOT}/scripts/env_manager.sh

Não é necessário executar 'conda activate' ou 'micromamba activate'.
======================================================================
EOF
}

main "$@"
