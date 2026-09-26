#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
source "${PROJECT_ROOT}/scripts/env_manager.sh"

RESULTS="${SCRIPT_DIR}/resultados_step04B1A_R5"
LOGS="${SCRIPT_DIR}/logs/R5"
GPW="${RESULTS}/gpw"
mkdir -p "${RESULTS}" "${LOGS}" "${GPW}"

echo "=============================================================================="
echo "STEP 04B1A-R5 — UO2: GRADE Ueff SOB PROTOCOLO COMUM"
echo "=============================================================================="
echo "Data: $(date)"
echo "Host: $(hostname)"
echo "Projeto: ${PROJECT_ROOT}"

required=(
  "${SCRIPT_DIR}/estruturas/UO2_fluorite_exp.traj"
  "${PROJECT_ROOT}/step03_paw_pbesol_benchmark/paw_generated/PBEsol/O.PBEsol"
  "${PROJECT_ROOT}/step04_u_pb_paw_validation/paw_generated/U/PBEsol/U.PBEsol"
  "${PROJECT_ROOT}/step04_u_pb_paw_validation/paw_candidates/U_R5_pseudization/U14_nc6/PBEsol/U.PBEsol"
)
for f in "${required[@]}"; do
  [[ -s "${f}" ]] || { echo "ERRO: artefato ausente: ${f}"; exit 20; }
done

json_ok() {
  python3 - "$1" <<'PY'
import json, sys
from pathlib import Path
p = Path(sys.argv[1])
if not p.exists():
    raise SystemExit(1)
try:
    d = json.loads(p.read_text())
except Exception:
    raise SystemExit(1)
raise SystemExit(0 if d.get("status") == "converged" else 1)
PY
}

for dataset in poly6 nc6; do
  for ueff in 0.0 2.0 3.0 4.0 5.0; do
    tag="UO2_${dataset}_Ueff_${ueff/./p}"
    out="${RESULTS}/${tag}.json"
    echo
    if json_ok "${out}"; then
      echo "[R5] reutilizando ${out}"
      continue
    fi
    rm -f "${out}"
    echo "[R5] ${tag}"
    run_in_upb_env gpaw env \
      UPB_R5_DATASET="${dataset}" \
      UPB_R5_UEFF="${ueff}" \
      UPB_R5_OUT="${out}" \
      UPB_R5_TXT_DIR="${LOGS}" \
      UPB_R5_GPW_DIR="${GPW}" \
      mpiexec -n 4 gpaw python "${SCRIPT_DIR}/04B1A_UO2_grid_R5.py"
  done
done

echo
echo ">>> Pós-processamento"
run_in_upb_env gpaw python "${SCRIPT_DIR}/04B1A_postprocess_R5.py"
echo "=============================================================================="
echo "STEP 04B1A-R5 FINALIZADO"
echo "=============================================================================="
