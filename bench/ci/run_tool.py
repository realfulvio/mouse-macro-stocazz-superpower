#!/usr/bin/env python3
"""Banco di prova su runner Windows: UNO strumento per VM pulita. Scarica da fonte ufficiale, verifica l'hash dove l'autore lo pubblica,
esegue N ripetizioni della macro di riferimento con il logger esterno, poi misura risorse a riposo e avvio.
  python bench/ci/run_tool.py --tool mmss|ahk|tinytask|ideal --runs 30 --out results
Stampa i CSV grezzi nel log tra marcatori RAW (il job non puo' fare push) e li salva come artifact."""
import argparse, ctypes, hashlib, json, os, shutil, struct, subprocess, sys, time, urllib.request, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "bench")); sys.path.insert(0, str(ROOT / "bench" / "ci"))
import reference_macro, analyze  # noqa: E402
u = ctypes.windll.user32
VK = {"CTRL": 0x11, "ALT": 0x12, "SHIFT": 0x10, "ENTER": 0x0D, "F8": 0x77}

TOOLS = {
    "mmss": {"url": "https://github.com/realfulvio/mouse-macro-stocazz-superpower/releases/download/v1.2.3/MouseMacroStocazzSuperpower-Windows-v1.2.3.zip",
             "sha256": "3b9e795f25bc4c8b4d46ee2cfe481521c1f5e432d71cf7630198c70f7e25a45e", "hash_source": "digest della release GitHub v1.2.3 e SHA256SUMS-v1.2.3.txt"},
    "ahk": {"url": "https://github.com/AutoHotkey/AutoHotkey/releases/download/v2.0.31/AutoHotkey_2.0.31.zip",
            "sha256": "ca1a595aca4528755d8d4cd7fed23d497a37bd9a0b6892072612d68dee1bd00a", "hash_source": "note della release AutoHotkey v2.0.31"},
    "ideal": {"url": None, "sha256": None, "hash_source": "nessun programma: riproduzione con SendInput e attese QPC (riferimento del runner)"},
    "tinytask": {"url": "https://github.com/ron896/cJpzsJZwG/releases/download/tt/tinytask.exe", "sha256": None, "hash_source": "nessun hash pubblicato dall'autore: registrato qui",
                 "fallback": ["https://dl.tinytask.net/with-editor.exe", "https://dl.tinytask.net/micro-with-editor.exe"]},
}


def press(*keys):
    codes = [VK[k] for k in keys]
    for c in codes: u.keybd_event(c, 0, 0, 0)
    time.sleep(0.06)
    for c in reversed(codes): u.keybd_event(c, 0, 2, 0)


def download(url, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) bench-download",
        "Referer": "https://tinytask.net/download.html"})
    with urllib.request.urlopen(req, timeout=120) as r, open(dest, "wb") as f:
        shutil.copyfileobj(r, f)
    return hashlib.sha256(dest.read_bytes()).hexdigest()


