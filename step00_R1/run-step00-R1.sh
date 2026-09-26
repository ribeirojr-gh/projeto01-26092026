#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

echo "============================================================"
echo "ETAPA 00-R1 — Correção do GPAW/MPI"
echo "============================================================"

./00_repair_gpaw_mpi.sh |& tee saida-step00-R1.txt
