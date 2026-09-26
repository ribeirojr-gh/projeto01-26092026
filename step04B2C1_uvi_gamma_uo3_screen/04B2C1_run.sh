#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
source "${PROJECT_ROOT}/scripts/env_manager.sh"

RESULTS="${SCRIPT_DIR}/resultados_step04B2C1"
LOGS="${SCRIPT_DIR}/logs"
GPW="${RESULTS}/gpw"
mkdir -p "${RESULTS}" "${LOGS}" "${GPW}"

echo "=============================================================================="
echo "STEP 04B2C1 — U(VI) / gamma-UO3 Fddd (293 K)"
echo "=============================================================================="
echo "Data: $(date)"
echo "Host: $(hostname)"
echo "Projeto: ${PROJECT_ROOT}"
echo

required=(
  "${PROJECT_ROOT}/step03_paw_pbesol_benchmark/paw_generated/PBEsol/O.PBEsol"
  "${PROJECT_ROOT}/step04_u_pb_paw_validation/paw_candidates/U_R5_pseudization/U14_nc6/PBEsol/U.PBEsol"
)
for f in "${required[@]}"; do
  [[ -s "${f}" ]] || { echo "ERRO: artefato ausente: ${f}"; exit 20; }
done

echo ">>> Preparação e validação da estrutura COD 1527742"
run_in_upb_env structures python \
  "${SCRIPT_DIR}/04B2C1_prepare_structure.py"

run_case() {
  local case="$1"
  local ueff="$2"
  local ecut="$3"
  local kpts="$4"
  local spin="$5"
  local tag="$6"

  echo
  echo "[B2C1] ${case}"

  run_in_upb_env gpaw env \
    UPB_UVI_CASE="${case}" \
    UPB_UVI_UEFF="${ueff}" \
    UPB_UVI_ECUT="${ecut}" \
    UPB_UVI_KPTS="${kpts}" \
    UPB_UVI_SPIN="${spin}" \
    UPB_UVI_OUT="${RESULTS}/${tag}.json" \
    UPB_UVI_TXT="${LOGS}/${tag}.txt" \
    UPB_UVI_GPW="${GPW}/${tag}.gpw" \
    mpiexec -n 4 gpaw python \
      "${SCRIPT_DIR}/04B2C1_calculate.py"
}

run_case "U0_NM_1600_k222" 0.0 1600 "2,2,2" "nm" \
  "gammaUO3_U0_1600_k222"

run_case "U3_NM_1600_k222" 3.0 1600 "2,2,2" "nm" \
  "gammaUO3_U3_1600_k222"

run_case "U3_NM_1600_k333" 3.0 1600 "3,3,3" "nm" \
  "gammaUO3_U3_1600_k333"

run_case "U3_NM_1800_k222" 3.0 1800 "2,2,2" "nm" \
  "gammaUO3_U3_1800_k222"

run_case "U3_seeded_1600_k222" 3.0 1600 "2,2,2" "seeded" \
  "gammaUO3_U3_seeded_1600_k222"

echo
echo ">>> SOC gamma-UO3 no estado U3/NM"
run_in_upb_env gpaw \
  mpiexec -n 4 gpaw python \
  "${SCRIPT_DIR}/04B2C1_soc.py"

echo
echo ">>> Decisão"
run_in_upb_env analysis python \
  "${SCRIPT_DIR}/04B2C1_decision.py"

echo "=============================================================================="
echo "STEP 04B2C1 FINALIZADO"
echo "=============================================================================="
