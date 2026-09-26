#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
source "${PROJECT_ROOT}/scripts/env_manager.sh"

section() {
    printf '\n============================================================\n'
    printf '%s\n' "$1"
    printf '============================================================\n'
}

section "AMBIENTE structures"
run_in_upb_env structures python - <<'PY'
import sys
import ase
import pymatgen
import requests
import spglib
import seekpath
import numpy
import scipy
import pandas
from mp_api.client import MPRester

print("Python:", sys.version.split()[0])
print("ASE:", ase.__version__)
print("pymatgen: OK")
print("mp-api: OK")
print("requests:", requests.__version__)
print("spglib:", spglib.__version__)
print("seekpath:", seekpath.__version__)
print("numpy:", numpy.__version__)
print("scipy:", scipy.__version__)
print("pandas:", pandas.__version__)
PY

section "AMBIENTE mlip"
run_in_upb_env mlip python - <<'PY'
import sys
import torch
import chgnet
import mace

print("Python:", sys.version.split()[0])
print("PyTorch:", torch.__version__)
print("CHGNet:", getattr(chgnet, "__version__", "import OK"))
print("MACE:", getattr(mace, "__version__", "import OK"))
print("CUDA disponível:", torch.cuda.is_available())
print("CUDA do PyTorch:", torch.version.cuda)

if torch.cuda.is_available():
    print("GPU:", torch.cuda.get_device_name(0))
    print("Compute capability:", torch.cuda.get_device_capability(0))
else:
    print("AVISO: PyTorch não está vendo uma GPU CUDA; MLIP funcionará em CPU.")
PY

section "AMBIENTE gpaw"
run_in_upb_env gpaw python - <<'PY'
import sys
import ase
import gpaw
from mpi4py import MPI

print("Python:", sys.version.split()[0])
print("ASE:", ase.__version__)
print("GPAW:", gpaw.__version__)
print("mpi4py: OK")
print("MPI world size nesta checagem serial:", MPI.COMM_WORLD.Get_size())
PY

echo
echo "Teste MPI do GPAW com 4 processos:"
GPAW_ENV="$(upb_env_path gpaw)"
"${UPB_MICROMAMBA}" run -r "${UPB_MAMBA_ROOT_PREFIX}" -p "${GPAW_ENV}" \
    mpiexec -n 4 python -c \
    'from mpi4py import MPI; import gpaw; print(f"rank={MPI.COMM_WORLD.rank}/{MPI.COMM_WORLD.size} gpaw={gpaw.__version__}")'

section "AMBIENTE analysis"
run_in_upb_env analysis python - <<'PY'
import sys
import numpy
import scipy
import pandas
import matplotlib
import phonopy
import ase

print("Python:", sys.version.split()[0])
print("numpy:", numpy.__version__)
print("scipy:", scipy.__version__)
print("pandas:", pandas.__version__)
print("matplotlib:", matplotlib.__version__)
print("phonopy:", phonopy.__version__)
print("ASE:", ase.__version__)
PY

section "DIAGNÓSTICO FINAL"
if command -v nvidia-smi >/dev/null 2>&1; then
    nvidia-smi || true
else
    echo "nvidia-smi não encontrado."
fi

echo
echo "Todos os imports e testes básicos foram executados."
