#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
source "${PROJECT_ROOT}/scripts/env_manager.sh"

RESULTS="${SCRIPT_DIR}/resultados_step05A"
mkdir -p "${RESULTS}" "${SCRIPT_DIR}/logs"

echo "=============================================================================="
echo "STEP 05A — HOSTS PRISTINOS + DESIGN DE SUPERCÉLULAS"
echo "=============================================================================="
echo "Data: $(date)"
echo "Host: $(hostname)"
echo "Projeto: ${PROJECT_ROOT}"
echo

required=(
  "${PROJECT_ROOT}/step01_R2_final_references/referencias_finais/calcita_ref_experimental_primitiva.cif"
  "${PROJECT_ROOT}/step01_R2_final_references/referencias_finais/dolomita_ref_experimental_primitiva.cif"
  "${PROJECT_ROOT}/step03_paw_pbesol_benchmark/paw_generated/PBEsol/Ca.PBEsol"
  "${PROJECT_ROOT}/step03_paw_pbesol_benchmark/paw_generated/PBEsol/Mg.PBEsol"
  "${PROJECT_ROOT}/step03_paw_pbesol_benchmark/paw_generated/PBEsol/C.PBEsol"
  "${PROJECT_ROOT}/step03_paw_pbesol_benchmark/paw_generated/PBEsol/O.PBEsol"
)

for f in "${required[@]}"; do
  [[ -s "${f}" ]] || {
    echo "ERRO: artefato obrigatório ausente: ${f}"
    exit 20
  }
done

for mineral in calcita dolomita; do
  echo
  echo ">>> Relaxação fresh host: ${mineral}"
  run_in_upb_env gpaw env \
    UPB_HOST="${mineral}" \
    mpiexec -n 4 gpaw python \
      "${SCRIPT_DIR}/05A_relax_host.py"

  echo
  echo ">>> Validação 1600 eV: ${mineral}"
  run_in_upb_env gpaw env \
    UPB_HOST="${mineral}" \
    mpiexec -n 4 gpaw python \
      "${SCRIPT_DIR}/05A_validate_host.py"
done

echo
echo ">>> Busca de supercélulas HNF quase isotrópicas"
run_in_upb_env structures python \
  "${SCRIPT_DIR}/05A_build_supercells.py"

echo
echo ">>> Decisão"
run_in_upb_env analysis python \
  "${SCRIPT_DIR}/05A_decision.py"

echo "=============================================================================="
echo "STEP 05A FINALIZADO"
echo "=============================================================================="
