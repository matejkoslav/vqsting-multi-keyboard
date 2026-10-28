#!/usr/bin/env bash
# Vypne keyboard listener (práva k /dev/input tým zanikajú).
# Nikdy nezabíja cudzí proces: pid sa overuje proti /proc/<pid>/cmdline.
PID_FILE=/run/vqsting/listener.pid
PID=$(cat "$PID_FILE" 2>/dev/null || true)

if [ -z "$PID" ]; then
    echo "listener nebeží (chýba $PID_FILE)"
    exit 0
fi

if ! kill -0 "$PID" 2>/dev/null; then
    echo "listener nebeží (pid $PID už neexistuje) — mažem stale pid"
    rm -f "$PID_FILE"
    exit 0
fi

if ! grep -qa keyboard_listener /proc/"$PID"/cmdline 2>/dev/null; then
    echo "pid $PID nie je keyboard listener — nič nezabíjam, nič nemažem" >&2
    exit 1
fi

kill "$PID" 2>/dev/null || true
for _ in $(seq 1 20); do
    kill -0 "$PID" 2>/dev/null || break
    sleep 0.1
done

if kill -0 "$PID" 2>/dev/null; then
    echo "listener (pid $PID) sa neukončil do 2 s" >&2
    exit 1
fi

rm -f "$PID_FILE"
echo "listener stopped (pid $PID)"
