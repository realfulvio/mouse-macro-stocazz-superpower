#!/usr/bin/env python3
"""Profilo del pannello a riposo (Windows): da dove viene la CPU dell'animazione.
  python bench/ci/profile_idle.py --mode cpu     # CPU totale del processo (tutti i thread) in una finestra, senza profiler
  python bench/ci/profile_idle.py --mode prof    # cProfile del thread dell'interfaccia: funzioni per tempo proprio
Avvia windows_main.Panel dal sorgente nella sessione corrente, aspetta l'assestamento, misura, poi esce con WM_QUIT.\nIn modo prof il profilo comprende anche l'assestamento iniziale (cProfile ingrandisce il costo del codice Python: serve per la ripartizione, non per i valori assoluti)."""
import argparse, ctypes, cProfile, io, json, pstats, sys, threading, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
ap = argparse.ArgumentParser(); ap.add_argument("--mode", choices=("cpu", "prof", "verify"), required=True)
ap.add_argument("--warm", type=float, default=12); ap.add_argument("--window", type=float, default=30); ap.add_argument("--top", type=int, default=28)
a = ap.parse_args()
import windows_main as wm  # noqa: E402
import windows_visual as wv  # noqa: E402

k = ctypes.windll.kernel32; u = ctypes.windll.user32
tid = k.GetCurrentThreadId(); result = {}


k.GetCurrentProcess.restype = ctypes.c_void_p
k.GetProcessTimes.argtypes = [ctypes.c_void_p] + [ctypes.POINTER(ctypes.c_ulonglong)] * 4


def cpu_seconds():
    c, e, kt, ut = (ctypes.c_ulonglong() for _ in range(4))
    if not k.GetProcessTimes(k.GetCurrentProcess(), ctypes.byref(c), ctypes.byref(e), ctypes.byref(kt), ctypes.byref(ut)): raise OSError("GetProcessTimes")
    return (kt.value + ut.value) / 1e7


STATS = {}   # strumentazione leggera (perf_counter): chiave -> [chiamate, secondi]


def timed(key_of):
    def deco(fn):
        def wrapper(*args, **kw):
            t = time.perf_counter()
            try: return fn(*args, **kw)
            finally:
                e = STATS.setdefault(key_of(args), [0, 0.0]); e[0] += 1; e[1] += time.perf_counter() - t
        return wrapper
    return deco


if a.mode == "cpu":   # conteggi e tempi per messaggio e per tela (costo del timer: ~1 microsecondo a chiamata)
    wm.Panel.wndproc = timed(lambda args: "msg 0x%X%s" % (args[2], " id%d" % args[3] if args[2] == 0x113 else ""))(wm.Panel.wndproc)
    wm.Panel.render = timed(lambda args: "render")(wm.Panel.render)
    wm.Panel.paint = timed(lambda args: "paint")(wm.Panel.paint)
    wm.Panel.draw_control = timed(lambda args: "draw_control")(wm.Panel.draw_control)
    _init, _close = wm.Canvas.__init__, wm.Canvas.close
    def c_init(self, *x, **kw):
        _init(self, *x, **kw); self._t = time.perf_counter()
    def c_close(self):
        e = STATS.setdefault("tela %s" % ("parziale" if self.clip else "intera"), [0, 0.0]); e[0] += 1; e[1] += time.perf_counter() - self._t
        _close(self)
    wm.Canvas.__init__, wm.Canvas.close = c_init, c_close


def controller(panel, prof):
    time.sleep(a.warm)
    STATS.clear(); c0, t0 = cpu_seconds(), time.perf_counter()
    time.sleep(a.window)
    c1, t1 = cpu_seconds(), time.perf_counter()
    snap = {key: [v[0], round(v[1] * 1000, 1)] for key, v in sorted(STATS.items())}
    result.update(stats_calls_ms=snap, cpu_pct_of_core=round(100 * (c1 - c0) / (t1 - t0), 2), window_s=round(t1 - t0, 1),
                  shown=panel.shown, animating=panel.animating, skin=wm.CURRENT["skin"], dpi=panel.dpi)
    u.PostThreadMessageW(tid, 0x12, 0, 0)   # WM_QUIT: esce da GetMessageW


