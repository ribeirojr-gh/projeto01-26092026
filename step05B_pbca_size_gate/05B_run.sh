#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
source "${PROJECT_ROOT}/scripts/env_manager.sh"
RESULTS="${SCRIPT_DIR}/resultados_step05B"
mkdir -p "${RESULTS}" "${SCRIPT_DIR}/logs" "${RESULTS}/relax"

echo "=============================================================================="
echo "STEP 05B — GATE DE TAMANHO Pb2+_Ca NEUTRO"
echo "=============================================================================="
echo "Data: $(date)"
echo "Host: $(hostname)"
echo "Projeto: ${PROJECT_ROOT}"
echo

required=(
 "${PROJECT_ROOT}/step05A_host_supercells/resultados_step05A/decisao_step05A_R1.json"
 "${PROJECT_ROOT}/step05A_host_supercells/resultados_step05A/supercells_R1/calcita_det8_80atoms_R1.traj"
 "${PROJECT_ROOT}/step05A_host_supercells/resultados_step05A/supercells_R1/calcita_det16_160atoms_R1.traj"
 "${PROJECT_ROOT}/step05A_host_supercells/resultados_step05A/supercells_R1/calcita_det24_240atoms_R1.traj"
 "${PROJECT_ROOT}/step05A_host_supercells/resultados_step05A/supercells_R1/dolomita_det8_80atoms_R1.traj"
 "${PROJECT_ROOT}/step05A_host_supercells/resultados_step05A/supercells_R1/dolomita_det16_160atoms_R1.traj"
 "${PROJECT_ROOT}/step05A_host_supercells/resultados_step05A/supercells_R1/dolomita_det24_240atoms_R1.traj"
 "${PROJECT_ROOT}/step03_paw_pbesol_benchmark/paw_generated/PBEsol/Ca.PBEsol"
 "${PROJECT_ROOT}/step03_paw_pbesol_benchmark/paw_generated/PBEsol/Mg.PBEsol"
 "${PROJECT_ROOT}/step03_paw_pbesol_benchmark/paw_generated/PBEsol/C.PBEsol"
 "${PROJECT_ROOT}/step03_paw_pbesol_benchmark/paw_generated/PBEsol/O.PBEsol"
 "${PROJECT_ROOT}/step04_u_pb_paw_validation/paw_generated/Pb/PBEsol/Pb.PBEsol"
)
for f in "${required[@]}"; do [[ -s "${f}" ]] || { echo "ERRO: ausente ${f}"; exit 20; }; done

run_case() {
 local mineral="$1"; local natoms="$2"
 local j="${RESULTS}/${mineral}_${natoms}_PbCa.json"
 local t="${RESULTS}/relax/${mineral}_${natoms}_PbCa_relaxed.traj"
 if [[ -s "${j}" && -s "${t}" ]]; then
   echo ">>> Reutilizando ${mineral} ${natoms}"
   return
 fi
 echo
 echo ">>> ${mineral}: Pb_Ca em ${natoms} átomos"
 run_in_upb_env gpaw env UPB_PBCA_HOST="${mineral}" UPB_PBCA_NATOMS="${natoms}" \
   mpiexec -n 4 gpaw python "${SCRIPT_DIR}/05B_pbca_case.py"
}

for mineral in calcita dolomita; do
 run_case "${mineral}" 80
 run_case "${mineral}" 160
done

echo
echo ">>> Análise 80 -> 160"
run_in_upb_env analysis python "${SCRIPT_DIR}/05B_analyze.py" --phase initial

mapfile -t fallback_hosts < <(
 run_in_upb_env analysis python -c '
import json
from pathlib import Path
p=Path("'"${RESULTS}"'")/"fallback_request_step05B.json"
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
run_in_upb_env analysis python "${SCRIPT_DIR}/05B_analyze.py" --phase final
echo "=============================================================================="
echo "STEP 05B FINALIZADO"
echo "=============================================================================="
