"""Listener klávesníc (Windows). Beží oddelene od Flasku a jediný číta Raw Input.

Spustenie:  python tools/windows_keyboard_listener.py
Ukončenie:  Ctrl+C alebo dvojklik na stop.bat

Windows nepotrebuje žiadne práva navyše: Raw Input je bežné používateľské API.
Listener nič neinštaluje, nemení systémové nastavenia a píše len dva súbory
vedľa seba (cesty rieši state_paths.py):

- keyboards.json — posledná stlačená klávesa per klávesnica + krúžkový buffer
  eventov (tvar je zhodný s Linux listenerom, kontrakt v
  docs/for-ai/CONTEXT-group-mode.md sekcia 5),
- listener.pid — pid procesu, aby ho stop.bat vedel vypnúť.

Bez `--selftest` funguje len na Windows. `--selftest` prejde všade (Linux aj
Windows), lebo netestuje Windows API, len čisté funkcie.
"""

import atexit
import collections
import json
import os
import shutil
import signal
import sys
import tempfile
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from state_paths import pid_file, run_dir, state_file

WM_INPUT = 0x00FF
RID_INPUT, RIDI_DEVICENAME = 0x10000003, 0x20000007
RIM_TYPEKEYBOARD, RIDEV_INPUTSINK = 1, 0x00000100
RI_KEY_BREAK = 0x0001
HWND_MESSAGE, PM_REMOVE = -3, 0x0001
UINT_ERROR = 0xFFFFFFFF
POLL_SECONDS = 0.02

PLATFORM = "windows"
EVENTS_KEPT = 64          # krúžkový buffer posledných eventov (kontrakt)

# VKey -> názov klávesy. Číslice musia byť presne "1".."5" (hlasovanie).
KEYS = {0x08: "Backspace", 0x09: "Tab", 0x0D: "Enter", 0x1B: "Esc",
        0x20: "Space", 0x14: "CapsLock", 0x10: "Shift", 0x90: "NumLock",
        0xA0: "Left Shift", 0xA1: "Right Shift", 0xA2: "Left Ctrl",
        0xA3: "Right Ctrl", 0xA4: "Left Alt", 0xA5: "Right Alt",
        0x11: "Ctrl", 0x12: "Alt"}
KEYS.update({0x30 + i: str(i) for i in range(10)})    # horný rad číslic
KEYS.update({0x60 + i: str(i) for i in range(10)})    # numerický blok
KEYS.update({0x41 + i: chr(ord("A") + i) for i in range(26)})


def key_name(vkey):
    """Normalizovaný názov klávesy z Windows VKey."""
    return KEYS.get(vkey, f"VKey 0x{vkey:02X}")


def instance_id(device_name):
    """Vráti časť RIDI_DEVICENAME medzi druhým '#' a '#{' (7&2f&0&0000)."""
    parts = device_name.split("#", 2)
    if len(parts) < 3:
        return ""
    return parts[2].split("#{", 1)[0]


def device_id(device_name):
    """Stabilné ID zariadenia; prežíva reconnect, lebo je z inštančnej cesty."""
    return "win:" + (instance_id(device_name) or device_name)


def write_state(path, payload):
    """Celý súbor naraz: Flask nikdy nečíta rozrobený JSON."""
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f)
    os.replace(tmp, path)


class ListenerState:
    """Globálny seq, eventy a posledná klávesa per zariadenie."""

    def __init__(self):
        self.seq = 0
        self.devices = {}                                    # id -> dict
        self.events = collections.deque(maxlen=EVENTS_KEPT)  # {"seq","at","device_id","key"}

    def press(self, keyboard_id, name, node, key, at=None):
        """Zapíše jedno stlačenie (key-down) a vráti event."""
        at = time.time() if at is None else at
        self.seq += 1
        event = {"seq": self.seq, "at": at, "device_id": keyboard_id, "key": key}
        self.events.append(event)
        device = self.devices.setdefault(
            keyboard_id, {"id": keyboard_id, "name": name, "node": node,
                          "seq": None, "key": None, "at": None})
        device.update(name=name, node=node, seq=self.seq, key=key, at=at)
        return event

    def payload(self, now=None):
        """Stav na zapísanie do keyboards.json (kontrakt, sekcia 5)."""
        return {"ts": time.time() if now is None else now,
                "platform": PLATFORM,
                "seq": self.seq,
                "devices": [dict(d) for d in self.devices.values()],
                "events": list(self.events)}