def verify():
    """Il fotogramma della mascotte ridisegnato dal percorso rapido (Layer) deve essere IDENTICO, pixel per pixel,
    a quello del percorso completo, per ogni fotogramma dello sprite sheet. Indice del fotogramma fissato a mano."""
    import struct
    u.GetDC.restype = ctypes.c_void_p; u.GetDC.argtypes = [ctypes.c_void_p]; u.ReleaseDC.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    g = ctypes.windll.gdi32
    g.CreateCompatibleDC.restype = ctypes.c_void_p; g.CreateCompatibleDC.argtypes = [ctypes.c_void_p]
    g.CreateCompatibleBitmap.restype = ctypes.c_void_p; g.CreateCompatibleBitmap.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
    g.SelectObject.restype = ctypes.c_void_p; g.SelectObject.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    g.BitBlt.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_uint]
    g.GetDIBits.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint, ctypes.c_uint, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint]
    g.DeleteObject.argtypes = [ctypes.c_void_p]; g.DeleteDC.argtypes = [ctypes.c_void_p]
    msg = wm.W.MSG()
    def pump(sec):
        t = time.time()
        while time.time() - t < sec:
            while u.PeekMessageW(ctypes.byref(msg), None, 0, 0, 1):
                u.TranslateMessage(ctypes.byref(msg)); u.DispatchMessageW(ctypes.byref(msg))
            time.sleep(0.005)
    pump(4)
    cur = {"i": 0}
    wm.frame_index = wv.frame_index = lambda now: cur["i"]
    hwnd = panel.hwnd; sheet = wv.SKINS[wv.CURRENT["skin"]]["sheet"]
    def grab(l, t, r, b):
        w, h = r - l, b - t
        hdc = u.GetDC(hwnd); mdc = g.CreateCompatibleDC(hdc); bmp = g.CreateCompatibleBitmap(hdc, w, h); old = g.SelectObject(mdc, bmp)
        g.BitBlt(mdc, 0, 0, w, h, hdc, l, t, 0xCC0020)
        bi = ctypes.create_string_buffer(struct.pack("IiiHHIIiiII", 40, w, -h, 1, 32, 0, 0, 0, 0, 0, 0) + b"\0" * 16)
        buf = ctypes.create_string_buffer(w * h * 4); g.GetDIBits(mdc, bmp, 0, h, buf, bi, 0)
        g.SelectObject(mdc, old); g.DeleteObject(bmp); g.DeleteDC(mdc); u.ReleaseDC(hwnd, hdc)
        return bytes(buf)
    res = {"frames": sheet["frames"], "compared": 0, "mismatch": [], "fast_used": 0, "layer_box": None}
    for i in range(sheet["frames"]):
        cur["i"] = i
        panel.layer.valid = False; panel.invalidate_mascot(); u.UpdateWindow(hwnd)      # percorso completo
        box = panel.layer.box; res["layer_box"] = box
        if box is None: res["error"] = "nessuna mascotte singola: percorso rapido non usato"; break
        full = grab(*box)
        used = panel.layer.valid
        panel.invalidate_mascot(); u.UpdateWindow(hwnd)                                   # percorso rapido (se valido)
        fast = grab(*box); res["fast_used"] += int(used); res["compared"] += 1
        if full != fast: res["mismatch"].append(i)
    print("VERIFICA", json.dumps(res), flush=True)
    sys.exit(0 if res["compared"] == sheet["frames"] and not res["mismatch"] and res["fast_used"] == res["compared"] else 1)


panel = wm.Panel()
if a.mode == "verify": verify()
prof = cProfile.Profile() if a.mode == "prof" else None
threading.Thread(target=controller, args=(panel, prof), daemon=True).start()
if prof: prof.enable()      # nel thread dell'interfaccia: comprende anche le prime pitture e l'assestamento
panel.run()
if prof: prof.disable()
print("RISULTATO", json.dumps(result), flush=True)
if prof:
    s = io.StringIO(); st = pstats.Stats(prof, stream=s).sort_stats("tottime"); st.print_stats(a.top)
    print("PROFILO tottime (thread interfaccia, finestra %.0f s)" % a.window); print(s.getvalue(), flush=True)
