#!/usr/bin/env bash
# Build an FDV model from versioned config. Runs on ai-server (where ollama lives).
#
# Usage:
#   scripts/fdv_build.sh v3              # local build (if ollama is installed locally)
#   ssh ai-server 'cd ~/ai-server && scripts/fdv_build.sh v3'
set -euo pipefail

VER=${1:-v3}
cd "$(dirname "$0")/.."

if [ ! -f "configs/fdv/Modelfile.${VER}" ]; then
  echo "no configs/fdv/Modelfile.${VER}"
  exit 1
fi

.venv/bin/python -m aiserver.fdv.build "${VER}"
