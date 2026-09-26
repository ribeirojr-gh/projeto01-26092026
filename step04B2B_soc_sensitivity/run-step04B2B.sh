#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

"${SCRIPT_DIR}/04B2B_run_R3.sh" |& tee \
  "${SCRIPT_DIR}/saida-step04B2B-R3.txt"
