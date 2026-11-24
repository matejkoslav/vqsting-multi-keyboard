"""Stav klávesníc pre stránku /keyboards.

Dáta píše tools/keyboard_listener.py (Linux) alebo
tools/windows_keyboard_listener.py (Windows) — jediné procesy, ktoré čítajú
vstupné zariadenia.  Tu sa len čítajú; Flask k zariadeniam nikdy nepristupuje.
"""

import json
import os
import platform
import time

from state_paths import pid_file, state_file

STATE = state_file()
PID = pid_file()

SUPPORTED = ("Linux", "Windows")


def _alive_windows(pid):
    """OpenProcess with a query-only right: never terminates anything.

    ``os.kill(pid, 0)`` is not usable here — on Windows it calls
    TerminateProcess instead of checking existence.
    """
    import ctypes

    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    handle = ctypes.windll.kernel32.OpenProcess(
        PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not handle:
        return False
    ctypes.windll.kernel32.CloseHandle(handle)
    return True


def _listener_alive():
    try:
        with open(PID) as f:
            pid = int(f.read())
        if platform.system() == "Windows":
            return _alive_windows(pid)
        os.kill(pid, 0)
        return True
    except (OSError, ValueError):
        return False


def _read_state():
    """Read keyboards.json. On Windows the listener may be replacing the file at
    this very moment (open/replace collide), so try a few times before giving up;
    an empty answer would make keys look lost or late."""
    for attempt in range(5):
        try:
            with open(STATE) as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except (OSError, ValueError):
            time.sleep(0.002)
    return {}


def state():
    system = platform.system()
    if system not in SUPPORTED:
        return {
            "platform": system,
            "supported": False,
            "listener": False,
            "devices": [],
            "events": [],
            "seq": 0,
            "age": None,
        }

    data = _read_state()

    alive = _listener_alive()
    return {
        "platform": system,
        "supported": True,
        "listener": alive,
        "devices": data.get("devices", []) if alive else [],
        "events": data.get("events", []) if alive else [],
        "seq": data.get("seq", 0) if alive else 0,
        "age": round(time.time() - data["ts"], 1) if alive and "ts" in data else None,
    }
