#!/usr/bin/env bash
set -Eeuo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

if [[ -f .env ]]; then
  set -a
  source .env
  set +a
fi

if [[ ! -x .venv/bin/python ]]; then
  echo "Missing .venv. Run scripts/setup_jetson.sh first." >&2
  exit 1
fi

exec .venv/bin/python -m uvicorn jetson.app:app \
  --host "${GATEWAY_HOST:-0.0.0.0}" \
  --port "${GATEWAY_PORT:-8081}"