def set_display():
    """Prova 1920x1080 se il driver la offre; altrimenti lascia com'e'. Ritorna (w, h)."""
    b = ctypes.create_string_buffer(220); struct.pack_into("H", b, 68, 220)
    modes = []
    for i in range(500):
        if not u.EnumDisplaySettingsW(None, i, b): break
        modes.append(struct.unpack_from("III", b, 168))
    print("modalita' schermo disponibili:", sorted(set(modes))[-8:], flush=True)
    if any(m[1] == 1920 and m[2] == 1080 for m in modes):  # (bpp, larghezza, altezza)
        b = ctypes.create_string_buffer(220); struct.pack_into("H", b, 68, 220); u.EnumDisplaySettingsW(None, -1, b)
        struct.pack_into("I", b, 172, 1920); struct.pack_into("I", b, 176, 1080); struct.pack_into("I", b, 72, 0x00080000 | 0x00100000)
        print("ChangeDisplaySettings ->", u.ChangeDisplaySettingsW(b, 0), flush=True); time.sleep(3)
    return u.GetSystemMetrics(0), u.GetSystemMetrics(1)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--tool", required=True, choices=TOOLS); ap.add_argument("--runs", type=int, default=30)
    ap.add_argument("--out", default="results"); ap.add_argument("--idle-s", type=int, default=60); ap.add_argument("--startups", type=int, default=15)
    a = ap.parse_args(); cfg = TOOLS[a.tool]
    out = Path(a.out) / a.tool; out.mkdir(parents=True, exist_ok=True)
    u.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
    w, h = set_display(); print(f"schermo di prova {w}x{h}", flush=True)
    work = Path(os.environ.get("RUNNER_TEMP", "C:/bench")) / "bench_tool"; shutil.rmtree(work, ignore_errors=True)
    # 1. download + hash ("ideal" non scarica nulla: e' il riferimento del runner, serve a separare il rumore dell'ambiente da quello dei programmi)
    used, f, got = None, None, None
    for url in ([] if a.tool == "ideal" else [cfg["url"]] + cfg.get("fallback", [])):     # link elencati nella pagina download ufficiale, in ordine
        try:
            f = work / Path(url).name; got = download(url, f); used = url; print("scaricato da", url, flush=True); break
        except Exception as error:
            print("download fallito", url, error, flush=True)
    if used is None and a.tool != "ideal": sys.exit("nessun link di download funzionante")
    cfg = {**cfg, "url": used}
    ok = cfg["sha256"] is None or got == cfg["sha256"]
    inv = {"tool": a.tool, "url": cfg["url"], "bytes": f.stat().st_size if f else 0, "sha256": got, "expected": cfg["sha256"], "hash_ok": ok, "hash_source": cfg["hash_source"],
           "screen": [w, h], "os": sys.platform, "cpu": os.environ.get("PROCESSOR_IDENTIFIER", "")}
    print("INVENTARIO", json.dumps(inv), flush=True); (out / "inventario.json").write_text(json.dumps(inv, indent=1))
    if not ok: sys.exit("hash non corrisponde: mi fermo")
    d = work / "x"; d.mkdir()
    if f is None: pass
    elif f.suffix == ".zip":
        with zipfile.ZipFile(f) as z: z.extractall(d)
    else: shutil.copy(f, d / f.name)
    # 2. macro di riferimento
    ev = reference_macro.build(w, h); spec = {"width": w, "height": h, "events": ev}
    (out / "reference.spec.json").write_text(json.dumps(spec)); spec_path = out / "reference.spec.json"
    dur = ev[-1]["t"] + 2.0
    procs = []
    if a.tool == "mmss":
        pkg = next(p.parent.parent for p in d.rglob("pythonw.exe") if p.parent.name == "runtime")
        (out / "reference.mmr").write_text(json.dumps(reference_macro.to_mmr(ev, w, h, 0, 0)))
        exe = pkg / "runtime" / "pythonw.exe"; app = str(pkg / "app" / "windows_main.py")
        def trigger():
            subprocess.Popen([str(exe), "-B", app, "--run", str((out / "reference.mmr").resolve()), "--repeat", "1"], cwd=pkg)
            time.sleep(3.0); press("ENTER")        # conferma "Riprodurre la macro?"
        idle_cmd, proc_name, startup = [str(exe), "-B", app], "pythonw", (str(exe), 'pythonw', f'-B "{app}"')
    elif a.tool == "ahk":
        exe = next(d.rglob("AutoHotkey64.exe")); script = out / "reference.ahk"; script.write_text(reference_macro.to_ahk(ev), encoding="utf-8")
        procs.append(subprocess.Popen([str(exe), str(script)])); time.sleep(2)
        def trigger(): press("F8")
        idle_cmd, proc_name, startup = None, "AutoHotkey64", (str(exe), "AutoHotkey64", f'"{script}"')
    elif a.tool == "ideal":
        import injector
        def trigger(): injector.play(spec)
        idle_cmd, proc_name, startup = None, None, None
    else:
        exe = d / f.name; tt = subprocess.Popen([str(exe)]); procs.append(tt); time.sleep(3)
        import injector
        for c in (VK["CTRL"], VK["SHIFT"], VK["ALT"]): u.keybd_event(c, 0, 0, 0)
        u.keybd_event(ord("R"), 0, 0, 0); time.sleep(0.06); u.keybd_event(ord("R"), 0, 2, 0)
        for c in (VK["ALT"], VK["SHIFT"], VK["CTRL"]): u.keybd_event(c, 0, 2, 0)
        time.sleep(1.5); injector.play(spec); time.sleep(1.0)
        for c in (VK["CTRL"], VK["SHIFT"], VK["ALT"]): u.keybd_event(c, 0, 0, 0)
        u.keybd_event(ord("R"), 0, 0, 0); time.sleep(0.06); u.keybd_event(ord("R"), 0, 2, 0)
        for c in (VK["ALT"], VK["SHIFT"], VK["CTRL"]): u.keybd_event(c, 0, 2, 0)
        time.sleep(1.5)
        def trigger():
            for c in (VK["CTRL"], VK["SHIFT"], VK["ALT"]): u.keybd_event(c, 0, 0, 0)
            u.keybd_event(ord("P"), 0, 0, 0); time.sleep(0.06); u.keybd_event(ord("P"), 0, 2, 0)
            for c in (VK["ALT"], VK["SHIFT"], VK["CTRL"]): u.keybd_event(c, 0, 2, 0)
        idle_cmd, proc_name, startup = None, exe.stem, (str(exe), exe.stem, "")
    # 3. fedelta'
    runs = out / "fedelta"; runs.mkdir()
    for i in range(1, a.runs + 1):
        log = runs / f"run_{i:02d}.csv"
        lg = subprocess.Popen([sys.executable, str(ROOT / "bench" / "logger" / "inputlogger.py"), "--out", str(log), "--duration", str(dur + 8), "--no-moves"])
        time.sleep(1.2); trigger(); lg.wait(); time.sleep(1.0)
        print(f"run {i:02d}/{a.runs}", flush=True)
    thr = json.load(open(ROOT / "bench" / "thresholds.json"))
    res = analyze.evaluate(spec, sorted(str(p) for p in runs.glob("run_*.csv")), thr)
    (out / "sommario_fedelta.json").write_text(json.dumps(res, indent=1))
    print("SOMMARIO", json.dumps({k: v for k, v in res.items() if k != "per_run"}), flush=True)
    for p in sorted(runs.glob("run_*.csv")): print(f"RAW BEGIN {a.tool}/{p.name}\n{p.read_text()}RAW END", flush=True)
    for p in procs:
        try: p.kill()
        except Exception: pass
    if a.tool == "ideal":
        print("RIEPILOGO " + json.dumps({"tool": "ideal", "schermo": inv["screen"], "fedelta": {"verdetto": res["verdict"], "run": res["runs"], "pos_px": res["pos_error_px"],
              "intervallo_ms": res["interval_error_abs_ms"], "deriva_ms": res["drift_max_ms"], "mancanti": res["missing_total"], "extra": res["extra_total"]}}), flush=True)
        return
    # 4. risorse a riposo e avvio (script PowerShell)
    ps = lambda *c: subprocess.run(["pwsh", "-NoProfile", "-File", *c], check=False)
    cmd = idle_cmd or ([str(exe), str(script)] if a.tool == "ahk" else [str(exe)])
    pr = subprocess.Popen(cmd); time.sleep(10)          # lascia assestare l'avvio, poi 60 s a riposo
    ps(str(ROOT / "bench/tools/measure_resources.ps1"), "-Name", proc_name, "-Seconds", str(a.idle_s), "-Out", str(out / "risorse_riposo.csv")); pr.kill()
    time.sleep(2)
    if a.tool != "ahk":   # AutoHotkey non ha una finestra principale: il tempo di avvio "finestra visibile" non e' definito
        ps(str(ROOT / "bench/tools/measure_startup.ps1"), "-Exe", startup[0], "-ProcName", startup[1], "-ArgumentList", startup[2], "-Runs", str(a.startups),
           "-Out", str(out / "avvio.csv"), "-TimeoutS", "30")
    for name in ("risorse_riposo.csv", "avvio.csv"):
        p = out / name
        if p.exists(): print(f"RAW BEGIN {a.tool}/{name}\n{p.read_text(encoding='utf-8-sig')}RAW END", flush=True)
    summary(a.tool, out, res, inv)


