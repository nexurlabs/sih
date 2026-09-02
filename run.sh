#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi
python3 -m pip install -q -r requirements.txt
python3 scripts/write_samples.py
python3 -m pytest -q
PORT="${MAILTRACE_PORT:-8777}"
exec python3 -m uvicorn app:app --host 127.0.0.1 --port "$PORT"
