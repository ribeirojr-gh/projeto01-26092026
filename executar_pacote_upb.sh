#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# executar_pacote_upb.sh
#
# Launcher genérico do projeto "Datação U-Pb em Carbonatos / Petrobras".
#
# Fluxo automatizado:
#   1. localiza o pacote ZIP;
#   2. copia o ZIP para packages/ se necessário;
#   3. cria diretório temporário;
#   4. descompacta;
#   5. valida a estrutura petrobras_upb_project/;
#   6. copia/atualiza os arquivos na raiz do projeto;
#   7. ajusta permissões dos scripts .sh;
#   8. identifica o run-*.sh da etapa;
#   9. executa a etapa;
#  10. remove o diretório temporário.
#
# Uso mais simples, a partir da raiz do projeto:
#
#   bash executar_pacote_upb.sh
#
# O script procura o ZIP mais recente em:
#   - ./packages/
#   - ./
#   - ~/Downloads/
#
# Uso explícito:
#
#   bash executar_pacote_upb.sh /caminho/pacote.zip
#
# Se houver mais de um run-*.sh na etapa:
#
#   UPB_RUN_SCRIPT=step04_u_pb_paw_validation/run-step04A.sh \
#       bash executar_pacote_upb.sh /caminho/pacote.zip
# ==============================================================================

die() {
    echo
    echo "ERRO: $*" >&2
    exit 1
}

info() {
    echo "[UPB] $*"
}

# ------------------------------------------------------------------------------
# Determina a raiz do projeto.
# O launcher deve permanecer na raiz de petrobras_upb_project.
# ------------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${UPB_PROJECT_ROOT:-${SCRIPT_DIR}}"

[[ -d "${PROJECT_ROOT}" ]] || die "Raiz do projeto inexistente: ${PROJECT_ROOT}"

# Verificações mínimas para evitar executar no lugar errado.
[[ -d "${PROJECT_ROOT}/scripts" ]] || \
    die "Diretório scripts/ não encontrado em ${PROJECT_ROOT}."

mkdir -p "${PROJECT_ROOT}/packages"

# ------------------------------------------------------------------------------
# Localiza o ZIP.
# ------------------------------------------------------------------------------
PACKAGE_INPUT="${1:-}"

