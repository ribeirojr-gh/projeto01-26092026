#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
source "${PROJECT_ROOT}/scripts/env_manager.sh"

RESULTS="${SCRIPT_DIR}/resultados_step04B1B2_R2"
LOGS="${SCRIPT_DIR}/logs"
RESTARTS="${RESULTS}/restart"
mkdir -p "${RESULTS}" "${LOGS}" "${RESTARTS}"

echo "=============================================================================="
echo "STEP 04B1B2-R2 — EOS DETERMINÍSTICO + CUTOFF 1400/1600/1800"
echo "=============================================================================="
echo "Data: $(date)"
echo "Host: $(hostname)"
echo "Projeto: ${PROJECT_ROOT}"

required=(
  "${PROJECT_ROOT}/step04B_compound_screening/estruturas/UO2_fluorite_exp.traj"
  "${PROJECT_ROOT}/step03_paw_pbesol_benchmark/paw_generated/PBEsol/O.PBEsol"
  "${PROJECT_ROOT}/step04_u_pb_paw_validation/paw_candidates/U_R5_pseudization/U14_nc6/PBEsol/U.PBEsol"
  "${PROJECT_ROOT}/step04B1B_uo2_reproducibility/resultados_step04B1B1/UO2_nc6_U3p0_ky.json"
  "${PROJECT_ROOT}/step04B1B_uo2_reproducibility/resultados_step04B1B1/UO2_nc6_U4p0_ky.json"
)
for f in "${required[@]}"; do
    [[ -s "${f}" ]] || {
        echo "ERRO: artefato requerido ausente: ${f}"
        exit 20
    }
done

json_ok() {
  local f="$1"
  [[ -s "${f}" ]] || return 1
  python3 - "${f}" <<'PY'
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
        echo "[R2] reutilizando ${out}"
        return
    fi

    rm -f "${out}"
    echo "[R2] ${tag}"

    run_in_upb_env gpaw env \
      UPB_R2_UEFF="${ueff}" \
      UPB_R2_ECUT="${ecut}" \
      UPB_R2_A="${a}" \
      UPB_R2_TAG="${tag}" \
      UPB_R2_OUT="${out}" \
      UPB_R2_LOGS="${LOGS}" \
      UPB_R2_RESTARTS="${RESTARTS}" \
      mpiexec -n 4 gpaw python "${SCRIPT_DIR}/04B1B2_R2_calculate.py"
}

# EOS completo e autoconsistente em 1400 eV, sem random=True.
for ueff in 3.0 4.0; do
    u="${ueff/./p}"
    run_case "${ueff}" 1400 5.361188 "UO2_nc6_U${u}_s0p98_1400"
    run_case "${ueff}" 1400 5.415894 "UO2_nc6_U${u}_s0p99_1400"
    run_case "${ueff}" 1400 5.470600 "UO2_nc6_U${u}_s1p00_1400"
    run_case "${ueff}" 1400 5.525306 "UO2_nc6_U${u}_s1p01_1400"
    run_case "${ueff}" 1400 5.580012 "UO2_nc6_U${u}_s1p02_1400"

    # Cutoff ladder no centro; 1400 é copiado logicamente do EOS central,
    # mas gravamos os três nomes esperados pelo pós-processamento.
    cp -f \
      "${RESULTS}/UO2_nc6_U${u}_s1p00_1400.json" \
      "${RESULTS}/UO2_nc6_U${u}_center_1400.json"

    run_case "${ueff}" 1600 5.470600 "UO2_nc6_U${u}_center_1600"
    run_case "${ueff}" 1800 5.470600 "UO2_nc6_U${u}_center_1800"
done

echo
echo ">>> Pós-processamento"
run_in_upb_env gpaw python "${SCRIPT_DIR}/04B1B2_R2_postprocess.py"

echo "=============================================================================="
echo "STEP 04B1B2-R2 FINALIZADO"
echo "=============================================================================="
