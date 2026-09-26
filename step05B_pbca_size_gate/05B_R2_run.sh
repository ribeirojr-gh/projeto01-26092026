#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
source "${PROJECT_ROOT}/scripts/env_manager.sh"
RESULTS="${SCRIPT_DIR}/resultados_step05B_R2"
mkdir -p "${RESULTS}" "${SCRIPT_DIR}/logs_R2" "${RESULTS}/relax"

echo "=============================================================================="
echo "STEP 05B-R2 — GAMMA-CALIBRATED MEMORY-SAFE SIZE GATE"
echo "=============================================================================="
echo "Data: $(date)"
echo "Host: $(hostname)"
echo "Projeto: ${PROJECT_ROOT}"
echo

run_case() {
 local mineral="$1"; local natoms="$2"
 local j="${RESULTS}/${mineral}_${natoms}_PbCa.json"
 local t="${RESULTS}/relax/${mineral}_${natoms}_PbCa_relaxed_R2.traj"
 if [[ -s "${j}" && -s "${t}" ]]; then echo ">>> Reutilizando ${mineral} ${natoms}"; return; fi
 echo
 echo ">>> ${mineral}: Pb_Ca ${natoms} átomos"
 run_in_upb_env gpaw env UPB_PBCA_HOST="${mineral}" UPB_PBCA_NATOMS="${natoms}" \
   mpiexec -n 4 gpaw python "${SCRIPT_DIR}/05B_R2_pbca_case.py"
}

for mineral in calcita dolomita; do
 run_case "${mineral}" 80
 run_case "${mineral}" 160
done

echo
echo ">>> Análise 80 -> 160"
run_in_upb_env analysis python "${SCRIPT_DIR}/05B_R2_analyze.py" --phase initial

mapfile -t fallback_hosts < <(
 run_in_upb_env analysis python -c '
import json
from pathlib import Path
p=Path("'"${RESULTS}"'")/"fallback_request_step05B_R2.json"
for x in json.loads(p.read_text())["fallback_hosts"]: print(x)
'
)

if (( ${#fallback_hosts[@]} > 0 )); then
 echo ">>> Fallback 240 necessário para: ${fallback_hosts[*]}"
 for mineral in "${fallback_hosts[@]}"; do run_case "${mineral}" 240; done
else
 echo ">>> 80 -> 160 convergiu para ambos; 240 não será calculado."
fi

echo
echo ">>> Decisão final"
run_in_upb_env analysis python "${SCRIPT_DIR}/05B_R2_analyze.py" --phase final
echo "=============================================================================="
echo "STEP 05B-R2 FINALIZADO"
echo "=============================================================================="
