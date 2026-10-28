"""Listener klávesníc (Linux). Beží oddelene od Flasku a jediný číta /dev/input.

Spustenie:  pkexec python tools/keyboard_listener.py

Rozdelenie práv:
- root "opener" — jediná vec: na požiadanie otvorí /dev/input/eventN a pošle
  späť file descriptor. Sám žiadne klávesy nečíta.
- potomok beží ako prihlásený user (PKEXEC_UID), číta eventy a zapisuje stav.

Prístup k zariadeniam držia len otvorené fds — zanikajú so skončením procesov.
Výstup: /run/vqsting/keyboards.json (posledná stlačená klávesa per klávesnica).
"""

import json
import os
import pwd
import re
import select
import signal
import socket
import struct
import sys
import time

EV_KEY = 1
RUN_DIR = "/run/vqsting"
STATE = os.path.join(RUN_DIR, "keyboards.json")
PID = os.path.join(RUN_DIR, "listener.pid")
OPEN_SOCK = os.path.join(RUN_DIR, "open.sock")
EVENT = struct.Struct("llHHi")   # x86_64 Linux: 24 B
SCAN_EVERY = 5                   # s, kedy skúsiť novo pripojené klávesnice

KEY_NAMES = {1: "Esc", 14: "Backspace", 15: "Tab", 28: "Enter", 29: "Left Ctrl",
             42: "Left Shift", 54: "Right Shift", 56: "Left Alt", 57: "Space",
             58: "CapsLock", 69: "NumLock", 97: "Right Ctrl", 100: "Right Alt"}
KEY_NAMES.update({16 + i: c for i, c in enumerate("QWERTYUIOP")})
KEY_NAMES.update({30 + i: c for i, c in enumerate("ASDFGHJKL")})
KEY_NAMES.update({44 + i: c for i, c in enumerate("ZXCVBNM")})
KEY_NAMES.update({2 + i: str((i + 1) % 10) for i in range(10)})

devices = {}   # node -> {"node", "name", "uniq", "phys", "key", "at"}


# ---------- root opener: iba otvára nody a posiela fd ----------

def _opener_loop(server):
    def child_gone(signum, frame):
        os.waitpid(-1, os.WNOHANG)
        raise SystemExit(0)

    signal.signal(signal.SIGCHLD, child_gone)
    while True:
        conn, _ = server.accept()
        try:
            node = conn.recv(64).decode(errors="replace")
            fd = -1
            if re.fullmatch(r"event\d+", node):
                try:
                    fd = os.open(f"/dev/input/{node}", os.O_RDONLY | os.O_NONBLOCK)
                except OSError:
                    fd = -1
            if fd >= 0:
                socket.send_fds(conn, [b"ok"], [fd])
                os.close(fd)
            else:
                conn.send(b"no")
        except OSError:
            pass
        finally:
            conn.close()


# ---------- unprivileged listener ----------

def _attr(node, name):
    try:
        with open(f"/sys/class/input/{node}/device/{name}") as f:
            return f.read().strip()
    except OSError:
        return ""


def _is_keyboard(node):
    # myš má tiež KEY_A/KEY_1 bity (Logitech receiver), ale má REL_X/REL_Y
    rel = _attr(node, "capabilities/rel")
    if rel and int(rel.split()[-1], 16) & 0b11:
        return False
    caps = _attr(node, "capabilities/key")
    if not caps:
        return False
    bits = int(caps.split()[-1], 16)   # najnižší word = bity 0-63
    return bool(bits >> 30 & 1) and bool(bits >> 2 & 1)


def _keyboards():
    try:
        nodes = os.listdir("/sys/class/input")
    except OSError:
        return []
    return sorted(n for n in nodes if n.startswith("event") and _is_keyboard(n))


def _open(node):
    try:
        return os.open(f"/dev/input/{node}", os.O_RDONLY | os.O_NONBLOCK)
    except PermissionError:
        pass
    # nový node po reconnecte — otvorí ho root opener a pošle fd
    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client.connect(OPEN_SOCK)
    client.send(node.encode())
    _, fds, _, _ = socket.recv_fds(client, 8, 1)
    client.close()
    if not fds:
        raise OSError(f"cannot open /dev/input/{node}")
    return fds[0]


