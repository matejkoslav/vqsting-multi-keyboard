#!/usr/bin/env bash
# Spustí keyboard listener (root len na otvorenie /dev/input, hneď zhodí práva)
# + Flask appku. Ctrl+C vypne oboje.
set -e
cd "$(dirname "$0")"
SCRIPT_DIR="$PWD"

PY="$HOME/.venvs/vqsting/bin/python"
[ -x "$PY" ] || PY=python3

pkexec "$PY" "$SCRIPT_DIR/tools/keyboard_listener.py" &
LISTENER=$!
trap 'kill "$(cat /run/vqsting/listener.pid 2>/dev/null)" 2>/dev/null || true' EXIT

"$PY" main.py
