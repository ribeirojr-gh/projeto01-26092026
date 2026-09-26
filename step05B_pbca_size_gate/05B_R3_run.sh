#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
source "${PROJECT_ROOT}/scripts/env_manager.sh"

RESULTS="${SCRIPT_DIR}/resultados_step05B_R3"
MONITOR="${RESULTS}/memory_monitor"
mkdir -p "${RESULTS}" "${SCRIPT_DIR}/logs_R3" "${RESULTS}/relax" "${MONITOR}"

MPI_N=8
MIN_MEM_GIB=20

echo "=============================================================================="
echo "STEP 05B-R3 — 8 MPI / DOMAIN-DECOMPOSED GPAW SIZE GATE"
echo "=============================================================================="
echo "Data: $(date)"
echo "Host: $(hostname)"
echo "Projeto: ${PROJECT_ROOT}"
echo

if (( $(nproc) < MPI_N )); then
  echo "ERRO: menos de ${MPI_N} CPUs disponíveis."
  exit 30
fi

available_kb="$(awk '/MemAvailable:/ {print $2}' /proc/meminfo)"
available_gib="$(awk -v kb="${available_kb}" 'BEGIN {printf "%.1f", kb/1024/1024}')"

echo "Memória disponível antes do cálculo: ${available_gib} GiB"

if ! awk -v x="${available_gib}" -v y="${MIN_MEM_GIB}" 'BEGIN {exit !(x>=y)}'; then
  echo "ERRO: menos de ${MIN_MEM_GIB} GiB disponíveis."
  echo "Feche aplicações pesadas e execute novamente."
  exit 31
fi

monitor_memory() {
  local pid="$1"
  local outfile="$2"
  echo "epoch,MemAvailable_kB,SwapFree_kB" > "${outfile}"
  while kill -0 "${pid}" 2>/dev/null; do
    awk '
      /MemAvailable:/ {a=$2}
      /SwapFree:/ {s=$2}
      END {printf "%d,%s,%s\n", systime(), a, s}
    ' /proc/meminfo >> "${outfile}"
    sleep 2
  done
}

summarize_memory() {
  local infile="$1"
  awk -F, '
    NR==2 {min=$2}
    NR>1 && $2<min {min=$2}
    END {
      if (NR>1) printf "Menor MemAvailable observado: %.2f GiB\n", min/1024/1024
    }
  ' "${infile}" || true
}

run_case() {
  local mineral="$1"
  local natoms="$2"
  local json="${RESULTS}/${mineral}_${natoms}_PbCa.json"
  local traj="${RESULTS}/relax/${mineral}_${natoms}_PbCa_relaxed_R3.traj"
  local case_log="${SCRIPT_DIR}/logs_R3/${mineral}_${natoms}_console.txt"
  local memlog="${MONITOR}/${mineral}_${natoms}_memory.csv"

  if [[ -s "${json}" && -s "${traj}" ]]; then
    echo ">>> Reutilizando ${mineral} ${natoms}"
    return
  fi

  local mpi_current=8
  if (( natoms == 80 )); then
    mpi_current=4
  fi

  echo
  echo ">>> ${mineral}: Pb_Ca ${natoms} átomos / ${mpi_current} MPI"

  set +e
  (
    run_in_upb_env gpaw env \
      OMP_NUM_THREADS=1 \
      UPB_PBCA_HOST="${mineral}" \
      UPB_PBCA_NATOMS="${natoms}" \
      mpiexec -n "${mpi_current}" gpaw python \
        "${SCRIPT_DIR}/05B_R3_pbca_case.py"
  ) |& tee "${case_log}" &
  jobpid=$!

  monitor_memory "${jobpid}" "${memlog}" &
  monpid=$!

  wait "${jobpid}"
  status=$?

  kill "${monpid}" 2>/dev/null || true
  wait "${monpid}" 2>/dev/null || true
  set -e

  summarize_memory "${memlog}"

  if (( status != 0 )); then
    echo
    echo "ERRO: ${mineral}/${natoms} terminou com status ${status}."
    echo "Últimos eventos OOM do kernel:"
    journalctl -k -b --no-pager 2>/dev/null \
      | grep -Ei 'oom|out of memory|killed process' \
      | tail -20 || true
    exit "${status}"
  fi
}

# Ordem deliberada: calcita 80 -> 160 primeiro.
# Se 160 não sobreviver em 8 MPI, paramos antes de gastar tempo na dolomita.
run_case calcita 80
run_case calcita 160
run_case dolomita 80
run_case dolomita 160

echo
echo ">>> Análise 80 -> 160"
run_in_upb_env analysis python \
  "${SCRIPT_DIR}/05B_R3_analyze.py" --phase initial

mapfile -t fallback_hosts < <(
  run_in_upb_env analysis python -c '
import json
from pathlib import Path
p=Path("'"${RESULTS}"'")/"fallback_request_step05B_R3.json"
for x in json.loads(p.read_text())["fallback_hosts"]:
    print(x)
'
)

if (( ${#fallback_hosts[@]} > 0 )); then
  echo
  echo ">>> Fallback 240 necessário para: ${fallback_hosts[*]}"
  for mineral in "${fallback_hosts[@]}"; do
    run_case "${mineral}" 240
  done
else
  echo
  echo ">>> 80 -> 160 convergiu para ambos; 240 não será calculado."
fi

echo
echo ">>> Decisão final"
run_in_upb_env analysis python \
  "${SCRIPT_DIR}/05B_R3_analyze.py" --phase final

echo "=============================================================================="
echo "STEP 05B-R3 FINALIZADO"
echo "=============================================================================="
