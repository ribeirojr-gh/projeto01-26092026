#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

echo "============================================================"
echo "ETAPA 00 — Preparação dos ambientes de simulação"
echo "============================================================"

./00_prepare_environments.sh "$@" |& tee saida-step00.txt
