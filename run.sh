#!/usr/bin/env bash
set -euo pipefail
if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
if ! python3 -c "import flask,requests,bs4,lxml" >/dev/null 2>&1; then
  python3 -m pip install -r requirements.txt
fi
python3 tools/fast_bootstrap.py
export HOST="${HOST:-127.0.0.1}"
export PORT="${PORT:-5012}"
export FLASK_DEBUG="${FLASK_DEBUG:-0}"
export PYTHONUNBUFFERED=1
# The evaluation cache is prepared ahead of time. Keep local navigation responsive
# instead of starting a full NCAA/player-stat warm crawl on every bash run.sh.
export CXI_DISABLE_WARM_CACHE="${CXI_DISABLE_WARM_CACHE:-1}"
python3 app.py
