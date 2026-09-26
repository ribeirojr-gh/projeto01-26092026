#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
source "${PROJECT_ROOT}/scripts/env_manager.sh"

PB_PBE="${SCRIPT_DIR}/paw_generated/Pb/PBE"
PB_PBESOL="${SCRIPT_DIR}/paw_generated/Pb/PBEsol"
U_PBE="${SCRIPT_DIR}/paw_generated/U/PBE"
U_PBESOL="${SCRIPT_DIR}/paw_generated/U/PBEsol"

U_CANDIDATES="${SCRIPT_DIR}/paw_candidates/U_R5_pseudization"
RESULTS="${SCRIPT_DIR}/resultados_step04A"
LOGS="${SCRIPT_DIR}/logs"

mkdir -p \
    "${PB_PBE}" "${PB_PBESOL}" \
    "${U_PBE}" "${U_PBESOL}" \
    "${U_CANDIDATES}" "${RESULTS}" "${LOGS}"

generate_old_pb() {
    local xc="$1"
    local outdir="$2"
    local outfile="${outdir}/Pb.${xc}"

    if [[ -s "${outfile}" ]]; then
        echo "[Pb/${xc}] já existe; reutilizando ${outfile}"
        return
    fi

    echo "[Pb/${xc}] gpaw-setup (old generator)"
    (
        cd "${outdir}"
        run_in_upb_env gpaw gpaw-setup -f "${xc}" Pb
    ) |& tee "${LOGS}/Pb_${xc}_old_generator.txt"

    [[ -s "${outfile}" ]] || {
        echo "ERRO: ${outfile} não foi gerado." >&2
        exit 10
    }
}

try_u_candidate() {
    local xc="$1"
    local candidate_id="$2"
    local pseudize="$3"
    local projectors="$4"
    local radii="$5"
    local outdir="$6"
    local logfile="$7"

    mkdir -p "${outdir}"
    rm -f "${outdir}/U.${xc}"

    echo "[U/${xc}] candidate=${candidate_id}"
    echo "[U/${xc}] pseudize=${pseudize}"
    echo "[U/${xc}] projectors=${projectors}"
    echo "[U/${xc}] radii=${radii} Bohr"
    echo "[U/${xc}] scalar-relativistic; check_all ENABLED"

    set +e
    (
        cd "${outdir}"
        run_in_upb_env gpaw gpaw dataset U \
            -f "${xc}" \
            -s \
            -e 14 \
            -P "${projectors}" \
            -r "${radii}" \
            -z "${pseudize}" \
            -w
    ) |& tee "${logfile}"
    local status=${PIPESTATUS[0]}
    set -e

    if [[ ${status} -eq 0 && -s "${outdir}/U.${xc}" ]]; then
        return 0
    fi
    return 1
}

