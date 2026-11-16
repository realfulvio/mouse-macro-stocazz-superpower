#!/usr/bin/env python3
"""Analisi di fedelta': confronta i CSV del logger esterno con la spec della macro di riferimento.

  python analyze.py --spec reference.spec.json --runs "data/tinytask/dpi100/run_*.csv" [--thresholds thresholds.json] [--json out.json]

Per ogni run: abbina in ordine gli eventi ldown/lup/wheel registrati a quelli attesi (stesso tipo),
ancorando il tempo al primo ldown. Misura:
  - errore di posizione (px, distanza euclidea) per ogni evento abbinato;
  - errore di intervallo (ms): (t_i - t_{i-1}) osservato - atteso, per intervalli >= 100 ms;
  - deriva (ms): |t_i - t_0| osservato - atteso, massimo per run;
  - eventi mancanti ed extra (solo ldown/lup/wheel; i movimenti non contano).
Riporta n, mediana, p95, varianza (deviazione standard) e verdetto PASSA/NON PASSA sulle soglie fissate.
Gli eventi iniettati dal sistema di test (flag injected) NON vengono scartati: gli strumenti iniettano
tutti, quindi il flag non distingue; la finestra temporale e' definita dal logger acceso solo durante la prova.
"""
import argparse, csv, glob, json, math, statistics, sys
from pathlib import Path

KINDS = ("ldown", "lup", "wheel")


def pctl(v, p):
    if not v: return float("nan")
    s = sorted(v); k = (len(s) - 1) * p / 100.0
    lo, hi = math.floor(k), math.ceil(k)
    return s[lo] if lo == hi else s[lo] + (s[hi] - s[lo]) * (k - lo)


def summary(v):
    if not v: return {"n": 0}
    return {"n": len(v), "median": statistics.median(v), "p95": pctl(v, 95), "mean": statistics.fmean(v),
            "stdev": statistics.stdev(v) if len(v) > 1 else 0.0,
            "variance": statistics.variance(v) if len(v) > 1 else 0.0, "min": min(v), "max": max(v)}


def read_run(path):
    out = []
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["event"] in KINDS:
                out.append((float(r["t_ms"]), r["event"], int(r["x"]), int(r["y"]), int(r["data"])))
    return out


def analyze_run(spec_events, obs):
    """Abbinamento in ordine per tipo. Ritorna (pos_err, interval_err, drift_max, missing, extra)."""
    exp = [(e["t"] * 1000.0, e["kind"], e["x"], e["y"]) for e in spec_events]
    used, pairs, missing = 0, [], 0
    j = 0
    for t, kind, x, y in exp:
        while j < len(obs) and obs[j][1] != kind: j += 1   # salta eventi di altro tipo (extra)
        if j >= len(obs): missing += 1; continue
        pairs.append(((t, kind, x, y), obs[j])); j += 1
    extra = len(obs) - len(pairs)
    if not pairs: return [], [], float("nan"), missing, extra
    pos = [math.hypot(o[2] - e[2], o[3] - e[3]) for e, o in pairs]
    e0, o0 = pairs[0][0][0], pairs[0][1][0]
    drift = [abs((o[0] - o0) - (e[0] - e0)) for e, o in pairs]
    iv = []
    for (e1, o1), (e2, o2) in zip(pairs, pairs[1:]):
        if e2[0] - e1[0] >= 100.0:
            iv.append((o2[0] - o1[0]) - (e2[0] - e1[0]))
    return pos, iv, max(drift), missing, extra


def evaluate(spec, run_paths, thr):
    pos, iv, drift, miss, extra, per_run = [], [], [], [], [], []
    for p in run_paths:
        a, b, d, m, x = analyze_run(spec["events"], read_run(p))
        pos += a; iv += [abs(v) for v in b]; drift.append(d); miss.append(m); extra.append(x)
        per_run.append({"run": Path(p).name, "missing": m, "extra": x, "drift_max_ms": d})
    f = thr["fidelity"]
    s = {"runs": len(run_paths), "pos_error_px": summary(pos), "interval_error_abs_ms": summary(iv),
         "drift_max_ms": summary([d for d in drift if d == d]), "missing_total": sum(miss), "extra_total": sum(extra)}
    checks = {
        "repetitions>=min": len(run_paths) >= thr["repetitions_min"],
        "pos_median": s["pos_error_px"].get("median", 1e9) <= f["pos_error_px_median_max"],
        "pos_p95": s["pos_error_px"].get("p95", 1e9) <= f["pos_error_px_p95_max"],
        "interval_median": s["interval_error_abs_ms"].get("median", 1e9) <= f["interval_error_ms_median_max"],
        "interval_p95": s["interval_error_abs_ms"].get("p95", 1e9) <= f["interval_error_ms_p95_max"],
        "drift_p95": s["drift_max_ms"].get("p95", 1e9) <= f["drift_ms_p95_max"],
        "missing": max(miss or [0]) <= f["missing_events_max"],
        "extra": max(extra or [0]) <= f["extra_events_max"],
    }
    s["checks"] = checks; s["verdict"] = "PASSA" if all(checks.values()) else "NON PASSA"; s["per_run"] = per_run
    return s


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True); ap.add_argument("--runs", required=True)
    ap.add_argument("--thresholds", default=str(Path(__file__).with_name("thresholds.json")))
    ap.add_argument("--json")
    a = ap.parse_args()
    spec = json.load(open(a.spec)); thr = json.load(open(a.thresholds))
    paths = sorted(glob.glob(a.runs))
    if not paths: sys.exit("nessun file di run trovato")
    res = evaluate(spec, paths, thr)
    if a.json: Path(a.json).write_text(json.dumps(res, indent=1))
    pe, ie = res["pos_error_px"], res["interval_error_abs_ms"]
    print(f"run={res['runs']}  verdetto={res['verdetto'] if 'verdetto' in res else res['verdict']}")
    print(f"posizione px: mediana {pe.get('median',0):.2f}  p95 {pe.get('p95',0):.2f}  var {pe.get('variance',0):.3f}")
    print(f"intervallo ms: mediana {ie.get('median',0):.2f}  p95 {ie.get('p95',0):.2f}  var {ie.get('variance',0):.3f}")
    print(f"mancanti {res['missing_total']}  extra {res['extra_total']}")
    for k, v in res["checks"].items(): print(("  ok  " if v else "  NO  ") + k)
