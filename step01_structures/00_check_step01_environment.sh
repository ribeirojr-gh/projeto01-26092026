#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
source "${PROJECT_ROOT}/scripts/env_manager.sh"

require_upb_environment structures

echo "============================================================"
echo "DIAGNÓSTICO DO AMBIENTE — ETAPA 01"
echo "============================================================"

run_in_upb_env structures python - <<'PY'
import sys
import ase
import numpy
import pandas
import requests
import scipy
import seekpath
import spglib
import pymatgen
from mp_api.client import MPRester

print("Python executável:", sys.executable)
print("Python versão:", sys.version.split()[0])
print("ASE:", ase.__version__)
print("pymatgen: OK")
print("mp-api: OK")
print("NumPy:", numpy.__version__)
print("SciPy:", scipy.__version__)
print("pandas:", pandas.__version__)
print("requests:", requests.__version__)
print("spglib:", spglib.__version__)
print("seekpath:", seekpath.__version__)
PY

echo "============================================================"
echo "AMBIENTE structures: OK"
echo "============================================================"
