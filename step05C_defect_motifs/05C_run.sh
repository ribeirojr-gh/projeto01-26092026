#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
source "${PROJECT_ROOT}/scripts/env_manager.sh"

RESULTS="${SCRIPT_DIR}/results"
LOGS="${SCRIPT_DIR}/logs"
RELAX="${RESULTS}/relax"
MONITOR="${RESULTS}/memory_monitor"
mkdir -p "${RESULTS}" "${LOGS}" "${RELAX}" "${MONITOR}"

MPI_N=8
MIN_MEM_GIB=18

echo "=============================================================================="
echo "STEP 05C — FIRST-PRINCIPLES DFT (GPAW PW) DEFECT MOTIFS & COMPENSATION"
echo "=============================================================================="
echo "Date: $(date)"
echo "Host: $(hostname)"
echo "Project: ${PROJECT_ROOT}"
echo

if (( $(nproc) < MPI_N )); then
  echo "ERROR: fewer than ${MPI_N} CPUs available."
  exit 30
fi

available_kb="$(awk '/MemAvailable:/ {print $2}' /proc/meminfo)"
available_gib="$(awk -v kb="${available_kb}" 'BEGIN {printf "%.1f", kb/1024/1024}')"
echo "Available memory: ${available_gib} GiB"

if ! awk -v x="${available_gib}" -v y="${MIN_MEM_GIB}" 'BEGIN {exit !(x>=y)}'; then
  echo "ERROR: less than ${MIN_MEM_GIB} GiB available."
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
      if (NR>1) printf "Lowest MemAvailable observed: %.2f GiB\n", min/1024/1024
    }
  ' "${infile}" || true
}

run_dft_motif() {
  local tag="$1"
  local json="${RESULTS}/${tag}.json"
  local traj="${RELAX}/${tag}_relaxed.traj"
  local console_log="${LOGS}/${tag}_console.txt"
  local memlog="${MONITOR}/${tag}_memory.csv"

  if [[ -s "${json}" && -s "${traj}" ]]; then
    echo ">>> Reusing converged calculation: ${tag}"
    return 0
  fi

  echo
  echo ">>> Launching GPAW DFT for motif: ${tag} (${MPI_N} MPI ranks)"

  set +e
  (
    run_in_upb_env gpaw env \
      PYTHONUNBUFFERED=1 \
      PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH:-}" \
      OMP_NUM_THREADS=1 \
      UPB_MOTIF_TAG="${tag}" \
      mpiexec -n "${MPI_N}" gpaw python \
        "${SCRIPT_DIR}/05C_dft_case.py"
  ) |& tee "${console_log}" &
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
    echo "ERROR: ${tag} failed with status ${status}."
    exit "${status}"
  fi
}

# 1. Structure generation (if needed)
if [[ ! -f "${SCRIPT_DIR}/structures/motifs_manifest.json" ]]; then
  echo ">>> Generating defect structures..."
  run_in_upb_env structures python "${SCRIPT_DIR}/05C_enumerate_motifs.py"
fi

# 2. Fast MLIP pre-screening (if needed)
if [[ ! -f "${RESULTS}/prescreening_summary.json" ]]; then
  echo ">>> Running CHGNet fast pre-screening..."
  run_in_upb_env mlip python "${SCRIPT_DIR}/05C_prescreen_motifs.py"
  python3 "${SCRIPT_DIR}/05C_analyze_prescreening.py"
fi

# 3. High-Priority First-Principles DFT Executions (GPAW Plane-Wave Local)
echo
echo "=============================================================================="
echo "RUNNING HIGH-PRIORITY FIRST-PRINCIPLES DFT CALCULATIONS"
echo "=============================================================================="

# Priority 1: U(IV) in Calcite with vacancy compensation
run_dft_motif "calcita_160_U_Ca_V_Ca_NN"

# Priority 2: U(IV) in Dolomite with selective Mg vacancy compensation
run_dft_motif "dolomita_160_U_Ca_V_Mg_NN"

# Priority 3: Pb on Mg site in Dolomite (site-preference benchmark)
run_dft_motif "dolomita_160_Pb_Mg"

# Priority 4: Oxidative interstitial compensation
run_dft_motif "calcita_160_U_Ca_Oi"
run_dft_motif "dolomita_160_U_Ca_Oi"

# Automated Google Drive Sync
echo
echo ">>> Automated Mirroring to Google Drive"
python3 "${PROJECT_ROOT}/scripts/sync_to_gdrive.py" || true

echo "=============================================================================="
echo "STEP 05C COMPLETED SUCCESSFULLY"
echo "=============================================================================="
