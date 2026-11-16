#!/usr/bin/env python3
"""Genera la macro di riferimento IDENTICA per tutti gli strumenti.

Uscite (stessa traiettoria, stessi tempi):
  reference.spec.json  -> verita' per analyze.py
  reference.mmr        -> Mouse Macro Stocazz Superpower
  reference.ahk        -> AutoHotkey v2 (SendInput, coordinate di schermo)
Per TinyTask / Jitbit / Pulover / Mini Mouse Macro / OP Auto Clicker la macro
si REGISTRA a mano seguendo la guida stampata da --guide (stesse coordinate, stessi tempi
con il metronomo di record_helper.py): il registratore introduce il suo errore, ed e' giusto misurarlo.

Uso: python reference_macro.py --out DIR [--origin-x 0 --origin-y 0 --width 1920 --height 1080]
Le coordinate sono in pixel fisici, relativi al monitor principale (origine 0,0).
"""
import argparse, json
from pathlib import Path

HOLD = 0.15   # s tra down e up: sopra il minimo di 0,12 s del nostro motore
GAP = 0.90    # s tra un gesto e il successivo: sopra i 0,65 s minimi del nostro motore


def build(width, height, ox=0, oy=0):
    """12 clic su griglia 4x3, 1 trascinamento, 3 scatti di rotella. Deterministica."""
    pts = [(ox + round(width * (0.15 + 0.23 * c)), oy + round(height * (0.2 + 0.3 * r)))
           for r in range(3) for c in range(4)]
    ev, t = [], 0.0
    for x, y in pts:
        ev.append({"t": round(t, 4), "kind": "ldown", "x": x, "y": y})
        ev.append({"t": round(t + HOLD, 4), "kind": "lup", "x": x, "y": y})
        t += HOLD + GAP
    x0, y0, x1, y1 = pts[0][0], pts[0][1], pts[-1][0], pts[-1][1]
    ev.append({"t": round(t, 4), "kind": "ldown", "x": x0, "y": y0})
    ev.append({"t": round(t + 1.0, 4), "kind": "lup", "x": x1, "y": y1})   # drag lungo 1 s
    t += 1.0 + GAP
    for i in range(3):
        ev.append({"t": round(t, 4), "kind": "wheel", "x": pts[5][0], "y": pts[5][1], "data": -120})
        t += GAP
    return ev


def to_mmr(events, width, height, ox, oy):
    k = {"ldown": "left_down", "lup": "left_up", "wheel": "wheel"}
    out, last = [], None
    for e in events:
        if (e["x"], e["y"]) != last:      # un MOVE prima di ogni gesto, come farebbe il registratore
            out.append({"t": max(0.0, e["t"] - 0.01), "kind": "move_abs", "dx": 0.0, "dy": 0.0,
                        "x": e["x"], "y": e["y"], "wheel": 0.0, "snap": "", "key": ""})
            last = (e["x"], e["y"])
        out.append({"t": e["t"], "kind": k[e["kind"]], "dx": 0.0, "dy": 0.0, "x": e["x"], "y": e["y"],
                    "wheel": float(e.get("data", 0)) / 120 if e["kind"] == "wheel" else 0.0, "snap": "", "key": ""})
    out.sort(key=lambda d: d["t"])
    return {"platform": "windows", "screen": [ox, oy, width, height], "layout": {}, "events": out}


def to_ahk(events):
    lines = ["#Requires AutoHotkey v2.0", "CoordMode 'Mouse', 'Screen'", "SendMode 'Input'",
             "start := 0", "DllCall('QueryPerformanceFrequency', 'Int64*', &f := 0)",
             "DllCall('QueryPerformanceCounter', 'Int64*', &q0 := 0)",
             "Wait(t) {", "  global f, q0", "  loop {", "    DllCall('QueryPerformanceCounter', 'Int64*', &q := 0)",
             "    r := t - (q - q0) / f", "    if r <= 0", "      return", "    if r > 0.003", "      Sleep(1)", "  }", "}",
             "F8::{", "  global q0", "  DllCall('QueryPerformanceCounter', 'Int64*', &q0)"]
    for e in events:
        lines.append(f"  Wait({e['t']})")
        if e["kind"] == "ldown":
            lines.append(f"  MouseMove {e['x']}, {e['y']}, 0`n  Click 'Down'")
        elif e["kind"] == "lup":
            lines.append(f"  MouseMove {e['x']}, {e['y']}, 0`n  Click 'Up'")
        else:
            lines.append(f"  MouseMove {e['x']}, {e['y']}, 0`n  Click 'WheelDown'")
    lines += ["}", "F12::ExitApp"]
    return "\n".join(lines).replace("`n", "\n")


GUIDE = """Registrazione manuale (TinyTask, Jitbit, Pulover, Mini Mouse Macro, OP Auto Clicker):
1. Avvia 'python bench/tools/record_helper.py --spec reference.spec.json': mostra a schermo il prossimo punto
   e fa un bip nel momento in cui va cliccato (metronomo), cosi' la mano segue i tempi della spec.
2. Registra con lo strumento in prova, tutta la sequenza, senza correggere gli errori.
3. Salva la macro come bench/macros/<strumento>/reference.*  Una sola registrazione, poi 30 riproduzioni.
"""

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--width", type=int, default=1920)
    ap.add_argument("--height", type=int, default=1080)
    ap.add_argument("--origin-x", type=int, default=0)
    ap.add_argument("--origin-y", type=int, default=0)
    ap.add_argument("--guide", action="store_true")
    a = ap.parse_args()
    if a.guide:
        print(GUIDE); raise SystemExit
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    ev = build(a.width, a.height, a.origin_x, a.origin_y)
    (out / "reference.spec.json").write_text(json.dumps({"width": a.width, "height": a.height, "events": ev}, indent=1))
    (out / "reference.mmr").write_text(json.dumps(to_mmr(ev, a.width, a.height, a.origin_x, a.origin_y)))
    (out / "reference.ahk").write_text(to_ahk(ev), encoding="utf-8")
    print(f"{len(ev)} eventi, durata {ev[-1]['t']:.1f} s -> {out}")
