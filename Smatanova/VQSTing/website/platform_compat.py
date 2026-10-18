"""Small cross-platform helpers.

Windows behaviour is unchanged: bundled ``mpv.exe``, ``video\\...`` paths and
opening folders with ``start``.  Linux/macOS get the native equivalents so the
same code runs on both.
"""

import os
import shutil
import subprocess
import sys

IS_WINDOWS = sys.platform.startswith("win")

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def find_mpv():
    """Return the mpv executable to use on this platform."""
    if IS_WINDOWS:
        bundled = os.path.join(APP_DIR, "mpv.exe")
        if os.path.isfile(bundled):
            return bundled
        return shutil.which("mpv.exe") or shutil.which("mpv") or "mpv.exe"
    return shutil.which("mpv") or "mpv"


def video_path(*parts):
    """Build a path inside the ``video/`` folder for the current platform."""
    return os.path.join("video", *parts)


def play_videos(*paths):
    """Play one or more videos fullscreen in mpv and block until it closes."""
    command = [
        find_mpv(),
        "--cursor-autohide=0",
        "--osc=no",
        "--no-input-default-bindings",
        "--ontop",
        "--fs",
        *paths,
    ]
    return subprocess.call(command)


def open_folder(path):
    """Open a folder in the system file manager."""
    if IS_WINDOWS:
        return subprocess.call(["start", path], shell=True)
    opener = "open" if sys.platform == "darwin" else "xdg-open"
    return subprocess.call([opener, path])
