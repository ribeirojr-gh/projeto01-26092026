#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

"${SCRIPT_DIR}/04B1B1_run.sh" |& tee \
    "${SCRIPT_DIR}/saida-step04B1B1.txt"
