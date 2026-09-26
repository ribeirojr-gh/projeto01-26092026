#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
"${SCRIPT_DIR}/05B_R3_run.sh" |& tee \
  "${SCRIPT_DIR}/saida-step05B-R3.txt"
