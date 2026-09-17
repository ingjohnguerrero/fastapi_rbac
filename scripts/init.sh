#!/usr/bin/env bash
# First-time operator bootstrap: project venv, requirements, then schema/admin seed.
set -euo pipefail
cd "$(dirname "$0")/.."

python_with_deps() {
  local candidate="$1"
  if [ -x "$candidate" ] && "$candidate" -c "import pydantic, sqlalchemy, jwt, pwdlib, fastapi" >/dev/null 2>&1; then
    printf '%s' "$candidate"
    return 0
  fi
  return 1
}

PY=""
if [ -n "${VIRTUAL_ENV:-}" ] && PY="$(python_with_deps "$VIRTUAL_ENV/bin/python")"; then
  :
elif PY="$(python_with_deps .venv/bin/python)"; then
  :
elif command -v python3 >/dev/null && PY="$(python_with_deps "$(command -v python3)")"; then
  :
else
  if ! command -v python3 >/dev/null; then
    echo "error: python3 is required to create .venv" >&2
    exit 1
  fi
  if [ ! -x .venv/bin/python ]; then
    echo "init: creating .venv"
    python3 -m venv .venv
  fi
  PY=".venv/bin/python"
  echo "init: installing requirements.txt into $PY"
  "$PY" -m pip install -r requirements.txt
fi

exec "$PY" -m app.cli init
