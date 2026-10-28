"""Runtime paths shared by the keyboard listener and the web app.

The listener is a separate process from Flask, so both sides must agree on
where the state file lives.  On Linux this is the tmpfs directory used since
the first proof of concept; on Windows ``/run`` does not exist, so the files
live next to the user's local application data.

Nothing here creates directories: on Linux ``/run/vqsting`` is created by the
root part of the listener, and the web app must never try to write into /run.
"""

import os
import sys
import tempfile

IS_WINDOWS = sys.platform.startswith("win")


def run_dir():
    """Directory that holds keyboards.json, listener.pid and open.sock."""
    if IS_WINDOWS:
        base = os.environ.get("LOCALAPPDATA") or tempfile.gettempdir()
    else:
        base = "/run"
    return os.path.join(base, "vqsting")


def state_file():
    return os.path.join(run_dir(), "keyboards.json")


def pid_file():
    return os.path.join(run_dir(), "listener.pid")


def open_socket_file():
    return os.path.join(run_dir(), "open.sock")
