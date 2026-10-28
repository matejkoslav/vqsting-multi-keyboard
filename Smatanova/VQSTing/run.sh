#!/usr/bin/env bash
# Spustí keyboard listener (root len na otvorenie /dev/input, hneď zhodí práva)
# + Flask appku. Ctrl+C vypne oboje.
set -e
cd "$(dirname "$0")"
SCRIPT_DIR="$PWD"

PY="$HOME/.venvs/vqsting/bin/python"
[ -x "$PY" ] || PY=python3

PID_FILE=/run/vqsting/listener.pid
RUNNING_PID=$(cat "$PID_FILE" 2>/dev/null || true)

if [ -n "$RUNNING_PID" ] && kill -0 "$RUNNING_PID" 2>/dev/null; then
    echo "listener už beží (pid $RUNNING_PID) — nespúšťam druhý"
else
    rm -f "$PID_FILE"
    pkexec "$PY" "$SCRIPT_DIR/tools/keyboard_listener.py" &
    for _ in $(seq 1 50); do
        [ -s "$PID_FILE" ] && break
        sleep 0.1
    done
    if [ -s "$PID_FILE" ]; then
        echo "listener beží (pid $(cat "$PID_FILE"))"
    else
        echo "listener sa nespustil (pkexec zrušený?) — appka pobeží bez klávesníc" >&2
    fi
fi

trap 'kill "$(cat /run/vqsting/listener.pid 2>/dev/null)" 2>/dev/null || true' EXIT

"$PY" main.py
