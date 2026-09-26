#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
source "${PROJECT_ROOT}/scripts/env_manager.sh"

RESULTS="${SCRIPT_DIR}/resultados_step04B1B1"
LOGS="${SCRIPT_DIR}/logs"
RESTART="${RESULTS}/restart"

mkdir -p "${RESULTS}" "${LOGS}" "${RESTART}"

echo "=============================================================================="
echo "STEP 04B1B1 — UO2/nc6: REPRODUTIBILIDADE E SCF TIGHT"
echo "=============================================================================="
echo "Data: $(date)"
echo "Host: $(hostname)"
echo "Projeto: ${PROJECT_ROOT}"
echo

required=(
  "${PROJECT_ROOT}/step04B_compound_screening/estruturas/UO2_fluorite_exp.traj"
  "${PROJECT_ROOT}/step03_paw_pbesol_benchmark/paw_generated/PBEsol/O.PBEsol"
  "${PROJECT_ROOT}/step04_u_pb_paw_validation/paw_candidates/U_R5_pseudization/U14_nc6/PBEsol/U.PBEsol"
)

for file in "${required[@]}"; do
    [[ -s "${file}" ]] || {
        echo "ERRO: artefato obrigatório ausente: ${file}"
        exit 20
    }
done

json_ok() {
    local file="$1"
    [[ -s "${file}" ]] || return 1
    python3 - "${file}" <<'PY'
import json
import sys
from pathlib import Path
p = Path(sys.argv[1])
try:
    d = json.loads(p.read_text(encoding="utf-8"))
except Exception:
    raise SystemExit(1)
raise SystemExit(0 if d.get("status") == "converged_tight" else 1)
PY
}

for ueff in 2.5 3.0 4.0; do
    for domain in kz kx ky; do
        tag="UO2_nc6_U${ueff/./p}_${domain}"
        out="${RESULTS}/${tag}.json"

        echo
        if json_ok "${out}"; then
            echo "[B1B1] reutilizando ${out}"
            continue
        fi

        rm -f "${out}"

        echo "[B1B1] Ueff=${ueff} eV | domínio=${domain}"

        run_in_upb_env gpaw env \
            UPB_B1B1_UEFF="${ueff}" \
            UPB_B1B1_DOMAIN="${domain}" \
            UPB_B1B1_OUT="${out}" \
            UPB_B1B1_LOG_DIR="${LOGS}" \
            UPB_B1B1_RESTART_DIR="${RESTART}" \
            mpiexec -n 4 gpaw python \
                "${SCRIPT_DIR}/04B1B1_calculate.py"
    done
done

echo
echo ">>> Pós-processamento"
run_in_upb_env gpaw python \
    "${SCRIPT_DIR}/04B1B1_postprocess.py"

echo
echo "=============================================================================="
echo "STEP 04B1B1 FINALIZADO"
echo "=============================================================================="
