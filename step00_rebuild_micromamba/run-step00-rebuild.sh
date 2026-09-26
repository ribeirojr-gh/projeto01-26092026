#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"
{
    echo "=============================================================================="
    echo "STEP00-R — RECONSTRUÇÃO MICROMAMBA NO PREFIXO ATUAL"
    echo "=============================================================================="
    echo "Data: $(date)"
    echo "Host: $(hostname)"
    "${SCRIPT_DIR}/00_rebuild_envs.sh"
    "${SCRIPT_DIR}/01_validate_envs.sh"
} |& tee "${SCRIPT_DIR}/saida-step00-rebuild.txt"