def _num(x):
    try: return float(str(x).replace(",", "."))
    except ValueError: return None


def summary(tool, out, res, inv):
    """Riepilogo compatto in fondo al log (mediana, p95, varianza): e' la riga da leggere."""
    import csv, statistics
    r = {"tool": tool, "pacchetto_MB": round(inv["bytes"] / 1e6, 3), "schermo": inv["screen"], "fedelta": {
         "verdetto": res["verdict"], "run": res["runs"], "pos_px": res["pos_error_px"], "intervallo_ms": res["interval_error_abs_ms"],
         "deriva_ms": res["drift_max_ms"], "mancanti": res["missing_total"], "extra": res["extra_total"], "controlli": res["checks"]}}
    p = out / "risorse_riposo.csv"
    if p.exists():
        rows = list(csv.DictReader(open(p, encoding="utf-8-sig")))
        cpu = [v for v in (_num(x["cpu_pct_of_core"]) for x in rows) if v is not None]; mem = [v for v in (_num(x["private_mb"]) for x in rows) if v is not None]
        if cpu: r["riposo"] = {"n": len(cpu), "cpu_core_pct": analyze.summary(cpu), "private_mb_max": max(mem) if mem else None, "processi": rows[-1].get("procs")}
    p = out / "avvio.csv"
    if p.exists():
        rows = list(csv.DictReader(open(p, encoding="utf-8-sig")))
        warm = [v for v in (_num(x["startup_s"]) for x in rows if x["ok"] == "1" and x["cold"] == "0") if v is not None]
        r["avvio"] = {"riusciti": sum(x["ok"] == "1" for x in rows), "totali": len(rows), "caldo_s": analyze.summary(warm) if warm else None,
                      "freddo_s": next((_num(x["startup_s"]) for x in rows if x["cold"] == "1" and x["ok"] == "1"), None)}
    print("RIEPILOGO " + json.dumps(r), flush=True)


if __name__ == "__main__":
    main()
