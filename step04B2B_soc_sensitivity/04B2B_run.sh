#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
source "${PROJECT_ROOT}/scripts/env_manager.sh"

RESULTS="${SCRIPT_DIR}/resultados_step04B2B"
LOGS="${SCRIPT_DIR}/logs"
GPW="${RESULTS}/gpw"
mkdir -p "${RESULTS}" "${LOGS}" "${GPW}"

echo "=============================================================================="
echo "STEP 04B2B — SENSIBILIDADE SOC PbCO3 + UO2"
echo "=============================================================================="
echo "Data: $(date)"
echo "Host: $(hostname)"
echo "Projeto: ${PROJECT_ROOT}"
echo

required=(
  "${PROJECT_ROOT}/step04B2A_pb_cerussite_validation/resultados_step04B2A/relax/PbCO3_relaxed_production.traj"
  "${PROJECT_ROOT}/step04B_compound_screening/estruturas/UO2_fluorite_exp.traj"
  "${PROJECT_ROOT}/step03_paw_pbesol_benchmark/paw_generated/PBEsol/O.PBEsol"
  "${PROJECT_ROOT}/step03_paw_pbesol_benchmark/paw_generated/PBEsol/C.PBEsol"
  "${PROJECT_ROOT}/step04_u_pb_paw_validation/paw_generated/Pb/PBEsol/Pb.PBEsol"
  "${PROJECT_ROOT}/step04_u_pb_paw_validation/paw_candidates/U_R5_pseudization/U14_nc6/PBEsol/U.PBEsol"
)
for f in "${required[@]}"; do
  [[ -s "${f}" ]] || { echo "ERRO: artefato ausente: ${f}"; exit 20; }
done

echo ">>> Ground state PbCO3"
run_in_upb_env gpaw env UPB_SOC_SYSTEM="PbCO3" \
  mpiexec -n 4 gpaw python "${SCRIPT_DIR}/04B2B_groundstates.py"

echo ">>> Ground state UO2"
run_in_upb_env gpaw env UPB_SOC_SYSTEM="UO2" \
  mpiexec -n 4 gpaw python "${SCRIPT_DIR}/04B2B_groundstates.py"

echo ">>> SOC PbCO3"
run_in_upb_env gpaw env UPB_SOC_SYSTEM="PbCO3" \
  mpiexec -n 4 gpaw python "${SCRIPT_DIR}/04B2B_soc_postprocess.py"

echo ">>> SOC UO2"
run_in_upb_env gpaw env UPB_SOC_SYSTEM="UO2" \
  mpiexec -n 4 gpaw python "${SCRIPT_DIR}/04B2B_soc_postprocess.py"

echo ">>> Decisão"
run_in_upb_env analysis python "${SCRIPT_DIR}/04B2B_decision.py"

echo "=============================================================================="
echo "STEP 04B2B FINALIZADO"
echo "=============================================================================="
