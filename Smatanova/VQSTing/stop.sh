#!/usr/bin/env bash
# Vypne keyboard listener (práva k /dev/input tým zanikajú).
PID=$(cat /run/vqsting/listener.pid 2>/dev/null) || { echo "listener nebeží"; exit 0; }
kill "$PID" && echo "listener stopped (pid $PID)"