# ---------- Windows Raw Input ----------

def run():
    """Skryté message-only okno + slučka správ; píše stav pri každom stlačení."""
    import ctypes
    from ctypes import wintypes

    WNDPROC = ctypes.WINFUNCTYPE(wintypes.LPARAM, wintypes.HWND, wintypes.UINT,
                                 wintypes.WPARAM, wintypes.LPARAM)

    class RAWINPUTDEVICE(ctypes.Structure):
        _fields_ = [("usUsagePage", wintypes.USHORT), ("usUsage", wintypes.USHORT),
                    ("dwFlags", wintypes.DWORD), ("hwndTarget", wintypes.HWND)]

    class RAWINPUTHEADER(ctypes.Structure):
        _fields_ = [("dwType", wintypes.DWORD), ("dwSize", wintypes.DWORD),
                    ("hDevice", wintypes.HANDLE), ("wParam", wintypes.WPARAM)]

    class RAWKEYBOARD(ctypes.Structure):
        _fields_ = [("MakeCode", wintypes.USHORT), ("Flags", wintypes.USHORT),
                    ("Reserved", wintypes.USHORT), ("VKey", wintypes.USHORT),
                    ("Message", wintypes.UINT), ("ExtraInformation", wintypes.ULONG)]

    class RAWINPUT(ctypes.Structure):
        _fields_ = [("header", RAWINPUTHEADER), ("keyboard", RAWKEYBOARD)]

    class WNDCLASSEXW(ctypes.Structure):
        _fields_ = [("cbSize", wintypes.UINT), ("style", wintypes.UINT),
                    ("lpfnWndProc", WNDPROC), ("cbClsExtra", ctypes.c_int),
                    ("cbWndExtra", ctypes.c_int), ("hInstance", wintypes.HINSTANCE),
                    ("hIcon", wintypes.HANDLE), ("hCursor", wintypes.HANDLE),
                    ("hbrBackground", wintypes.HANDLE), ("lpszMenuName", wintypes.LPCWSTR),
                    ("lpszClassName", wintypes.LPCWSTR), ("hIconSm", wintypes.HANDLE)]

    u, k = ctypes.windll.user32, ctypes.windll.kernel32
    u.RegisterClassExW.argtypes = [ctypes.POINTER(WNDCLASSEXW)]
    u.RegisterClassExW.restype = wintypes.WORD
    u.CreateWindowExW.argtypes = [wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR,
                                  wintypes.DWORD, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                  ctypes.c_int, wintypes.HWND, wintypes.HMENU,
                                  wintypes.HINSTANCE, wintypes.LPVOID]
    u.CreateWindowExW.restype = wintypes.HWND
    u.DefWindowProcW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    u.DefWindowProcW.restype = wintypes.LPARAM
    u.RegisterRawInputDevices.argtypes = [ctypes.POINTER(RAWINPUTDEVICE), wintypes.UINT,
                                          wintypes.UINT]
    u.GetRawInputData.argtypes = [wintypes.HANDLE, wintypes.UINT, wintypes.LPVOID,
                                  ctypes.POINTER(wintypes.UINT), wintypes.UINT]
    u.GetRawInputData.restype = wintypes.UINT
    u.GetRawInputDeviceInfoW.argtypes = [wintypes.HANDLE, wintypes.UINT, wintypes.LPVOID,
                                         ctypes.POINTER(wintypes.UINT)]
    u.GetRawInputDeviceInfoW.restype = wintypes.UINT
    u.PeekMessageW.argtypes = [ctypes.POINTER(wintypes.MSG), wintypes.HWND,
                               wintypes.UINT, wintypes.UINT, wintypes.UINT]
    u.DispatchMessageW.argtypes = [ctypes.POINTER(wintypes.MSG)]
    u.DispatchMessageW.restype = wintypes.LPARAM
    u.DestroyWindow.argtypes = [wintypes.HWND]
    k.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
    k.GetModuleHandleW.restype = wintypes.HMODULE

    path = state_file()
    state = ListenerState()

    def raw_device_name(hdevice):
        size = wintypes.UINT(0)
        u.GetRawInputDeviceInfoW(hdevice, RIDI_DEVICENAME, None, ctypes.byref(size))
        if not size.value:
            return ""
        buf = ctypes.create_unicode_buffer(size.value)
        if u.GetRawInputDeviceInfoW(hdevice, RIDI_DEVICENAME,
                                    ctypes.cast(buf, wintypes.LPVOID),
                                    ctypes.byref(size)) == UINT_ERROR:
            return ""
        return buf.value

    def on_raw_input(hrawinput):
        size = wintypes.UINT(0)
        header_size = ctypes.sizeof(RAWINPUTHEADER)
        if u.GetRawInputData(hrawinput, RID_INPUT, None, ctypes.byref(size),
                             header_size) == UINT_ERROR or size.value < ctypes.sizeof(RAWINPUT):
            return
        buf = ctypes.create_string_buffer(size.value)
        if u.GetRawInputData(hrawinput, RID_INPUT, ctypes.cast(buf, wintypes.LPVOID),
                             ctypes.byref(size), header_size) != size.value:
            return
        raw = ctypes.cast(buf, ctypes.POINTER(RAWINPUT)).contents
        if raw.header.dwType != RIM_TYPEKEYBOARD:
            return
        key = raw.keyboard
        if key.Flags & RI_KEY_BREAK or key.VKey == 0xFF:   # len key-down
            return
        if not raw.header.hDevice:
            return
        name = raw_device_name(raw.header.hDevice)
        instance = instance_id(name) or name
        # node = inštančná cesta; na Linuxe je v tomto poli "eventN"
        event = state.press(device_id(name), name, instance, key_name(key.VKey))
        write_state(path, state.payload())
        print(f"[{event['device_id']}] {event['key']}  ({name})", flush=True)

    def wndproc(hwnd, msg, wparam, lparam):
        if msg != WM_INPUT:
            return u.DefWindowProcW(hwnd, msg, wparam, lparam)
        try:
            on_raw_input(lparam)
        except Exception as exc:   # slučka správ musí bežať ďalej
            print(f"Chyba pri WM_INPUT: {exc}", file=sys.stderr, flush=True)
        return 0

    hinst = k.GetModuleHandleW(None)
    wc = WNDCLASSEXW()
    wc.cbSize = ctypes.sizeof(WNDCLASSEXW)
    wc.lpfnWndProc = WNDPROC(wndproc)
    wc.hInstance = hinst
    wc.lpszClassName = "VQSTingKeyboardListener"
    if not u.RegisterClassExW(ctypes.byref(wc)):
        raise ctypes.WinError()
    hwnd = u.CreateWindowExW(0, wc.lpszClassName, "listener", 0, 0, 0, 0, 0,
                             ctypes.c_void_p(HWND_MESSAGE), None, hinst, None)
    if not hwnd:
        raise ctypes.WinError()
    try:
        # INPUTSINK = klávesy zbierame aj vtedy, keď nemáme fokus
        registration = RAWINPUTDEVICE(1, 6, RIDEV_INPUTSINK, hwnd)
        if not u.RegisterRawInputDevices(ctypes.byref(registration), 1,
                                        ctypes.sizeof(RAWINPUTDEVICE)):
            raise ctypes.WinError()

        write_state(path, state.payload())
        print(f"listener: Windows Raw Input, stav {path}", flush=True)

        stop = {"requested": False}

        def request_stop(signum, frame):
            stop["requested"] = True

        previous_sigint = signal.signal(signal.SIGINT, request_stop)
        msg = wintypes.MSG()
        try:
            while not stop["requested"]:
                if u.PeekMessageW(ctypes.byref(msg), None, 0, 0, PM_REMOVE):
                    u.DispatchMessageW(ctypes.byref(msg))
                else:
                    time.sleep(POLL_SECONDS)
        finally:
            signal.signal(signal.SIGINT, previous_sigint)
    finally:
        u.DestroyWindow(hwnd)


