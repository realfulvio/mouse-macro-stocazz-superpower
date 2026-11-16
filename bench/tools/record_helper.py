#!/usr/bin/env python3
"""Metronomo per registrare a mano la macro di riferimento: mostra il prossimo punto (finestra a tutto schermo
trasparente con un mirino) e fa un bip quando va cliccato. Windows. Uso: python record_helper.py --spec reference.spec.json"""
import argparse, json, time, tkinter as tk, winsound

ap = argparse.ArgumentParser(); ap.add_argument("--spec", required=True); ap.add_argument("--lead", type=float, default=5.0)
a = ap.parse_args(); spec = json.load(open(a.spec))
root = tk.Tk(); root.attributes("-fullscreen", True, "-topmost", True, "-transparentcolor", "white"); root.config(bg="white", cursor="arrow")
try:
    import ctypes; ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
except Exception: pass
cv = tk.Canvas(root, bg="white", highlightthickness=0); cv.pack(fill="both", expand=True)
# attraversabile al mouse: WS_EX_TRANSPARENT | WS_EX_LAYERED
hwnd = ctypes.windll.user32.GetParent(root.winfo_id()); st = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
ctypes.windll.user32.SetWindowLongW(hwnd, -20, st | 0x20 | 0x80000)
start = time.perf_counter() + a.lead; i = 0
def tick():
    global i
    now = time.perf_counter() - start
    cv.delete("all")
    if i < len(spec["events"]):
        e = spec["events"][i]
        cv.create_oval(e["x"]-14, e["y"]-14, e["x"]+14, e["y"]+14, outline="red", width=3)
        cv.create_text(e["x"], e["y"]-28, text=f"{i+1}/{len(spec['events'])} {e['kind']}", fill="red", font=("Segoe UI", 12, "bold"))
        if now >= e["t"]:
            winsound.Beep(1200, 40); i += 1
    else:
        root.after(500, root.destroy); return
    root.after(5, tick)
root.after(10, tick); root.bind("<Escape>", lambda _e: root.destroy()); root.mainloop()
