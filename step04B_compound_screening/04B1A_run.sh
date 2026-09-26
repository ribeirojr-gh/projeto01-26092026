#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
source "${PROJECT_ROOT}/scripts/env_manager.sh"

RESULTS="${SCRIPT_DIR}/resultados_step04B1A"
LOGS="${SCRIPT_DIR}/logs"
STRUCTURES="${SCRIPT_DIR}/estruturas"

mkdir -p "${RESULTS}" "${LOGS}" "${STRUCTURES}"

echo "=============================================================================="
echo "STEP 04B1A-R2 — TRIAGEM QUÍMICA U/Pb COM SCF ROBUSTO"
echo "=============================================================================="
echo "Data: $(date)"
echo "Host: $(hostname)"
echo "Projeto: ${PROJECT_ROOT}"
echo

required=(
  "${PROJECT_ROOT}/step03_paw_pbesol_benchmark/paw_generated/PBEsol/O.PBEsol"
  "${PROJECT_ROOT}/step03_paw_pbesol_benchmark/paw_generated/PBEsol/C.PBEsol"
  "${PROJECT_ROOT}/step04_u_pb_paw_validation/paw_generated/U/PBEsol/U.PBEsol"
  "${PROJECT_ROOT}/step04_u_pb_paw_validation/paw_generated/Pb/PBEsol/Pb.PBEsol"
  "${PROJECT_ROOT}/step04_u_pb_paw_validation/paw_candidates/U_R5_pseudization/U14_nc6/PBEsol/U.PBEsol"
)

for f in "${required[@]}"; do
    [[ -s "${f}" ]] || {
        echo "ERRO: artefato necessário ausente:"
        echo "  ${f}"
        exit 20
    }
done

echo ">>> Preparação das estruturas"
run_in_upb_env structures python "${SCRIPT_DIR}/04B1A_prepare_structures.py"

json_is_success() {
    local file="$1"
    [[ -s "${file}" ]] || return 1

    python3 - "${file}" <<'PY'
import json
import sys
from pathlib import Path

p = Path(sys.argv[1])
try:
    data = json.loads(p.read_text(encoding="utf-8"))
except Exception:
    raise SystemExit(1)

if data.get("status") == "converged":
    raise SystemExit(0)
if "energy_eV" in data and data.get("status") is None:
    raise SystemExit(0)
raise SystemExit(1)
PY
}

run_calc() {
    local system="$1"
    local structure="$2"
    local dataset="$3"
    local ueff="$4"
    local kpts="$5"
    local tag="$6"

    local out="${RESULTS}/${tag}.json"
    local txt="${LOGS}/${tag}_gpaw.txt"

    if json_is_success "${out}"; then
        echo "[B1A-R2] reutilizando resultado convergido: ${out}"
        return
    fi

    rm -f "${out}"

    echo
    echo "[B1A-R2] ${tag}"

    run_in_upb_env gpaw env \
        UPB_B1A_SYSTEM="${system}" \
        UPB_B1A_STRUCTURE="${structure}" \
        UPB_B1A_U_DATASET="${dataset}" \
        UPB_B1A_UEFF="${ueff}" \
        UPB_B1A_KPTS="${kpts}" \
        UPB_B1A_OUT="${out}" \
        UPB_B1A_TXT="${txt}" \
        mpiexec -n 4 gpaw python "${SCRIPT_DIR}/04B1A_calculate.py"
}

run_calc \
    "PbCO3" \
    "${STRUCTURES}/cerussite_exp.traj" \
    "" \
    "0.0" \
    "3,2,3" \
    "PbCO3_cerussite_PBEsol"

for dataset in poly6 nc6; do
    for ueff in 4.0 3.0 5.0 2.0 0.0; do
        tag="UO2_${dataset}_Ueff_${ueff/./p}"
        run_calc \
            "UO2" \
            "${STRUCTURES}/UO2_fluorite_exp.traj" \
            "${dataset}" \
            "${ueff}" \
            "3,3,3" \
            "${tag}"
    done
done

for dataset in poly6 nc6; do
    tag="delta_UO3_${dataset}_Ueff_0p0"
    run_calc \
        "delta_UO3" \
        "${STRUCTURES}/delta_UO3_ref.traj" \
        "${dataset}" \
        "0.0" \
        "5,5,5" \
        "${tag}"
done

echo
echo ">>> Pós-processamento"
run_in_upb_env gpaw python "${SCRIPT_DIR}/04B1A_postprocess.py"

echo
echo "=============================================================================="
echo "STEP 04B1A-R2 FINALIZADO"
echo "=============================================================================="
