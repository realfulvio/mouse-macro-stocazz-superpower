#!/usr/bin/env python3
"""Orchestratore delle prove di fedelta' (Windows). Per ogni strumento in tools.json esegue N riproduzioni
della macro di riferimento con il logger esterno acceso e salva un CSV per ripetizione.

  python run_trials.py --tool tinytask --scenario dpi100 --runs 30 --out ..\\data

Il PC di prova deve essere una VM pulita da snapshot (README: 'Banco di prova'), ripristinata PRIMA di ogni strumento.
Durante la prova non toccare mouse e tastiera della VM. Il lancio della riproduzione usa l'hotkey dello strumento
(tools.json), inviato con keybd_event: e' input iniettato, ma il logger confronta solo mouse (ldown/lup/wheel).
"""
import argparse, ctypes, json, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
VK = {**{f"F{i}": 0x6F + i for i in range(1, 13)}, "CTRL": 0x11, "ALT": 0x12, "SHIFT": 0x10, "PAUSE": 0x13,
      "SCROLL": 0x91, **{c: ord(c) for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"}}


def press(combo):
    keys = [VK[k.upper()] for k in combo.split("+")]
    u = ctypes.windll.user32
    for k in keys: u.keybd_event(k, 0, 0, 0)
    time.sleep(0.05)
    for k in reversed(keys): u.keybd_event(k, 0, 2, 0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tool", required=True); ap.add_argument("--scenario", default="dpi100")
    ap.add_argument("--runs", type=int, default=30); ap.add_argument("--out", required=True)
    ap.add_argument("--tools-json", default=str(HERE / "tools.json")); ap.add_argument("--settle", type=float, default=3.0)
    a = ap.parse_args()
    cfg = json.load(open(a.tools_json, encoding="utf-8"))[a.tool]
    spec = json.load(open(HERE.parent / "macros" / "reference.spec.json"))
    dur = spec["events"][-1]["t"] + cfg.get("tail_s", 2.0)
    out = Path(a.out) / a.tool / a.scenario; out.mkdir(parents=True, exist_ok=True)
    print(f"{a.tool}: {a.runs} ripetizioni, {dur:.1f} s ciascuna. Hai {a.settle:.0f} s per mettere a fuoco la finestra obiettivo.")
    time.sleep(a.settle)
    for i in range(1, a.runs + 1):
        log = out / f"run_{i:02d}.csv"
        p = subprocess.Popen([sys.executable, str(HERE.parent / "logger" / "inputlogger.py"), "--out", str(log),
                              "--duration", str(dur + 2.0), "--no-moves"])
        time.sleep(1.0)                      # il logger e' pronto
        press(cfg["play_hotkey"])
        p.wait()
        if cfg.get("stop_hotkey_after_run"): press(cfg["stop_hotkey_after_run"])
        time.sleep(cfg.get("rest_s", 1.5))
        print(f"  run {i:02d}/{a.runs} ok", flush=True)


if __name__ == "__main__":
    main()
