#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
source "${PROJECT_ROOT}/scripts/env_manager.sh"

RESULTS="${SCRIPT_DIR}/resultados_step04B1A_R4"
LOGS="${SCRIPT_DIR}/logs/R4"
GPW="${RESULTS}/gpw"

mkdir -p "${RESULTS}" "${LOGS}" "${GPW}"

echo "=============================================================================="
echo "STEP 04B1A-R4 — DIAGNÓSTICO UO2 DFT+U"
echo "=============================================================================="
echo "Data: $(date)"
echo "Host: $(hostname)"
echo "Projeto: ${PROJECT_ROOT}"
echo

required=(
  "${SCRIPT_DIR}/estruturas/UO2_fluorite_exp.traj"
  "${PROJECT_ROOT}/step03_paw_pbesol_benchmark/paw_generated/PBEsol/O.PBEsol"
  "${PROJECT_ROOT}/step04_u_pb_paw_validation/paw_generated/U/PBEsol/U.PBEsol"
  "${PROJECT_ROOT}/step04_u_pb_paw_validation/paw_candidates/U_R5_pseudization/U14_nc6/PBEsol/U.PBEsol"
)

for f in "${required[@]}"; do
    [[ -s "${f}" ]] || {
        echo "ERRO: artefato necessário ausente: ${f}"
        exit 20
    }
done

for dataset in poly6 nc6; do
    out="${RESULTS}/UO2_${dataset}_diagnostic_R4.json"

    echo
    echo ">>> Dataset ${dataset}"

    run_in_upb_env gpaw env \
        UPB_R4_DATASET="${dataset}" \
        UPB_R4_OUT="${out}" \
        UPB_R4_TXT_DIR="${LOGS}" \
        UPB_R4_GPW_DIR="${GPW}" \
        mpiexec -n 4 gpaw python \
            "${SCRIPT_DIR}/04B1A_UO2_diagnostic_R4.py"
done

echo
echo ">>> Pós-processamento"
run_in_upb_env gpaw python \
    "${SCRIPT_DIR}/04B1A_postprocess_R4.py"

echo
echo "=============================================================================="
echo "STEP 04B1A-R4 FINALIZADO"
echo "=============================================================================="