def _add(node, fds):
    if node in devices:
        return
    fds[_open(node)] = node
    devices[node] = {"node": node, "name": _attr(node, "name"),
                     "uniq": _attr(node, "uniq"), "phys": _attr(node, "phys"),
                     "key": None, "at": None}


def _write():
    with open(STATE + ".tmp", "w") as f:
        json.dump({"ts": time.time(), "devices": list(devices.values())}, f)
    os.replace(STATE + ".tmp", STATE)


def _drop_privileges(uid):
    """Become the invoking user and drop root's supplementary groups."""
    gid = pwd.getpwuid(uid).pw_gid
    os.chown(RUN_DIR, uid, gid)
    os.chown(OPEN_SOCK, uid, gid)
    os.setgroups([])
    os.setgid(gid)
    os.setuid(uid)


def _remove_if_ours(path):
    """Delete a runtime file only when it belongs to this process."""
    try:
        with open(path) as f:
            if int(f.read()) == os.getpid():
                os.unlink(path)
    except (OSError, ValueError):
        pass


def _cleanup():
    _remove_if_ours(PID)


def _on_signal(signum, frame):
    raise SystemExit(0)


def _already_running():
    """Return the pid of a live listener, or None."""
    try:
        with open(PID) as f:
            pid = int(f.read())
    except (OSError, ValueError):
        return None
    if pid == os.getpid():
        return None
    try:
        os.kill(pid, 0)
        with open(f"/proc/{pid}/cmdline", "rb") as f:
            cmdline = f.read()
    except OSError:
        return None
    return pid if b"keyboard_listener" in cmdline else None


def main():
    running = _already_running()
    if running:
        print(f"listener už beží (pid {running})", file=sys.stderr)
        raise SystemExit(1)

    os.makedirs(RUN_DIR, mode=0o755, exist_ok=True)

    if os.geteuid() == 0:
        try:
            os.unlink(OPEN_SOCK)
        except OSError:
            pass
        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        server.bind(OPEN_SOCK)
        server.listen(4)
        os.chmod(OPEN_SOCK, 0o660)   # priečinok je aj tak len pre usera
        if os.fork() == 0:
            _drop_privileges(int(os.environ.get("PKEXEC_UID", os.getuid())))
        else:
            try:
                _opener_loop(server)  # rodič: len otvára nody
            finally:
                try:
                    os.unlink(OPEN_SOCK)
                except OSError:
                    pass
            return

    signal.signal(signal.SIGTERM, _on_signal)
    signal.signal(signal.SIGINT, _on_signal)
    try:
        _listen()
    finally:
        _cleanup()


def _listen():
    fds = {}
    for node in _keyboards():
        try:
            _add(node, fds)
        except OSError as e:
            print(f"{node}: {e}", file=sys.stderr)

    with open(PID, "w") as f:
        f.write(str(os.getpid()))
    _write()
    print(f"listener: {len(fds)} keyboards {sorted(fds.values())}", flush=True)

    next_scan = time.time() + SCAN_EVERY
    while True:
        try:
            ready, _, _ = select.select(list(fds), [], [], 1)
        except InterruptedError:
            continue

        for fd in ready:
            try:
                data = os.read(fd, EVENT.size)
            except BlockingIOError:
                continue
            except OSError:
                data = b""

            if len(data) < EVENT.size:      # zariadenie zmizlo
                os.close(fd)
                devices.pop(fds.pop(fd), None)
                _write()
                continue

            _, _, typ, code, value = EVENT.unpack(data)
            if typ == EV_KEY and value == 1:
                node = devices[fds[fd]]
                node["key"] = KEY_NAMES.get(code, f"code {code}")
                node["at"] = time.time()
                _write()

        if time.time() >= next_scan:
            next_scan = time.time() + SCAN_EVERY
            added = False
            for node in _keyboards():
                if node not in devices:
                    try:
                        _add(node, fds)
                        added = True
                    except OSError:
                        pass
            if added:
                _write()


if __name__ == "__main__":
    main()
