"""Stav klávesníc pre stránku /keyboards.

Dáta píše tools/keyboard_listener.py (jediný proces s prístupom k /dev/input).
Tu sa len čítajú — Flask k zariadeniam nikdy nepristupuje.
"""

import json
import os
import platform
import time

STATE = "/run/vqsting/keyboards.json"
PID = "/run/vqsting/listener.pid"


def _listener_alive():
    try:
        with open(PID) as f:
            pid = int(f.read())
        os.kill(pid, 0)
        return True
    except (OSError, ValueError):
        return False


def state():
    system = platform.system()
    if system != "Linux":
        # Never touch /run or call os.kill on Windows: os.kill(pid, 0)
        # terminates the process there instead of checking it.
        return {
            "platform": system,
            "supported": False,
            "listener": False,
            "devices": [],
            "age": None,
        }

    try:
        with open(STATE) as f:
            data = json.load(f)
    except (OSError, ValueError):
        data = {}

    alive = _listener_alive()
    return {
        "platform": system,
        "supported": True,
        "listener": alive,
        "devices": data.get("devices", []) if alive else [],
        "age": round(time.time() - data["ts"], 1) if alive and "ts" in data else None,
    }
