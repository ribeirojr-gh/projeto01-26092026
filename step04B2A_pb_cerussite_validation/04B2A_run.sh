#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
source "${PROJECT_ROOT}/scripts/env_manager.sh"

RESULTS="${SCRIPT_DIR}/resultados_step04B2A"
LOGS="${SCRIPT_DIR}/logs"
RELAX="${RESULTS}/relax"
mkdir -p "${RESULTS}" "${LOGS}" "${RELAX}"

echo "=============================================================================="
echo "STEP 04B2A — Pb(II) / CERUSSITA PbCO3"
echo "=============================================================================="
echo "Data: $(date)"
echo "Host: $(hostname)"
echo "Projeto: ${PROJECT_ROOT}"
echo

required=(
  "${PROJECT_ROOT}/step04B_compound_screening/estruturas/cerussite_exp.traj"
  "${PROJECT_ROOT}/step03_paw_pbesol_benchmark/paw_generated/PBEsol/O.PBEsol"
  "${PROJECT_ROOT}/step03_paw_pbesol_benchmark/paw_generated/PBEsol/C.PBEsol"
  "${PROJECT_ROOT}/step04_u_pb_paw_validation/paw_generated/Pb/PBEsol/Pb.PBEsol"
)

for f in "${required[@]}"; do
    [[ -s "${f}" ]] || {
        echo "ERRO: artefato obrigatório ausente: ${f}"
        exit 20
    }
done

run_sp() {
    local structure="$1"
    local ecut="$2"
    local kpts="$3"
    local tag="$4"
    local out="${RESULTS}/${tag}.json"
    local txt="${LOGS}/${tag}_gpaw.txt"

    echo
    echo "[B2A] ${tag}"

    run_in_upb_env gpaw env \
      UPB_PB_STRUCTURE="${structure}" \
      UPB_PB_ECUT="${ecut}" \
      UPB_PB_KPTS="${kpts}" \
      UPB_PB_OUT="${out}" \
      UPB_PB_TXT="${txt}" \
      mpiexec -n 4 gpaw python \
        "${SCRIPT_DIR}/04B2A_singlepoint.py"
}

EXP="${PROJECT_ROOT}/step04B_compound_screening/estruturas/cerussite_exp.traj"

echo ">>> Gate numérico na estrutura experimental"
run_sp "${EXP}" 1400 "3,2,3" "PbCO3_exp_1400_k323"
run_sp "${EXP}" 1400 "4,3,4" "PbCO3_exp_1400_k434"
run_sp "${EXP}" 1600 "3,2,3" "PbCO3_exp_1600_k323"
run_sp "${EXP}" 1600 "4,3,4" "PbCO3_exp_1600_k434"

echo
echo ">>> Avaliação do gate numérico"
run_in_upb_env analysis python \
  "${SCRIPT_DIR}/04B2A_numeric_gate.py"

echo
echo ">>> Relaxação alternada posições/célula"
run_in_upb_env gpaw \
  mpiexec -n 4 gpaw python \
  "${SCRIPT_DIR}/04B2A_relax.py"

echo
echo ">>> Métricas estruturais"
run_in_upb_env analysis python \
  "${SCRIPT_DIR}/04B2A_structural_metrics.py"

echo
echo ">>> Single point final de validação"
FINAL="${RELAX}/PbCO3_relaxed_production.traj"
run_sp "${FINAL}" 1600 "4,3,4" "PbCO3_relaxed_1600_k434"

echo
echo ">>> Decisão final"
run_in_upb_env analysis python \
  "${SCRIPT_DIR}/04B2A_final_decision.py"

echo "=============================================================================="
echo "STEP 04B2A FINALIZADO"
echo "=============================================================================="
