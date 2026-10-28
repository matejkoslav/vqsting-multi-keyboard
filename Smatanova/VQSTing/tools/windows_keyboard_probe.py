"""Windows Raw Input probe: which physical keyboard sent a key press?

Windows-only, stdlib + ctypes. It installs nothing, writes no files, needs no
admin rights and changes no system settings. Run from the repo root:

    python Smatanova/VQSTing/tools/windows_keyboard_probe.py

Stop with Ctrl+C. For the pure helper self-test: --selftest (works anywhere).
"""

import ctypes
import signal
import sys
import time

WM_INPUT, WM_KEYDOWN, WM_SYSKEYDOWN = 0x00FF, 0x0100, 0x0104
RID_INPUT, RIDI_DEVICENAME = 0x10000003, 0x20000007
RIM_TYPEKEYBOARD, RIDEV_INPUTSINK = 1, 0x00000100
HWND_MESSAGE, PM_REMOVE = -3, 0x0001
UINT_ERROR, WARN_AFTER_PRESSES = 0xFFFFFFFF, 5


def instance_id(device_name):
    """Return the segment between the second '#' and '#{' in a device name."""
    parts = device_name.split("#", 2)
    if len(parts) < 3:
        return ""
    return parts[2].split("#{", 1)[0]


def selftest():
    samples = {
        r"\\?\HID#VID_046D&PID_C31C#7&2f&0&0000#{x}": "7&2f&0&0000",
        r"\\?\ACPI#PNP0303#4&1a&0#{x}": "4&1a&0",
        "no-hash": "",
    }
    for name, expected in samples.items():
        assert instance_id(name) == expected, name
    print("selftest OK")


def run_probe():
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

    devices = {}
    state = {"total": 0, "warned": False}

    def device_name(hdevice):
        size = wintypes.UINT(0)
        u.GetRawInputDeviceInfoW(hdevice, RIDI_DEVICENAME, None, ctypes.byref(size))
        if not size.value:
            return "<neznáme zariadenie>"
        buf = ctypes.create_unicode_buffer(size.value)
        if u.GetRawInputDeviceInfoW(hdevice, RIDI_DEVICENAME,
                                    ctypes.cast(buf, wintypes.LPVOID),
                                    ctypes.byref(size)) == UINT_ERROR:
            return "<neznáme zariadenie>"
        return buf.value

    def maybe_warn():
        if state["warned"] or state["total"] < WARN_AFTER_PRESSES or len(devices) != 1:
            return
        state["warned"] = True
        print(f"\nVAROVANIE: po {WARN_AFTER_PRESSES} stlačeniach vidím len 1 zariadenie.")
        print("  Možné príčiny: PS/2, USB hub, Bluetooth, alebo ovládač zlúčil klávesnice.")
        print("  Skús klávesnice zapojiť priamo do USB, vypni Bluetooth a spusti probe znova.\n")

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
        if key.Message not in (WM_KEYDOWN, WM_SYSKEYDOWN) or key.VKey == 0xFF:
            return
        name = device_name(raw.header.hDevice)
        entry = devices.setdefault(name, {"number": len(devices) + 1, "count": 0})
        entry["count"] += 1
        state["total"] += 1
        print(f"[{entry['number']}] id={instance_id(name) or '-'} "
              f"VKey=0x{key.VKey:02X}  {name}")
        maybe_warn()

    def wndproc(hwnd, msg, wparam, lparam):
        if msg != WM_INPUT:
            return u.DefWindowProcW(hwnd, msg, wparam, lparam)
        try:
            on_raw_input(lparam)
        except Exception as exc:  # keep the message loop alive
            print(f"Chyba pri WM_INPUT: {exc}", file=sys.stderr)
        return 0

    def print_summary():
        print("\nSúhrn:")
        if not devices:
            print("  žiadne stlačenie — stlač klávesu a potom Ctrl+C.")
            return
        for name, entry in sorted(devices.items(), key=lambda item: item[1]["number"]):
            print(f"  #{entry['number']}: {entry['count']} stlačení, "
                  f"id={instance_id(name) or '-'}")
            print(f"      {name}")

    hinst = k.GetModuleHandleW(None)
    wc = WNDCLASSEXW()
    wc.cbSize = ctypes.sizeof(WNDCLASSEXW)
    wc.lpfnWndProc = WNDPROC(wndproc)
    wc.hInstance = hinst
    wc.lpszClassName = "VQSTingRawInputProbe"
    if not u.RegisterClassExW(ctypes.byref(wc)):
        raise ctypes.WinError()
    hwnd = u.CreateWindowExW(0, wc.lpszClassName, "probe", 0, 0, 0, 0, 0,
                             ctypes.c_void_p(HWND_MESSAGE), None, hinst, None)
    if not hwnd:
        raise ctypes.WinError()
    registration = RAWINPUTDEVICE(1, 6, RIDEV_INPUTSINK, hwnd)
    if not u.RegisterRawInputDevices(ctypes.byref(registration), 1,
                                     ctypes.sizeof(RAWINPUTDEVICE)):
        raise ctypes.WinError()

    print("Windows Raw Input probe — rozlíšenie klávesníc")
    print("Stlač postupne klávesu na každej klávesnici. Ukončenie: Ctrl+C.\n")

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
                time.sleep(0.02)
    finally:
        signal.signal(signal.SIGINT, previous_sigint)
        print_summary()
        u.DestroyWindow(hwnd)
    return 0


def main():
    if "--selftest" in sys.argv[1:]:
        selftest()
        return 0
    if sys.platform != "win32":
        print("Tento nástroj funguje len na Windows (Raw Input API).")
        print(f"Zistený systém: {sys.platform}. Na tomto systéme nič nemení.")
        return 1
    try:
        return run_probe()
    except OSError as exc:
        print(f"Chyba Windows API: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
