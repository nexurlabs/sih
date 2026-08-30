#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python3 -m pip install -q -r requirements.txt
python3 scripts/write_samples.py
python3 -m pytest -q
exec python3 -m uvicorn app:app --host 127.0.0.1 --port 8000
