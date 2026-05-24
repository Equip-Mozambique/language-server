#!/usr/bin/env bash
# Sync local project -> server. Run from project root.
set -euo pipefail

rsync -avz --delete \
    --exclude='.venv' \
    --exclude='__pycache__' \
    --exclude='.git' \
    --exclude='data/cache' \
    --exclude='data/models' \
    --exclude='data/audio' \
    --exclude='.DS_Store' \
    --exclude='.env' \
    --exclude='.env.local' \
    ./ ai-server:~/ai-server/

echo "Synced to ai-server:~/ai-server/"
