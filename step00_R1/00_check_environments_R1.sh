#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
source "${PROJECT_ROOT}/scripts/env_manager.sh"

echo "============================================================"
echo "VALIDAÇÃO R1 DOS AMBIENTES"
echo "============================================================"

echo
echo "[structures]"
run_in_upb_env structures python - <<'PY'
import sys, ase, requests, spglib, seekpath, numpy, scipy, pandas
from mp_api.client import MPRester
import pymatgen
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

echo
echo "[mlip]"
run_in_upb_env mlip python - <<'PY'
import sys, torch, chgnet, mace
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
    raise SystemExit("ERRO: PyTorch não reconheceu a GPU CUDA.")
PY

echo
echo "[gpaw]"
GPAW_ENV="$(upb_env_path gpaw)"
"${UPB_MICROMAMBA}" run -r "${UPB_MAMBA_ROOT_PREFIX}" -p "${GPAW_ENV}" gpaw info

echo
echo "Teste GPAW/MPI real com 4 processos:"
"${UPB_MICROMAMBA}" run -r "${UPB_MAMBA_ROOT_PREFIX}" -p "${GPAW_ENV}" \
    mpiexec -n 4 python - <<'PY'
from gpaw.mpi import world
print(f"GPAW rank={world.rank}/{world.size}", flush=True)
assert world.size == 4, f"GPAW world.size={world.size}; esperado 4."
PY

echo
echo "[analysis]"
run_in_upb_env analysis python - <<'PY'
import sys, numpy, scipy, pandas, matplotlib, phonopy, ase
print("Python:", sys.version.split()[0])
print("numpy:", numpy.__version__)
print("scipy:", scipy.__version__)
print("pandas:", pandas.__version__)
print("matplotlib:", matplotlib.__version__)
print("phonopy:", phonopy.__version__)
print("ASE:", ase.__version__)
PY

echo
echo "============================================================"
echo "VALIDAÇÃO R1 CONCLUÍDA"
echo "============================================================"
