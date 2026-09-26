#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

{
    echo "=============================================================================="
    echo "STEP00-FIX — GPAW MPI"
    echo "=============================================================================="
    echo "Data: $(date)"
    echo "Host: $(hostname)"
    echo

    "${SCRIPT_DIR}/repair_gpaw_mpi.sh"

} |& tee "${SCRIPT_DIR}/saida-step00-fix-gpaw-mpi.txt"
