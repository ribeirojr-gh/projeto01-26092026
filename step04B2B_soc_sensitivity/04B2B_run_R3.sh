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
echo "STEP 04B2B-R3 — SOC DIRETO DO RAMO UO2 APROVADO"
echo "=============================================================================="
echo "Data: $(date)"
echo "Host: $(hostname)"
echo "Projeto: ${PROJECT_ROOT}"
echo

required=(
  "${PROJECT_ROOT}/step03_paw_pbesol_benchmark/paw_generated/PBEsol/O.PBEsol"
  "${PROJECT_ROOT}/step03_paw_pbesol_benchmark/paw_generated/PBEsol/C.PBEsol"
  "${PROJECT_ROOT}/step04_u_pb_paw_validation/paw_generated/Pb/PBEsol/Pb.PBEsol"
  "${PROJECT_ROOT}/step04_u_pb_paw_validation/paw_candidates/U_R5_pseudization/U14_nc6/PBEsol/U.PBEsol"
  "${PROJECT_ROOT}/step04B1B2_uo2_eos_R2/resultados_step04B1B2_R2/UO2_nc6_U3p0_center_1600.json"
  "${PROJECT_ROOT}/step04B1B2_uo2_eos_R2/resultados_step04B1B2_R2/restart/UO2_nc6_U3p0_center_1600_tight.gpw"
)

for f in "${required[@]}"; do
    [[ -s "${f}" ]] || {
        echo "ERRO: artefato obrigatório ausente: ${f}"
        exit 20
    }
done

PB_GPW="${GPW}/PbCO3_scalar_1600_k434_all.gpw"
PB_JSON="${RESULTS}/PbCO3_scalar_groundstate.json"

if [[ ! -s "${PB_GPW}" || ! -s "${PB_JSON}" ]]; then
    echo ">>> PbCO3 escalar ausente; recalculando"
    run_in_upb_env gpaw env \
      UPB_SOC_SYSTEM="PbCO3" \
      mpiexec -n 4 gpaw python \
      "${SCRIPT_DIR}/04B2B_groundstates.py"
else
    echo ">>> Reutilizando PbCO3 escalar já convergido"
fi

echo
echo ">>> Registrando metadados do RAMO UO2 APROVADO"
run_in_upb_env analysis python \
  "${SCRIPT_DIR}/04B2B_prepare_reference_metadata_R3.py"

echo
echo ">>> SOC PbCO3"
run_in_upb_env gpaw env \
  UPB_SOC_SYSTEM="PbCO3" \
  mpiexec -n 4 gpaw python \
  "${SCRIPT_DIR}/04B2B_soc_postprocess.py"

echo
echo ">>> SOC UO2 diretamente do .gpw aprovado do B1B2-R2"
run_in_upb_env gpaw env \
  UPB_SOC_SYSTEM="UO2" \
  mpiexec -n 4 gpaw python \
  "${SCRIPT_DIR}/04B2B_soc_postprocess.py"

echo
echo ">>> Decisão"
run_in_upb_env analysis python \
  "${SCRIPT_DIR}/04B2B_decision.py"

echo "=============================================================================="
echo "STEP 04B2B-R3 FINALIZADO"
echo "=============================================================================="
