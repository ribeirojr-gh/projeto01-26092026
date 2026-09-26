#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
source "${PROJECT_ROOT}/scripts/env_manager.sh"

RESULTS="${SCRIPT_DIR}/resultados_step04B1B2"
LOGS="${SCRIPT_DIR}/logs"
RESTART="${RESULTS}/restart"
mkdir -p "${RESULTS}" "${LOGS}" "${RESTART}"

echo "=============================================================================="
echo "STEP 04B1B2 — UO2/nc6: EOS + 1400/1600 eV"
echo "=============================================================================="
echo "Data: $(date)"
echo "Host: $(hostname)"
echo "Projeto: ${PROJECT_ROOT}"
echo

required=(
  "${PROJECT_ROOT}/step04B_compound_screening/estruturas/UO2_fluorite_exp.traj"
  "${PROJECT_ROOT}/step03_paw_pbesol_benchmark/paw_generated/PBEsol/O.PBEsol"
  "${PROJECT_ROOT}/step04_u_pb_paw_validation/paw_candidates/U_R5_pseudization/U14_nc6/PBEsol/U.PBEsol"
  "${PROJECT_ROOT}/step04B1B_uo2_reproducibility/resultados_step04B1B1/UO2_nc6_U3p0_ky.json"
  "${PROJECT_ROOT}/step04B1B_uo2_reproducibility/resultados_step04B1B1/UO2_nc6_U4p0_ky.json"
)
for f in "${required[@]}"; do
    [[ -s "${f}" ]] || {
        echo "ERRO: artefato necessário ausente: ${f}"
        exit 20
    }
done

json_ok() {
    local file="$1"
    [[ -s "${file}" ]] || return 1
    python3 - "${file}" <<'PY'
import json, sys
from pathlib import Path
p=Path(sys.argv[1])
try:
    d=json.loads(p.read_text(encoding="utf-8"))
except Exception:
    raise SystemExit(1)
raise SystemExit(0 if d.get("status")=="converged_tight" else 1)
PY
}

run_case() {
    local ueff="$1"
    local ecut="$2"
    local a="$3"
    local tag="$4"
    local out="${RESULTS}/${tag}.json"

    echo
    if json_ok "${out}"; then
        echo "[B1B2] reutilizando ${out}"
        return
    fi

    rm -f "${out}"
    echo "[B1B2] Ueff=${ueff} eV | Ecut=${ecut} eV | a=${a} Å"

    run_in_upb_env gpaw env \
        UPB_B1B2_UEFF="${ueff}" \
        UPB_B1B2_ECUT="${ecut}" \
        UPB_B1B2_A="${a}" \
        UPB_B1B2_TAG="${tag}" \
        UPB_B1B2_OUT="${out}" \
        UPB_B1B2_LOG_DIR="${LOGS}" \
        UPB_B1B2_RESTART_DIR="${RESTART}" \
        mpiexec -n 4 gpaw python \
            "${SCRIPT_DIR}/04B1B2_calculate.py"
}

# Centro a=5.4706 Å / Ecut=1400 eV é reutilizado do B1B1.
# Calculamos apenas os quatro pontos laterais do EOS para cada Ueff.
for ueff in 3.0 4.0; do
    u="${ueff/./p}"

    run_case "${ueff}" 1400 5.361188 \
        "UO2_nc6_U${u}_s0p98_1400"
    run_case "${ueff}" 1400 5.415894 \
        "UO2_nc6_U${u}_s0p99_1400"
    run_case "${ueff}" 1400 5.525306 \
        "UO2_nc6_U${u}_s1p01_1400"
    run_case "${ueff}" 1400 5.580012 \
        "UO2_nc6_U${u}_s1p02_1400"

    # Validação direta do cutoff no centro.
    run_case "${ueff}" 1600 5.470600 \
        "UO2_nc6_U${u}_center_1600"
done

echo
echo ">>> Pós-processamento EOS/cutoff"
run_in_upb_env gpaw python \
    "${SCRIPT_DIR}/04B1B2_postprocess.py"

echo
echo "=============================================================================="
echo "STEP 04B1B2 FINALIZADO"
echo "=============================================================================="
