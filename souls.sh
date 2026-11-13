#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PYTHON=${PYTHON:-python3}
VENV="$ROOT/.venv"
MARKER="$VENV/.souls-installed"

if ! command -v "$PYTHON" >/dev/null 2>&1; then
    echo "Python 3.10 or newer is required. Install it, then run ./souls.sh again." >&2
    exit 1
fi

if ! "$PYTHON" -c 'import sys; raise SystemExit(sys.version_info < (3, 10))'; then
    echo "Python 3.10 or newer is required; found $("$PYTHON" --version 2>&1)." >&2
    exit 1
fi

if [ ! -x "$VENV/bin/python" ]; then
    "$PYTHON" -m venv "$VENV"
fi

if [ ! -f "$MARKER" ] || [ "$ROOT/pyproject.toml" -nt "$MARKER" ]; then
    "$VENV/bin/python" -m pip install --editable "$ROOT"
    touch "$MARKER"
fi

exec "$VENV/bin/python" -m soulseek_tui "$@"
