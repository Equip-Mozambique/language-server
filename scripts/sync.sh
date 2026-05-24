#!/usr/bin/env bash
# Sync local project -> server. Run from project root.
#
# CRITICAL: NEVER use --delete. Other programmers work directly on the server.
# Sync is ADD/UPDATE only. The server is the source of truth for any file we
# don't have locally; deleting would destroy their work.
#
# Notable consequence: files renamed/removed locally will NOT be removed on
# server. Clean those up manually with explicit SSH if needed.
set -euo pipefail

rsync -avz \
    --exclude='.venv' \
    --exclude='__pycache__' \
    --exclude='.git' \
    --exclude='data/cache' \
    --exclude='data/models' \
    --exclude='data/audio' \
    --exclude='data/research' \
    --exclude='data/crawl_unlocked.json' \
    --exclude='.DS_Store' \
    --exclude='.env' \
    --exclude='.env.local' \
    ./ ai-server:~/ai-server/

echo "Synced to ai-server:~/ai-server/ (add/update only — no deletions)"
