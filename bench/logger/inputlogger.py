#!/usr/bin/env python3
"""Logger di input ESTERNO, indipendente da tutti gli strumenti in prova (solo Windows).

Un processo separato installa WH_MOUSE_LL e WH_KEYBOARD_LL (SetWindowsHookEx) e scrive
un CSV con timestamp QueryPerformanceCounter (ms dall'avvio), coordinate in pixel fisici
(processo Per-Monitor-V2 DPI aware) e il flag LLMHF_INJECTED. Non usa nulla dei progetti testati.

  python inputlogger.py --out run_01.csv [--duration 30] [--stop-key F12]

Esegui il logger con lo STESSO livello di integrita' dell'obiettivo piu' alto che vuoi osservare
(per le finestre elevate: come amministratore), altrimenti UIPI puo' nascondergli gli eventi.
Nessun dato di rete, nessun hook sul contenuto: solo tipo, tempo, x, y, rotella, tasto (codice).
"""
import argparse, csv, ctypes, sys, time
from ctypes import wintypes as W

if sys.platform != "win32":
    sys.exit("inputlogger.py funziona solo su Windows")

u = ctypes.WinDLL("user32", use_last_error=True)
k = ctypes.WinDLL("kernel32", use_last_error=True)
LRESULT = ctypes.c_ssize_t
HOOKPROC = ctypes.WINFUNCTYPE(LRESULT, ctypes.c_int, W.WPARAM, W.LPARAM)
u.SetWindowsHookExW.restype = W.HHOOK
u.SetWindowsHookExW.argtypes = [ctypes.c_int, HOOKPROC, W.HINSTANCE, W.DWORD]
u.CallNextHookEx.restype = LRESULT
u.CallNextHookEx.argtypes = [W.HHOOK, ctypes.c_int, W.WPARAM, W.LPARAM]
u.UnhookWindowsHookEx.argtypes = [W.HHOOK]
u.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))   # Per-Monitor-V2

WH_KEYBOARD_LL, WH_MOUSE_LL = 13, 14
NAMES = {0x200: "move", 0x201: "ldown", 0x202: "lup", 0x204: "rdown", 0x205: "rup",
         0x207: "mdown", 0x208: "mup", 0x20A: "wheel", 0x20E: "hwheel",
         0x100: "kdown", 0x101: "kup", 0x104: "kdown", 0x105: "kup"}


class MSLL(ctypes.Structure):
    _fields_ = [("x", W.LONG), ("y", W.LONG), ("data", W.DWORD), ("flags", W.DWORD),
                ("time", W.DWORD), ("extra", ctypes.c_size_t)]


class KBLL(ctypes.Structure):
    _fields_ = [("vk", W.DWORD), ("scan", W.DWORD), ("flags", W.DWORD), ("time", W.DWORD),
                ("extra", ctypes.c_size_t)]


freq = ctypes.c_int64(); k.QueryPerformanceFrequency(ctypes.byref(freq))
def qpc_ms():
    c = ctypes.c_int64(); k.QueryPerformanceCounter(ctypes.byref(c))
    return c.value * 1000.0 / freq.value


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--duration", type=float, default=0, help="secondi; 0 = fino al tasto di stop")
    ap.add_argument("--stop-key", default="F12", help="tasto che chiude il logger (F1..F12)")
    ap.add_argument("--no-moves", action="store_true", help="non scrive i movimenti (file piu' piccoli)")
    a = ap.parse_args()
    stop_vk = 0x70 + int(a.stop_key[1:]) - 1
    t0 = qpc_ms()
    f = open(a.out, "w", newline="", encoding="utf-8")
    w = csv.writer(f); w.writerow(["t_ms", "event", "x", "y", "data", "injected"])
    state = {"stop": False}

    def mouse_cb(n, wp, lp):
        if n == 0:
            t = qpc_ms() - t0                      # il prima possibile
            m = ctypes.cast(lp, ctypes.POINTER(MSLL)).contents
            ev = NAMES.get(wp, hex(wp))
            if not (a.no_moves and ev == "move"):
                data = ctypes.c_short(m.data >> 16).value if ev in ("wheel", "hwheel") else m.data >> 16
                w.writerow([f"{t:.3f}", ev, m.x, m.y, data, 1 if m.flags & 1 else 0])
        return u.CallNextHookEx(None, n, wp, lp)

    def key_cb(n, wp, lp):
        if n == 0:
            t = qpc_ms() - t0
            kb = ctypes.cast(lp, ctypes.POINTER(KBLL)).contents
            w.writerow([f"{t:.3f}", NAMES.get(wp, hex(wp)), 0, 0, kb.vk, 1 if kb.flags & 0x10 else 0])
            if wp in (0x100, 0x104) and kb.vk == stop_vk:
                state["stop"] = True
                u.PostQuitMessage(0)
        return u.CallNextHookEx(None, n, wp, lp)

    mp, kp = HOOKPROC(mouse_cb), HOOKPROC(key_cb)       # riferimenti vivi: se no il GC li distrugge
    hm = u.SetWindowsHookExW(WH_MOUSE_LL, mp, None, 0)
    hk = u.SetWindowsHookExW(WH_KEYBOARD_LL, kp, None, 0)
    if not hm or not hk:
        sys.exit(f"SetWindowsHookEx fallita: {ctypes.get_last_error()}")
    print(f"logger attivo -> {a.out} (stop: {a.stop_key}" + (f" o {a.duration}s)" if a.duration else ")"), flush=True)
    msg = W.MSG()
    end = time.time() + a.duration if a.duration else None
    while not state["stop"]:
        r = u.PeekMessageW(ctypes.byref(msg), None, 0, 0, 1)
        if r:
            if msg.message == 0x12: break
            u.TranslateMessage(ctypes.byref(msg)); u.DispatchMessageW(ctypes.byref(msg))
        else:
            time.sleep(0.001)
        if end and time.time() >= end: break
    u.UnhookWindowsHookEx(hm); u.UnhookWindowsHookEx(hk); f.close()


if __name__ == "__main__":
    main()
