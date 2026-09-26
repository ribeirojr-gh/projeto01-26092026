#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
MICROMAMBA="${PROJECT_ROOT}/.tools/micromamba"
MAMBA_ROOT="${PROJECT_ROOT}/.micromamba"
ENVS_ROOT="${PROJECT_ROOT}/.envs"
TOOLS_DIR="${PROJECT_ROOT}/.tools"
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1

timestamp="$(date +%Y%m%d-%H%M%S)"
backup_root="${PROJECT_ROOT}/backup_envs_${timestamp}"

echo "=============================================================================="
echo "RECONSTRUÇÃO DOS AMBIENTES MICROMAMBA NO PREFIXO ATUAL"
echo "=============================================================================="
echo "Projeto: ${PROJECT_ROOT}"
echo "Backup:  ${backup_root}"
mkdir -p "${TOOLS_DIR}"

if [[ ! -x "${MICROMAMBA}" ]]; then
    echo "[MICROMAMBA] Binário não encontrado; instalando cópia relocável..."
    tmpdir="$(mktemp -d)"
    trap 'rm -rf "${tmpdir}"' EXIT
    curl -Ls https://micro.mamba.pm/api/micromamba/linux-64/latest | tar -xj -C "${tmpdir}" bin/micromamba
    cp "${tmpdir}/bin/micromamba" "${MICROMAMBA}"
    chmod +x "${MICROMAMBA}"
fi

echo "[MICROMAMBA] $("${MICROMAMBA}" --version)"

if [[ -d "${ENVS_ROOT}" || -d "${MAMBA_ROOT}" ]]; then
    mkdir -p "${backup_root}"
    [[ ! -d "${ENVS_ROOT}" ]] || mv "${ENVS_ROOT}" "${backup_root}/.envs"
    [[ ! -d "${MAMBA_ROOT}" ]] || mv "${MAMBA_ROOT}" "${backup_root}/.micromamba"
fi
mkdir -p "${ENVS_ROOT}" "${MAMBA_ROOT}"
export MAMBA_ROOT_PREFIX="${MAMBA_ROOT}"

create_env() {
    local name="$1"; shift
    local prefix="${ENVS_ROOT}/${name}"
    echo "[ENV] Criando ${name}: ${prefix}"
    "${MICROMAMBA}" create -y -r "${MAMBA_ROOT}" -p "${prefix}" -c conda-forge "$@"
}

create_env structures "python=3.11" "ase=3.29.0" pymatgen mp-api requests spglib seekpath numpy scipy pandas pyyaml
create_env analysis "python=3.11" "ase=3.29.0" numpy scipy pandas matplotlib h5py pyyaml tqdm uncertainties phonopy spglib seekpath
create_env mlip "python=3.11" pip "ase=3.29.0" numpy scipy pymatgen

MLIP_PY="${ENVS_ROOT}/mlip/bin/python"
if command -v nvidia-smi >/dev/null 2>&1 && nvidia-smi >/dev/null 2>&1; then
    TORCH_INDEX="${UPB_TORCH_INDEX:-https://download.pytorch.org/whl/cu130}"
    echo "[MLIP] GPU NVIDIA detectada."
else
    TORCH_INDEX="${UPB_TORCH_INDEX:-https://download.pytorch.org/whl/cpu}"
    echo "[MLIP] GPU NVIDIA não detectada; usando PyTorch CPU."
fi
"${MLIP_PY}" -m pip install --upgrade --index-url "${TORCH_INDEX}" "torch==2.13.0"
"${MLIP_PY}" -m pip install --upgrade "chgnet==0.4.2" "mace-torch==0.3.16"

GPAW_PREFIX="${ENVS_ROOT}/gpaw"
set +e
"${MICROMAMBA}" create -y -r "${MAMBA_ROOT}" -p "${GPAW_PREFIX}" -c conda-forge     "python=3.11" "gpaw=25.7.0=*mpi*" "gpaw-data=1.0.1" "ase=3.29.0"     numpy scipy matplotlib mpi4py openmpi libxc fftw scalapack elpa libvdwxc
gpaw_status=$?
set -e
if [[ ${gpaw_status} -ne 0 ]]; then
    echo "[GPAW] Matchspec '*mpi*' não resolvido; tentando solver geral."
    rm -rf "${GPAW_PREFIX}"
    "${MICROMAMBA}" create -y -r "${MAMBA_ROOT}" -p "${GPAW_PREFIX}" -c conda-forge         "python=3.11" "gpaw=25.7.0" "gpaw-data=1.0.1" "ase=3.29.0"         numpy scipy matplotlib mpi4py openmpi libxc fftw scalapack elpa libvdwxc
fi

echo "RECONSTRUÇÃO CONCLUÍDA"