# ---------- pid súbor ----------

def remove_pid_file(path):
    try:
        os.unlink(path)
    except OSError:
        pass


# ---------- selftest (funguje aj na Linuxe) ----------

def selftest():
    names = [r"\\?\HID#VID_046D&PID_C31C#7&2f&0&0000#{884b96c3-56ef-11d1-bc8c-00a0c91405dd}",
             r"\\?\ACPI#PNP0303#4&1a&0#{884b96c3-56ef-11d1-bc8c-00a0c91405dd}",
             "no-hash"]
    for name, expected_instance in zip(names, ["7&2f&0&0000", "4&1a&0", ""]):
        assert instance_id(name) == expected_instance, name
    assert device_id(names[0]) == "win:7&2f&0&0000"
    assert device_id(names[2]) == "win:no-hash"        # bez inštancie aspoň meno
    assert device_id(names[0]) == device_id(names[0] + "#{other}")   # stabilné
    print("[OK] instančná cesta a stabilné id")

    for vkey, expected in [(0x31, "1"), (0x32, "2"), (0x33, "3"), (0x34, "4"),
                           (0x35, "5"), (0x30, "0"), (0x61, "1"), (0x69, "9"),
                           (0x0D, "Enter"), (0x08, "Backspace"), (0xA0, "Left Shift"),
                           (0x41, "A"), (0xE8, "VKey 0xE8")]:
        assert key_name(vkey) == expected, (hex(vkey), key_name(vkey))
    digits = {key_name(0x31 + i) for i in range(5)}
    assert digits == {"1", "2", "3", "4", "5"}, digits
    print("[OK] mapovanie VKey na názov klávesy")

    state = ListenerState()
    state.press("win:7&2f&0&0000", r"\\?\HID#kbd1#7&2f&0&0000#{x}", "7&2f&0&0000", "1", at=100.0)
    state.press("win:7&2f&0&0000", r"\\?\HID#kbd1#7&2f&0&0000#{x}", "7&2f&0&0000", "Enter", at=100.5)
    state.press("win:5&1a&0&0000", r"\\?\HID#kbd2#5&1a&0&0000#{x}", "5&1a&0&0000", "3", at=101.0)
    payload = state.payload(now=102.0)
    assert payload["platform"] == "windows" and payload["ts"] == 102.0
    assert payload["seq"] == 3
    assert [e["key"] for e in payload["events"]] == ["1", "Enter", "3"]
    assert [e["seq"] for e in payload["events"]] == [1, 2, 3]
    assert payload["events"][2]["device_id"] == "win:5&1a&0&0000"
    last = {d["id"]: d for d in payload["devices"]}
    assert last["win:7&2f&0&0000"]["seq"] == 2
    assert last["win:7&2f&0&0000"]["key"] == "Enter"
    assert last["win:7&2f&0&0000"]["at"] == 100.5
    assert last["win:5&1a&0&0000"]["key"] == "3"
    print("[OK] stavový JSON zo syntetických eventov")

    for _ in range(EVENTS_KEPT + 6):
        state.press("win:7&2f&0&0000", "kbd1", "7&2f&0&0000", "2", at=200.0)
    events = state.payload()["events"]
    assert len(events) == EVENTS_KEPT, len(events)
    assert events[0]["seq"] == state.seq - EVENTS_KEPT + 1
    assert events[-1]["seq"] == state.seq
    print(f"[OK] krúžkový buffer drží posledných {EVENTS_KEPT} eventov")

    path = os.path.join(tempfile.mkdtemp(prefix="vqsting-selftest-"), "keyboards.json")
    try:
        write_state(path, payload)
        assert not os.path.exists(path + ".tmp")
        with open(path, encoding="utf-8") as f:
            assert json.load(f) == payload
    finally:
        shutil.rmtree(os.path.dirname(path), ignore_errors=True)
    print("[OK] atomický zápis stavu")

    print("selftest OK")
    return 0


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--selftest" in argv:
        return selftest()
    if sys.platform != "win32":
        print("Listener klávesníc funguje len na Windows (Raw Input API).")
        print(f"Zistený systém: {sys.platform}. Na tomto systéme nič nemení.")
        return 1

    os.makedirs(run_dir(), exist_ok=True)
    pid = pid_file()
    with open(pid, "w") as f:
        f.write(str(os.getpid()))
    atexit.register(remove_pid_file, pid)
    try:
        run()
    except OSError as exc:
        print(f"Chyba Windows API: {exc}", file=sys.stderr)
        return 1
    finally:
        remove_pid_file(pid)
    return 0


if __name__ == "__main__":
    sys.exit(main())