scan_u_pseudization() {
    # ----------------------------------------------------------------------
    # R5: R2-R4 mostraram que:
    #   * reduzir rcut piora o 5f;
    #   * mudar energia/número de projetores f extras não corrige;
    #   * promover 5d ou 5s/5p/5d semicore não corrige.
    #
    # O log mostra que o 5f pseudo tem grande diferença de norma no esquema
    # padrão poly,4. O generator2 oferece pseudização "nc", que chama
    # pseudize_normalized(), além da "poly" padrão. Esta é a última triagem
    # interna controlada antes de abandonar generator2 para U.
    # ----------------------------------------------------------------------

    local ids=(
        "U14_poly4"
        "U14_poly6"
        "U14_poly8"
        "U14_nc4"
        "U14_nc6"
        "U14_nc8"
    )

    local pseudizers=(
        "poly,4"
        "poly,6"
        "poly,8"
        "nc,4"
        "nc,6"
        "nc,8"
    )

    local projectors="6s,7s,6p,7p,6d,d,5f,f,G"
    local radii="2.50,2.50,2.50,2.50"

    local scan_csv="${RESULTS}/u_pseudization_scan_R5.csv"
    local selection_json="${RESULTS}/u_pseudization_selection_R5.json"

    echo "candidate_id,pseudization,projectors,radii_Bohr,PBE_passes,PBEsol_passes,selected" \
        > "${scan_csv}"

    rm -f "${U_PBE}/U.PBE" "${U_PBESOL}/U.PBEsol"

    local passing_indices=()
    local i cid pseud pbe_dir pbesol_dir pbe_ok pbesol_ok

    for i in "${!ids[@]}"; do
        cid="${ids[$i]}"
        pseud="${pseudizers[$i]}"
        pbe_dir="${U_CANDIDATES}/${cid}/PBE"
        pbesol_dir="${U_CANDIDATES}/${cid}/PBEsol"

        echo
        echo "------------------------------------------------------------------------"
        echo "[U-R5] Testando ${cid}"
        echo "[U-R5] pseudize=${pseud}"
        echo "------------------------------------------------------------------------"

        pbe_ok="false"
        pbesol_ok="false"

        if try_u_candidate \
            PBE "${cid}" "${pseud}" "${projectors}" "${radii}" "${pbe_dir}" \
            "${LOGS}/U_R5_${cid}_PBE.txt"; then
            pbe_ok="true"
            echo "[U-R5/${cid}/PBE] check_all: APROVADO"
        else
            echo "[U-R5/${cid}/PBE] check_all: REPROVADO"
        fi

        if [[ "${pbe_ok}" == "true" ]]; then
            if try_u_candidate \
                PBEsol "${cid}" "${pseud}" "${projectors}" "${radii}" "${pbesol_dir}" \
                "${LOGS}/U_R5_${cid}_PBEsol.txt"; then
                pbesol_ok="true"
                echo "[U-R5/${cid}/PBEsol] check_all: APROVADO"
            else
                echo "[U-R5/${cid}/PBEsol] check_all: REPROVADO"
            fi
        else
            echo "[U-R5/${cid}/PBEsol] não executado porque PBE reprovou."
        fi

        echo "\"${cid}\",\"${pseud}\",\"${projectors}\",\"${radii}\",${pbe_ok},${pbesol_ok},false" \
            >> "${scan_csv}"

        if [[ "${pbe_ok}" == "true" && "${pbesol_ok}" == "true" ]]; then
            passing_indices+=("${i}")
        fi
    done

    if ((${#passing_indices[@]} == 0)); then
        cat > "${selection_json}" <<'EOF'
{
  "strategy": "pseudization_scan_default_U14",
  "generator": "gpaw dataset / generator2",
  "scalar_relativistic": true,
  "valence_electrons": 14,
  "projectors": "6s,7s,6p,7p,6d,d,5f,f,G",
  "radii_Bohr_spdf": [2.5, 2.5, 2.5, 2.5],
  "selected_candidate_id": null,
  "pseudization": null,
  "PBE_passes": false,
  "PBEsol_passes": false,
  "no_check_flag_used": false,
  "candidate_status": "FAILED_PSEUDIZATION_SCAN",
  "scientific_action": "STOP_CUSTOM_GENERATOR2_TUNING_AND_SWITCH_TO_VALIDATED_EXTERNAL_OR_ALL_ELECTRON_REFERENCE_STRATEGY"
}
EOF
        echo
        echo "ERRO: nenhum candidato de pseudização R5 passou em PBE e PBEsol."
        echo "Não foi usado -n/--no-check."
        echo "R2-R5 encerram a triagem interna do generator2 para U."
        echo "Próximo passo científico: estratégia externa/all-electron validada."
        echo "Envie:"
        echo "  ${scan_csv}"
        echo "  ${selection_json}"
        echo "  ${SCRIPT_DIR}/saida-step04A.txt"
        exit 11
    fi

    # Seleção conservadora: se poly e nc passarem, prefere poly com menor
    # número de derivadas; caso contrário escolhe o primeiro candidato que
    # passou na ordem explicitamente documentada acima.
    local best_i="${passing_indices[0]}"
    local best_id="${ids[$best_i]}"
    local best_pseud="${pseudizers[$best_i]}"
    local best_pbe="${U_CANDIDATES}/${best_id}/PBE/U.PBE"
    local best_pbesol="${U_CANDIDATES}/${best_id}/PBEsol/U.PBEsol"

    cp "${best_pbe}" "${U_PBE}/U.PBE"
    cp "${best_pbesol}" "${U_PBESOL}/U.PBEsol"

    python3 - "${scan_csv}" "${best_id}" <<'PY'
import csv
import sys
from pathlib import Path

path = Path(sys.argv[1])
best = sys.argv[2]
rows = list(csv.DictReader(path.open(encoding="utf-8")))
fields = list(rows[0])
for row in rows:
    row["selected"] = "true" if row["candidate_id"] == best else "false"
with path.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    w.writerows(rows)
PY

    cat > "${selection_json}" <<EOF
{
  "strategy": "pseudization_scan_default_U14",
  "generator": "gpaw dataset / generator2",
  "scalar_relativistic": true,
  "valence_electrons": 14,
  "projectors": "${projectors}",
  "radii_Bohr_spdf": [2.5, 2.5, 2.5, 2.5],
  "selected_candidate_id": "${best_id}",
  "pseudization": "${best_pseud}",
  "PBE_passes": true,
  "PBEsol_passes": true,
  "no_check_flag_used": false,
  "candidate_status": "INTERNAL_ATOMIC_GATE_PASSED_REQUIRES_COMPOUND_VALIDATION"
}
EOF

    echo
    echo "[U-R5] Candidato selecionado: ${best_id}"
    echo "[U-R5] pseudização: ${best_pseud}"
    echo "[U-R5] PBE e PBEsol passaram pelo check_all() padrão do GPAW."
}

echo "=============================================================================="
echo "STEP 04A1 — GERAÇÃO CONTROLADA DE PAWs — R5 PSEUDIZATION"
echo "=============================================================================="

generate_old_pb PBE "${PB_PBE}"
generate_old_pb PBEsol "${PB_PBESOL}"

scan_u_pseudization

echo
echo ">>> SHA256"
find "${SCRIPT_DIR}/paw_generated" -type f \
    \( -name 'Pb.PBE*' -o -name 'U.PBE*' \) \
    -print0 | sort -z | xargs -0 sha256sum \
    | tee "${RESULTS}/paw_sha256.txt"

echo
echo "STEP 04A1-R5 concluído."
