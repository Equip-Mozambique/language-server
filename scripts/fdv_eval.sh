#!/usr/bin/env bash
# Run the FDV eval set against a built ollama model.
#
# Usage:
#   ssh ai-server 'cd ~/ai-server && scripts/fdv_eval.sh fdv06-v3'
set -euo pipefail

MODEL=${1:-fdv06-v2}
cd "$(dirname "$0")/.."

.venv/bin/python -m aiserver.fdv.eval "${MODEL}" \
  --eval data/fdv/eval/real_whatsapp.example.jsonl \
  --host http://localhost:11434
