#!/usr/bin/env bash
set -euo pipefail
export HOST="${HOST:-0.0.0.0}"
export PORT="${PORT:-5012}"
export FLASK_DEBUG="${FLASK_DEBUG:-0}"
exec python3 app.py
