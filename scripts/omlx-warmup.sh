#!/usr/bin/env bash
# omlx-warmup — ensure omlx server is running and weights are in cache.
#
# Run once at session start. Cuts the cold-load latency (~30s) off the
# first real omlx-write call.
#
# Usage: scripts/omlx-warmup.sh [--model M]
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OMLX="$ROOT/.claude/skills/omlx/omlx.sh"

MODEL_FLAG=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --model) MODEL_FLAG=(--model "$2"); shift 2 ;;
    -h|--help) sed -n '2,9p' "$0"; exit 0 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

status_line="$("$OMLX" server status 2>&1 || true)"
echo "[warmup] status: $status_line"

if ! echo "$status_line" | grep -q "running"; then
  echo "[warmup] starting server..."
  "$OMLX" server start
fi

echo "[warmup] firing 1-token throwaway to load weights..."
mkdir -p "$ROOT/work"
"$OMLX" ${MODEL_FLAG[@]+"${MODEL_FLAG[@]}"} --max-tokens 4 --out "$ROOT/work/.warmup" -p "ping"
rm -f "$ROOT/work/.warmup" "$ROOT/work/.warmup.raw"

echo "[warmup] ready"
