#!/usr/bin/env bash
set -u
set -o pipefail

PROJECT_ROOT="$(pwd)"
STEP_DIR="${PROJECT_ROOT}/step05B_pbca_size_gate"
CASE_SCRIPT="${STEP_DIR}/05B_R2_pbca_case.py"
ENV_MANAGER="${PROJECT_ROOT}/scripts/env_manager.sh"

OUTDIR="${STEP_DIR}/diagnostico_memoria_R2"
MAIN_LOG="${OUTDIR}/saida-step05B-memory-diagnostic.txt"
DRY4="${OUTDIR}/dryrun-step05B-R2-calcita80-4MPI.txt"
DRY8="${OUTDIR}/dryrun-step05B-R2-calcita80-8MPI.txt"
SUMMARY="${OUTDIR}/resumo-step05B-memory-diagnostic.txt"

mkdir -p "${OUTDIR}"

if [[ ! -f "${ENV_MANAGER}" ]]; then
    echo "ERRO: não encontrei ${ENV_MANAGER}"
    exit 10
fi

if [[ ! -f "${CASE_SCRIPT}" ]]; then
    echo "ERRO: não encontrei ${CASE_SCRIPT}"
    echo "Confirme que o pacote Step05B-R2 foi instalado corretamente."
    exit 11
fi

source "${ENV_MANAGER}"

{
    echo "======================================================================"
    echo "STEP 05B-R2 - DIAGNÓSTICO DE MEMÓRIA / DRY-RUN"
    echo "======================================================================"
    echo "Data: $(date)"
    echo "Host: $(hostname)"
    echo "Projeto: ${PROJECT_ROOT}"
    echo
    echo "IMPORTANTE: este script NÃO executa um SCF real."
    echo "Ele coleta memória disponível e faz dry-run do GPAW para 4 e 8 processos."
    echo

    echo ">>> CPU"
    echo "nproc = $(nproc)"
    lscpu 2>/dev/null | grep -E '^(CPU\(s\)|Core|Thread|Socket|Model name)' || true
    echo

    echo ">>> MEMÓRIA"
    free -h || true
    echo

    echo ">>> SWAP"
    swapon --show || true
    echo

    echo ">>> LIMITES DO SHELL"
    ulimit -a || true
    echo

    echo ">>> 20 PROCESSOS COM MAIOR RSS"
    ps -eo pid,user,%cpu,%mem,rss,cmd --sort=-rss | head -21 || true
    echo

    echo ">>> Script GPAW analisado"
    echo "${CASE_SCRIPT}"
    echo

    echo "======================================================================"
    echo "DRY-RUN 4 PROCESSOS"
    echo "======================================================================"
} |& tee "${MAIN_LOG}"

set +e
UPB_PBCA_HOST=calcita UPB_PBCA_NATOMS=80 run_in_upb_env gpaw     gpaw python --dry-run=4 "${CASE_SCRIPT}"     |& tee "${DRY4}"
status4=${PIPESTATUS[0]}
set -e

{
    echo
    echo "[STATUS] dry-run 4 processos = ${status4}"
    echo
    echo "======================================================================"
    echo "DRY-RUN 8 PROCESSOS"
    echo "======================================================================"
} |& tee -a "${MAIN_LOG}"

set +e
UPB_PBCA_HOST=calcita UPB_PBCA_NATOMS=80 run_in_upb_env gpaw     gpaw python --dry-run=8 "${CASE_SCRIPT}"     |& tee "${DRY8}"
status8=${PIPESTATUS[0]}
set -e

{
    echo
    echo "[STATUS] dry-run 8 processos = ${status8}"
    echo
    echo "======================================================================"
    echo "RESUMO AUTOMÁTICO"
    echo "======================================================================"
} |& tee -a "${MAIN_LOG}"

{
    echo "=== 4 PROCESSOS ==="
    grep -iE 'memory|ram|parallel|domain|band|k-point|kpoint|scalapack|cores|process|rank|grid' "${DRY4}" || true

    echo
    echo "=== 8 PROCESSOS ==="
    grep -iE 'memory|ram|parallel|domain|band|k-point|kpoint|scalapack|cores|process|rank|grid' "${DRY8}" || true

    echo
    echo "=== STATUS ==="
    echo "dry-run 4 processos: ${status4}"
    echo "dry-run 8 processos: ${status8}"
} | tee "${SUMMARY}"

{
    echo
    echo "Arquivos gerados:"
    echo "  ${MAIN_LOG}"
    echo "  ${DRY4}"
    echo "  ${DRY8}"
    echo "  ${SUMMARY}"
    echo
    echo "Envie estes quatro arquivos para análise antes de rodar novamente o Step05B."
    echo "======================================================================"
} |& tee -a "${MAIN_LOG}"

if [[ ${status4} -ne 0 && ${status8} -ne 0 ]]; then
    exit 20
fi
exit 0
