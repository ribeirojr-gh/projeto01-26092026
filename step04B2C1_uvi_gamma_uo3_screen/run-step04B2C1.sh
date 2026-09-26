#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
"${SCRIPT_DIR}/04B2C1_run.sh" |& tee \
  "${SCRIPT_DIR}/saida-step04B2C1.txt"
