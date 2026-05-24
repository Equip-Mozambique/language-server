#!/usr/bin/env bash
# omlx-write — wrapper around `.claude/skills/omlx/omlx.sh` with:
#   - hard timeout (default 90s)
#   - automatic markdown-fence stripping
#   - lint pass (ruff for .py, tsc for .ts/.tsx) with one auto-retry
#
# Usage:
#   scripts/omlx-write.sh --out path/to/file.py --prompt "spec text..."
#   scripts/omlx-write.sh --out path/to/file.py --prompt-file prompts/foo.md
#   scripts/omlx-write.sh --out path/to/file.py --max-tokens 4096 \
#                         --model mlx-community/DeepSeek-V3.2-Speciale-4bit \
#                         --prompt "..."
#
# Exits non-zero if lint still fails after one retry.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OMLX="$ROOT/.claude/skills/omlx/omlx.sh"
TIMEOUT="${OMLX_TIMEOUT:-90}"
MAX_TOKENS="${OMLX_MAX_TOKENS:-3000}"
MODEL_FLAG=()
OUT=""
PROMPT=""
PROMPT_FILE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --out) OUT="$2"; shift 2 ;;
    --prompt) PROMPT="$2"; shift 2 ;;
    --prompt-file) PROMPT_FILE="$2"; shift 2 ;;
    --max-tokens) MAX_TOKENS="$2"; shift 2 ;;
    --timeout) TIMEOUT="$2"; shift 2 ;;
    --model) MODEL_FLAG=(--model "$2"); shift 2 ;;
    -h|--help) sed -n '2,18p' "$0"; exit 0 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

if [[ -z "$OUT" ]]; then
  echo "error: --out required" >&2
  exit 2
fi
if [[ -z "$PROMPT" && -z "$PROMPT_FILE" ]]; then
  echo "error: --prompt or --prompt-file required" >&2
  exit 2
fi
if [[ -n "$PROMPT_FILE" ]]; then
  PROMPT="$(cat "$PROMPT_FILE")"
fi

mkdir -p "$(dirname "$OUT")"

strip_fences() {
  # Remove leading "```lang" and trailing "```" markdown fences.
  local f="$1"
  python3 - "$f" <<'PY'
import sys, re, pathlib
p = pathlib.Path(sys.argv[1])
t = p.read_text()
# strip wrapping fences if both ends present
lines = t.splitlines()
while lines and lines[0].strip() == "":
    lines.pop(0)
while lines and lines[-1].strip() == "":
    lines.pop()
if lines and re.match(r"^```[\w+-]*$", lines[0]):
    lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
p.write_text("\n".join(lines) + ("\n" if lines else ""))
PY
}

lint_file() {
  local f="$1"
  case "$f" in
    *.py)
      local RUFF="$ROOT/.venv/bin/ruff"
      if [[ ! -x "$RUFF" ]]; then RUFF="$(command -v ruff || true)"; fi
      if [[ -n "$RUFF" ]]; then
        # E9 = syntax errors. F821 = undefined names. F401 = unused imports.
        # Skip stylistic rules (B, etc.) so the wrapper doesn't reject for
        # pre-existing issues in input sources.
        "$RUFF" check --no-cache --select E9,F821,F401,F811 "$f" 2>&1
      else
        python3 -c "import ast; ast.parse(open('$f').read())" 2>&1
      fi
      ;;
    *.ts|*.tsx)
      if [[ -x "$ROOT/frontend/node_modules/.bin/tsc" ]]; then
        ( cd "$ROOT/frontend" && node_modules/.bin/tsc --noEmit --target ES2022 --module ESNext \
          --moduleResolution bundler --strict --skipLibCheck --jsx preserve "$f" ) 2>&1
      else
        echo "(no tsc, skipping)"
        return 0
      fi
      ;;
    *) echo "(no linter for $f, skipping)"; return 0 ;;
  esac
}

run_once() {
  local prompt="$1"
  local rendered="${OUT}.raw"
  # Pipe via gtimeout/timeout to enforce ceiling. macOS = no GNU timeout by default.
  # Portable timeout via perl alarm (BSD/macOS lack GNU `timeout`).
  if command -v gtimeout >/dev/null 2>&1; then
    gtimeout "$TIMEOUT" "$OMLX" ${MODEL_FLAG[@]+"${MODEL_FLAG[@]}"} --max-tokens "$MAX_TOKENS" --out "$rendered" -p "$prompt"
  elif command -v timeout >/dev/null 2>&1; then
    timeout "$TIMEOUT" "$OMLX" ${MODEL_FLAG[@]+"${MODEL_FLAG[@]}"} --max-tokens "$MAX_TOKENS" --out "$rendered" -p "$prompt"
  else
    perl -e 'alarm shift; exec @ARGV' "$TIMEOUT" \
      "$OMLX" ${MODEL_FLAG[@]+"${MODEL_FLAG[@]}"} --max-tokens "$MAX_TOKENS" --out "$rendered" -p "$prompt"
  fi
  mv "$rendered" "$OUT"
  strip_fences "$OUT"
}

echo "[omlx-write] generating $OUT (timeout=${TIMEOUT}s, max_tokens=$MAX_TOKENS)"
run_once "$PROMPT"

set +e
LINT_OUT="$(lint_file "$OUT")"
LINT_STATUS=$?
set -e

if [[ $LINT_STATUS -eq 0 ]]; then
  echo "[omlx-write] OK ($(wc -l < "$OUT") lines, lint clean)"
  exit 0
fi

echo "[omlx-write] lint failed:"
echo "$LINT_OUT" | head -20
echo "[omlx-write] retrying with error feedback..."

RETRY_PROMPT=$(cat <<EOF
Your previous output failed lint with these errors:

$LINT_OUT

Original spec:

$PROMPT

Re-output ONLY corrected code. No fences. No commentary.
EOF
)

set +e
run_once "$RETRY_PROMPT"
LINT_OUT2="$(lint_file "$OUT")"
LINT_STATUS2=$?
set -e

if [[ $LINT_STATUS2 -eq 0 ]]; then
  echo "[omlx-write] retry OK"
  exit 0
fi

echo "[omlx-write] retry still failing:"
echo "$LINT_OUT2" | head -20
echo "[omlx-write] FAIL — Claude needs to take over"
exit 1
