#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
source "${PROJECT_ROOT}/scripts/env_manager.sh"

RESULTS="${SCRIPT_DIR}/resultados_step04A/eos_Pb_PBE_R8"
LOGS="${SCRIPT_DIR}/logs/eos_Pb_PBE_R8"
PB_PBE="${SCRIPT_DIR}/paw_generated/Pb/PBE"

mkdir -p "${RESULTS}/official" "${RESULTS}/generated" "${LOGS}/official" "${LOGS}/generated"

LATTICES=("4.80" "4.90" "5.00" "5.10" "5.20")

run_point() {
    local kind="$1"
    local a="$2"
    local setup_dir="$3"

    local tag="${a/./p}"
    local out="${RESULTS}/${kind}/a_${tag}.json"
    local txt="${LOGS}/${kind}/a_${tag}.txt"
    local label="Pb_PBE_${kind}_a_${tag}"

    if [[ -s "${out}" ]]; then
        echo "[R8] reutilizando ${out}"
        return
    fi

    echo "[R8] ${kind} | a=${a} Å"

    run_in_upb_env gpaw env \
        UPB_EOS_LABEL="${label}" \
        UPB_EOS_SETUP_KIND="${kind}" \
        UPB_EOS_SETUP_DIR="${setup_dir}" \
        UPB_EOS_A="${a}" \
        UPB_EOS_OUT="${out}" \
        UPB_EOS_TXT="${txt}" \
        mpiexec -n 4 gpaw python "${SCRIPT_DIR}/04A_pb_eos_point_R8.py"
}

echo "=============================================================================="
echo "STEP 04A-R8 — Pb/PBE: EQUATION-OF-STATE GATE"
echo "=============================================================================="

for a in "${LATTICES[@]}"; do
    run_point official "${a}" ""
done

for a in "${LATTICES[@]}"; do
    run_point generated "${a}" "${PB_PBE}"
done

echo
echo ">>> Pós-processamento EOS"
run_in_upb_env gpaw python "${SCRIPT_DIR}/04A_pb_eos_post_R8.py"
