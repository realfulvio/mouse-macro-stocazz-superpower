#!/usr/bin/env python3
"""Finestra obiettivo (Windows): riceve davvero i clic e la rotella e li registra con timestamp QPC.
Serve per la prova 'finestre elevate' (UIPI) e DPI: avviala normale oppure come amministratore e riproduci la macro
da un processo a integrita' diversa. Confronta gli eventi che ARRIVANO alla finestra con quelli del logger esterno.
  python target_window.py --out target_run_01.csv [--duration 40]
"""
import argparse, csv, ctypes, time, tkinter as tk
ap = argparse.ArgumentParser(); ap.add_argument("--out", required=True); ap.add_argument("--duration", type=float, default=0)
a = ap.parse_args()
try: ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
except Exception: pass
f = open(a.out, "w", newline="", encoding="utf-8"); w = csv.writer(f); w.writerow(["t_ms", "event", "x_root", "y_root", "delta"])
t0 = time.perf_counter()
root = tk.Tk(); root.attributes("-fullscreen", True, "-topmost", True); cv = tk.Canvas(root, bg="#202428", highlightthickness=0); cv.pack(fill="both", expand=True)
cv.create_text(40, 30, anchor="w", fill="white", font=("Segoe UI", 14), text="Finestra obiettivo - Esc per chiudere")
def log(ev, e, d=0): w.writerow([f"{(time.perf_counter()-t0)*1000:.3f}", ev, e.x_root, e.y_root, d])
root.bind("<ButtonPress-1>", lambda e: log("ldown", e)); root.bind("<ButtonRelease-1>", lambda e: log("lup", e))
root.bind("<MouseWheel>", lambda e: log("wheel", e, e.delta)); root.bind("<Escape>", lambda e: root.destroy())
if a.duration: root.after(int(a.duration * 1000), root.destroy)
root.mainloop(); f.close()
