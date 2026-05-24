#!/usr/bin/env bash
# Build the Angular frontend locally, then sync source + dist to ai-server.
# Assumes:
#   - `ssh ai-server` works (CLAUDE.md alias)
#   - remote project lives at ~/ai-server
#   - remote `uv` is on PATH
set -euo pipefail

cd "$(dirname "$0")/.."
ROOT="$(pwd)"

echo "==> building Angular frontend"
( cd frontend && npm run build )

echo "==> rsync source to ai-server:~/ai-server"
rsync -avz --delete --exclude '.venv' --exclude '__pycache__' --exclude 'node_modules' \
      --exclude 'work' --exclude '.git' --exclude 'data/cache' --exclude 'data/models' \
      --exclude 'frontend/.angular' \
      "${ROOT}/" ai-server:~/ai-server/

echo "==> remote: uv sync + smoke"
ssh ai-server bash -lc '
  set -euo pipefail
  cd ~/ai-server
  uv sync --extra dev
  uv run python -c "from aiserver.api.app import app; print(\"OK\", app.title)"
'

echo
echo "Deploy complete. To run the server on the tailnet IP:"
echo "  ssh ai-server"
echo "  cd ~/ai-server"
echo "  uv run aisrv serve --host 100.94.161.30 --port 8000 --preload"
echo
echo "Then from another tailnet device:"
echo "  open http://eu-ai1:8000"
