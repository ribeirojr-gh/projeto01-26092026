#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

source "${PROJECT_ROOT}/scripts/env_manager.sh"
require_upb_environment gpaw

GPAW_ENV="$(upb_env_path gpaw)"
GPAW_SETUP="${GPAW_ENV}/bin/gpaw-setup"

PAW_ROOT="${SCRIPT_DIR}/paw_generated"
PBE_DIR="${PAW_ROOT}/PBE"
PBESOL_DIR="${PAW_ROOT}/PBEsol"
LOG_DIR="${PAW_ROOT}/logs"

mkdir -p "${PBE_DIR}" "${PBESOL_DIR}" "${LOG_DIR}"

if [[ ! -x "${GPAW_SETUP}" ]]; then
    echo "ERRO: gpaw-setup não encontrado em ${GPAW_SETUP}" >&2
    echo "O Step 03 foi desenhado para o gerador antigo porque os setups" >&2
    echo "oficiais distribuídos pelo GPAW são gerados com esse gerador." >&2
    exit 4
fi

"${GPAW_SETUP}" --help > "${LOG_DIR}/gpaw-setup-help.txt" 2>&1 || true

generate_one() {
    local xc="$1"
    local element="$2"
    local outdir="$3"
    local logfile="${LOG_DIR}/${element}_${xc}_generation.log"
    local expected="${outdir}/${element}.${xc}"

    if [[ -f "${expected}" || -f "${expected}.gz" ]]; then
        echo "[PAW] ${element}.${xc}: já existe; reutilizando."
        return 0
    fi

    echo "[PAW] Gerando ${element}.${xc} com gpaw-setup..."
    (
        cd "${outdir}"
        "${GPAW_SETUP}" -f "${xc}" "${element}"
    ) |& tee "${logfile}"

    if [[ ! -f "${expected}" && ! -f "${expected}.gz" ]]; then
        echo "ERRO: gpaw-setup terminou, mas ${element}.${xc} não foi encontrado." >&2
        echo "Conteúdo de ${outdir}:" >&2
        ls -la "${outdir}" >&2
        exit 5
    fi
}

for element in Ca Mg C O; do
    generate_one "PBE" "${element}" "${PBE_DIR}"
done

for element in Ca Mg C O; do
    generate_one "PBEsol" "${element}" "${PBESOL_DIR}"
done

{
    echo "arquivo,sha256"
    for f in \
        "${PBE_DIR}"/Ca.PBE* \
        "${PBE_DIR}"/Mg.PBE* \
        "${PBE_DIR}"/C.PBE* \
        "${PBE_DIR}"/O.PBE* \
        "${PBESOL_DIR}"/Ca.PBEsol* \
        "${PBESOL_DIR}"/Mg.PBEsol* \
        "${PBESOL_DIR}"/C.PBEsol* \
        "${PBESOL_DIR}"/O.PBEsol*
    do
        [[ -f "${f}" ]] || continue
        hash="$(sha256sum "${f}" | awk '{print $1}')"
        printf "%s,%s\n" "$(basename "${f}")" "${hash}"
    done
} > "${PAW_ROOT}/paw_sha256.csv"

echo
echo "============================================================"
echo "GERAÇÃO PAW CONCLUÍDA"
echo "PBE:    ${PBE_DIR}"
echo "PBEsol: ${PBESOL_DIR}"
echo "Hashes: ${PAW_ROOT}/paw_sha256.csv"
echo "============================================================"
