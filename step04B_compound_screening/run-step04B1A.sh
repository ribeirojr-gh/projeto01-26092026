#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
"${SCRIPT_DIR}/04B1A_run_R5.sh" |& tee "${SCRIPT_DIR}/saida-step04B1A-R5.txt"
