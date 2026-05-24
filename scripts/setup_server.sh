#!/usr/bin/env bash
# One-shot setup on ai-server. Idempotent.
set -euo pipefail

cd ~/ai-server

# uv-managed venv (Python 3.12)
if [ ! -d .venv ]; then
    uv venv --python 3.12
fi

# Install with CUDA 12.4 wheel index for torch
uv pip install \
    --index-strategy unsafe-best-match \
    --extra-index-url https://download.pytorch.org/whl/cu124 \
    -e .

# System deps for audio
if ! command -v ffmpeg >/dev/null; then
    echo "ffmpeg missing — run: sudo apt-get install -y ffmpeg"
fi

# HF cache dir on big disk
export HF_HOME="${HF_HOME:-$HOME/ai-server/data/cache}"
mkdir -p "$HF_HOME"

echo "Setup complete. Activate with: source ~/ai-server/.venv/bin/activate"
echo "HF_HOME=$HF_HOME"