if [[ -n "${PACKAGE_INPUT}" ]]; then
    if [[ "${PACKAGE_INPUT}" != /* ]]; then
        PACKAGE_INPUT="${PROJECT_ROOT}/${PACKAGE_INPUT}"
    fi
    [[ -f "${PACKAGE_INPUT}" ]] || die "Pacote não encontrado: ${PACKAGE_INPUT}"
    PACKAGE_SOURCE="$(readlink -f "${PACKAGE_INPUT}")"
else
    # Seleciona o ZIP petrobras_upb_*.zip mais recentemente modificado
    # entre packages/, raiz do projeto e ~/Downloads.
    mapfile -t CANDIDATES < <(
        {
            find "${PROJECT_ROOT}/packages" -maxdepth 1 -type f \
                -name 'petrobras_upb_*.zip' -printf '%T@|%p\n' 2>/dev/null || true
            find "${PROJECT_ROOT}" -maxdepth 1 -type f \
                -name 'petrobras_upb_*.zip' -printf '%T@|%p\n' 2>/dev/null || true
            find "${HOME}/Downloads" -maxdepth 1 -type f \
                -name 'petrobras_upb_*.zip' -printf '%T@|%p\n' 2>/dev/null || true
        } | sort -t'|' -k1,1nr
    )

    ((${#CANDIDATES[@]} > 0)) || \
        die "Nenhum petrobras_upb_*.zip encontrado em packages/, raiz ou ~/Downloads."

    PACKAGE_SOURCE="${CANDIDATES[0]#*|}"
fi

PACKAGE_SOURCE="$(readlink -f "${PACKAGE_SOURCE}")"
PACKAGE_BASENAME="$(basename "${PACKAGE_SOURCE}")"
PACKAGE_LOCAL="${PROJECT_ROOT}/packages/${PACKAGE_BASENAME}"

info "Projeto: ${PROJECT_ROOT}"
info "Pacote selecionado: ${PACKAGE_SOURCE}"

# Mantém uma cópia organizada em packages/.
if [[ "${PACKAGE_SOURCE}" != "$(readlink -f "${PACKAGE_LOCAL}" 2>/dev/null || true)" ]]; then
    info "Copiando pacote para packages/${PACKAGE_BASENAME}"
    cp -f "${PACKAGE_SOURCE}" "${PACKAGE_LOCAL}"
fi

[[ -s "${PACKAGE_LOCAL}" ]] || die "ZIP vazio ou inválido: ${PACKAGE_LOCAL}"

# ------------------------------------------------------------------------------
# Pré-validação do ZIP.
# ------------------------------------------------------------------------------
command -v unzip >/dev/null 2>&1 || die "Comando 'unzip' não encontrado."

if ! unzip -tq "${PACKAGE_LOCAL}" >/dev/null; then
    die "Falha no teste de integridade do ZIP: ${PACKAGE_LOCAL}"
fi

if ! unzip -Z1 "${PACKAGE_LOCAL}" | grep -q '^petrobras_upb_project/'; then
    die "O ZIP não contém a raiz esperada petrobras_upb_project/."
fi

# ------------------------------------------------------------------------------
# Extração temporária.
# ------------------------------------------------------------------------------
TMPDIR_UPB="$(mktemp -d /tmp/upb_package.XXXXXX)"

cleanup() {
    rm -rf "${TMPDIR_UPB}"
}
trap cleanup EXIT

info "Temporário: ${TMPDIR_UPB}"
info "Descompactando..."

unzip -q "${PACKAGE_LOCAL}" -d "${TMPDIR_UPB}"

EXTRACTED_ROOT="${TMPDIR_UPB}/petrobras_upb_project"
[[ -d "${EXTRACTED_ROOT}" ]] || \
    die "Raiz extraída não encontrada: ${EXTRACTED_ROOT}"

# ------------------------------------------------------------------------------
# Detecta quais diretórios de etapa o pacote modifica.
# ------------------------------------------------------------------------------
mapfile -t STEP_DIRS < <(
    find "${EXTRACTED_ROOT}" \
        -mindepth 1 -maxdepth 1 -type d \
        -printf '%f\n' \
    | grep -E '^step[0-9][0-9]' \
    | sort -u
)

if ((${#STEP_DIRS[@]} == 0)); then
    die "Nenhum diretório stepXX_* encontrado dentro do pacote."
fi

info "Etapa(s) presente(s) no pacote: ${STEP_DIRS[*]}"

# ------------------------------------------------------------------------------
# Atualiza o projeto.
# ------------------------------------------------------------------------------
info "Copiando arquivos para a raiz do projeto..."
cp -a "${EXTRACTED_ROOT}/." "${PROJECT_ROOT}/"

# ------------------------------------------------------------------------------
# Permissões.
# Somente scripts shell recebem bit de execução.
# ------------------------------------------------------------------------------
if [[ -d "${PROJECT_ROOT}/scripts" ]]; then
    find "${PROJECT_ROOT}/scripts" \
        -maxdepth 1 -type f -name '*.sh' \
        -exec chmod 0755 {} +
fi

for step_dir in "${STEP_DIRS[@]}"; do
    if [[ -d "${PROJECT_ROOT}/${step_dir}" ]]; then
        find "${PROJECT_ROOT}/${step_dir}" \
            -maxdepth 1 -type f -name '*.sh' \
            -exec chmod 0755 {} +
    fi
done

# ------------------------------------------------------------------------------
# Descobre o script principal.
# Pode ser explicitado por UPB_RUN_SCRIPT.
# ------------------------------------------------------------------------------
RUNNER=""

if [[ -n "${UPB_RUN_SCRIPT:-}" ]]; then
    RUNNER="${PROJECT_ROOT}/${UPB_RUN_SCRIPT}"
    [[ -f "${RUNNER}" ]] || \
        die "UPB_RUN_SCRIPT aponta para arquivo inexistente: ${RUNNER}"
else
    # Procura run*.sh nos diretórios de etapa afetados.
    mapfile -t RUNNERS < <(
        for step_dir in "${STEP_DIRS[@]}"; do
            find "${PROJECT_ROOT}/${step_dir}" \
                -maxdepth 1 -type f \
                \( -name 'run-step*.sh' -o -name 'run*.sh' \) \
                -printf '%p\n' 2>/dev/null || true
        done | sort -u
    )

    if ((${#RUNNERS[@]} == 1)); then
        RUNNER="${RUNNERS[0]}"
    elif ((${#RUNNERS[@]} == 0)); then
        die "Nenhum run*.sh encontrado na etapa atualizada."
    else
        echo
        echo "Foram encontrados vários scripts de execução:"
        for i in "${!RUNNERS[@]}"; do
            printf '  [%d] %s\n' "$((i + 1))" "${RUNNERS[$i]#${PROJECT_ROOT}/}"
        done
        echo
        read -r -p "Escolha o número do script a executar: " choice
        [[ "${choice}" =~ ^[0-9]+$ ]] || die "Seleção inválida."
        ((choice >= 1 && choice <= ${#RUNNERS[@]})) || die "Seleção fora do intervalo."
        RUNNER="${RUNNERS[$((choice - 1))]}"
    fi
fi

chmod 0755 "${RUNNER}"

echo
echo "=============================================================================="
echo "PACOTE INSTALADO"
echo "=============================================================================="
echo "Pacote : ${PACKAGE_BASENAME}"
echo "Runner : ${RUNNER#${PROJECT_ROOT}/}"
echo "Projeto: ${PROJECT_ROOT}"
echo "=============================================================================="
echo

# ------------------------------------------------------------------------------
# Executa a etapa a partir da raiz do projeto.
# ------------------------------------------------------------------------------
cd "${PROJECT_ROOT}"

info "Iniciando execução..."
"${RUNNER}"

status=$?

echo
echo "=============================================================================="
if [[ ${status} -eq 0 ]]; then
    echo "PACOTE EXECUTADO COM SUCESSO"
else
    echo "PACOTE TERMINOU COM CÓDIGO DE ERRO: ${status}"
fi
echo "=============================================================================="

exit "${status}"
