#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
source "${PROJECT_ROOT}/scripts/env_manager.sh"

RESULTS="${SCRIPT_DIR}/resultados_step04B2C2"
LOGS="${SCRIPT_DIR}/logs"
GPW="${RESULTS}/gpw"
RELAX="${RESULTS}/relax"
mkdir -p "${RESULTS}" "${LOGS}" "${GPW}" "${RELAX}"

echo "=============================================================================="
echo "STEP 04B2C2 — RELAXAÇÃO FINAL U(VI) / gamma-UO3"
echo "=============================================================================="
echo "Data: $(date)"
echo "Host: $(hostname)"
echo "Projeto: ${PROJECT_ROOT}"
echo

required=(
  "${PROJECT_ROOT}/step04B2C1_uvi_gamma_uo3_screen/estruturas/gamma_UO3_293K_primitive.traj"
  "${PROJECT_ROOT}/step04B2C1_uvi_gamma_uo3_screen/estruturas/gamma_UO3_structure_manifest.json"
  "${PROJECT_ROOT}/step03_paw_pbesol_benchmark/paw_generated/PBEsol/O.PBEsol"
  "${PROJECT_ROOT}/step04_u_pb_paw_validation/paw_candidates/U_R5_pseudization/U14_nc6/PBEsol/U.PBEsol"
)
for f in "${required[@]}"; do
  [[ -s "${f}" ]] || { echo "ERRO: artefato obrigatório ausente: ${f}"; exit 20; }
done

echo ">>> Relaxação escalar Fddd com simetria preservada"
run_in_upb_env gpaw mpiexec -n 4 gpaw python "${SCRIPT_DIR}/04B2C2_relax.py"

echo
echo ">>> Métricas estruturais"
run_in_upb_env structures python "${SCRIPT_DIR}/04B2C2_structural_metrics.py"

run_sp() {
  local ecut="$1"; local kpts="$2"; local tag="$3"
  echo
  echo "[B2C2] ${tag}"
  run_in_upb_env gpaw env \
    UPB_B2C2_ECUT="${ecut}" \
    UPB_B2C2_KPTS="${kpts}" \
    UPB_B2C2_TAG="${tag}" \
    UPB_B2C2_OUT="${RESULTS}/${tag}.json" \
    UPB_B2C2_TXT="${LOGS}/${tag}.txt" \
    UPB_B2C2_GPW="${GPW}/${tag}.gpw" \
    mpiexec -n 4 gpaw python "${SCRIPT_DIR}/04B2C2_singlepoint.py"
}

echo
echo ">>> Single points finais / convergência"
run_sp 1600 "2,2,2" "gammaUO3_relaxed_1600_k222"
run_sp 1600 "3,3,3" "gammaUO3_relaxed_1600_k333"
run_sp 1800 "2,2,2" "gammaUO3_relaxed_1800_k222"

echo
echo ">>> Convergência SOC: subespaço, k-points e cutoff"
run_in_upb_env gpaw mpiexec -n 4 gpaw python "${SCRIPT_DIR}/04B2C2_soc_convergence.py"

echo
echo ">>> Decisão final"
run_in_upb_env analysis python "${SCRIPT_DIR}/04B2C2_decision.py"

echo "=============================================================================="
echo "STEP 04B2C2 FINALIZADO"
echo "=============================================================================="
