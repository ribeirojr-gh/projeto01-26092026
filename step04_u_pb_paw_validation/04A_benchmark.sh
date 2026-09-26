#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
source "${PROJECT_ROOT}/scripts/env_manager.sh"

RESULTS="${SCRIPT_DIR}/resultados_step04A"
LOGS="${SCRIPT_DIR}/logs"
PB_PBE="${SCRIPT_DIR}/paw_generated/Pb/PBE"
PB_PBESOL="${SCRIPT_DIR}/paw_generated/Pb/PBEsol"
U_PBE="${SCRIPT_DIR}/paw_generated/U/PBE"
U_PBESOL="${SCRIPT_DIR}/paw_generated/U/PBEsol"
mkdir -p "${RESULTS}" "${LOGS}"

run_pb_mpi() {
    local label="$1" xc="$2" setup_dir="$3" out="$4" txt="$5"
    echo "[MPI] ${label} | xc=${xc} | setup=${setup_dir:-OFFICIAL}"
    run_in_upb_env gpaw env \
        UPB_PB_LABEL="${label}" \
        UPB_PB_XC="${xc}" \
        UPB_PB_SETUP_DIR="${setup_dir}" \
        UPB_PB_OUT="${out}" \
        UPB_PB_TXT="${txt}" \
        mpiexec -n 4 gpaw python "${SCRIPT_DIR}/04A_pb_singlepoint.py"
}

echo "=============================================================================="
echo "STEP 04A2 — TESTE DE CARREGAMENTO DOS PAWs"
echo "=============================================================================="
run_in_upb_env gpaw python "${SCRIPT_DIR}/04A_load_test.py" \
    --out "${RESULTS}/paw_load_test.json" \
    --pb-pbe "${PB_PBE}" \
    --pb-pbesol "${PB_PBESOL}" \
    --u-pbe "${U_PBE}" \
    --u-pbesol "${U_PBESOL}"

echo
echo "=============================================================================="
echo "STEP 04A3 — GATE Pb-PBE GERADO vs OFICIAL"
echo "=============================================================================="
run_pb_mpi "Pb_PBE_official" "PBE" "" \
    "${RESULTS}/Pb_PBE_official.json" "${LOGS}/Pb_PBE_official_gpaw.txt"
run_pb_mpi "Pb_PBE_generated" "PBE" "${PB_PBE}" \
    "${RESULTS}/Pb_PBE_generated.json" "${LOGS}/Pb_PBE_generated_gpaw.txt"

echo
echo "=============================================================================="
echo "STEP 04A4 — TESTE Pb-PBEsol GERADO"
echo "=============================================================================="
run_pb_mpi "Pb_PBEsol_generated" "PBEsol" "${PB_PBESOL}" \
    "${RESULTS}/Pb_PBEsol_generated.json" "${LOGS}/Pb_PBEsol_generated_gpaw.txt"

echo
echo "=============================================================================="
echo "STEP 04A5 — PÓS-PROCESSAMENTO"
echo "=============================================================================="
run_in_upb_env gpaw python "${SCRIPT_DIR}/04A_postprocess.py"
