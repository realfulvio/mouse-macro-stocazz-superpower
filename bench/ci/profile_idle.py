#!/usr/bin/env python3
"""Profilo del pannello a riposo (Windows): da dove viene la CPU dell'animazione.
  python bench/ci/profile_idle.py --mode cpu     # CPU totale del processo (tutti i thread) in una finestra, senza profiler
  python bench/ci/profile_idle.py --mode prof    # cProfile del thread dell'interfaccia: funzioni per tempo proprio
Avvia windows_main.Panel dal sorgente nella sessione corrente, aspetta l'assestamento, misura, poi esce con WM_QUIT.\nIn modo prof il profilo comprende anche l'assestamento iniziale (cProfile ingrandisce il costo del codice Python: serve per la ripartizione, non per i valori assoluti)."""
import argparse, ctypes, cProfile, io, json, pstats, sys, threading, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
ap = argparse.ArgumentParser(); ap.add_argument("--mode", choices=("cpu", "prof"), required=True)
ap.add_argument("--warm", type=float, default=12); ap.add_argument("--window", type=float, default=30); ap.add_argument("--top", type=int, default=28)
a = ap.parse_args()
import windows_main as wm  # noqa: E402

k = ctypes.windll.kernel32; u = ctypes.windll.user32
tid = k.GetCurrentThreadId(); result = {}


def cpu_seconds():
    c, e, kt, ut = (ctypes.c_ulonglong() for _ in range(4))
    k.GetProcessTimes(k.GetCurrentProcess(), ctypes.byref(c), ctypes.byref(e), ctypes.byref(kt), ctypes.byref(ut))
    return (kt.value + ut.value) / 1e7


def controller(panel, prof):
    time.sleep(a.warm)
    c0, t0 = cpu_seconds(), time.perf_counter()
    time.sleep(a.window)
    c1, t1 = cpu_seconds(), time.perf_counter()
    result.update(cpu_pct_of_core=round(100 * (c1 - c0) / (t1 - t0), 2), window_s=round(t1 - t0, 1),
                  shown=panel.shown, animating=panel.animating, skin=wm.CURRENT["skin"], dpi=panel.dpi)
    u.PostThreadMessageW(tid, 0x12, 0, 0)   # WM_QUIT: esce da GetMessageW


panel = wm.Panel()
prof = cProfile.Profile() if a.mode == "prof" else None
threading.Thread(target=controller, args=(panel, prof), daemon=True).start()
if prof: prof.enable()      # nel thread dell'interfaccia: comprende anche le prime pitture e l'assestamento
panel.run()
if prof: prof.disable()
print("RISULTATO", json.dumps(result), flush=True)
if prof:
    s = io.StringIO(); st = pstats.Stats(prof, stream=s).sort_stats("tottime"); st.print_stats(a.top)
    print("PROFILO tottime (thread interfaccia, finestra %.0f s)" % a.window); print(s.getvalue(), flush=True)
