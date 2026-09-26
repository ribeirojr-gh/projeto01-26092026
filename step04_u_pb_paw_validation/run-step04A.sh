#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${SCRIPT_DIR}"

{
    echo "=============================================================================="
    echo "STEP 04A-R8 — GATE EOS Pb/PBE"
    echo "=============================================================================="
    echo "Data: $(date)"
    echo "Host: $(hostname)"
    echo "Projeto: ${PROJECT_ROOT}"
    echo

    source "${PROJECT_ROOT}/scripts/env_manager.sh"

    for f in \
        "${SCRIPT_DIR}/paw_generated/Pb/PBE/Pb.PBE" \
        "${SCRIPT_DIR}/paw_generated/Pb/PBEsol/Pb.PBEsol" \
        "${SCRIPT_DIR}/paw_generated/U/PBE/U.PBE" \
        "${SCRIPT_DIR}/paw_generated/U/PBEsol/U.PBEsol" \
        "${SCRIPT_DIR}/resultados_step04A/u_pseudization_selection_R5.json"
    do
        [[ -s "${f}" ]] || {
            echo "ERRO: artefato requerido ausente: ${f}"
            exit 20
        }
    done

    echo ">>> PAWs U/Pb anteriores encontrados. Nenhuma regeneração será feita."
    echo
    "${SCRIPT_DIR}/04A_pb_eos_R8.sh"

    echo
    echo "=============================================================================="
    echo "STEP 04A-R8 FINALIZADO"
    echo "=============================================================================="

} |& tee "${SCRIPT_DIR}/saida-step04A-R8.txt"
