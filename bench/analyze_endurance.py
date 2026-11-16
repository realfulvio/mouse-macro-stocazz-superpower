#!/usr/bin/env python3
"""Lunga durata: periodo dei cicli e crescita della memoria.

  python analyze_endurance.py --logger data/tool/endurance_logger.csv --resources data/tool/endurance_resources.csv \
      --cycle-s 17.3 [--thresholds thresholds.json]

Cicli: ogni 'ldown' che segue una pausa piu' lunga di meta' periodo inizia un nuovo ciclo. Riporta mediana, p95 e varianza del
periodo, il numero di cicli, il drift (p95 |periodo - mediana|) e la pendenza di Private Bytes in MB/h (regressione lineare).
"""
import argparse, csv, json, statistics, sys
from pathlib import Path
from analyze import pctl, summary


def cycles(logger_csv, cycle_s):
    starts, last = [], None
    for r in csv.DictReader(open(logger_csv, encoding="utf-8")):
        if r["event"] != "ldown": continue
        t = float(r["t_ms"]) / 1000
        if last is None or t - last > cycle_s / 2: starts.append(t)
        last = t
    return starts


def slope_mb_per_hour(resources_csv):
    xs, ys = [], []
    for r in csv.DictReader(open(resources_csv, encoding="utf-8-sig")):
        xs.append(float(r["t_s"])); ys.append(float(str(r["private_mb"]).replace(",", ".")))
    if len(xs) < 3: return float("nan")
    mx, my = statistics.fmean(xs), statistics.fmean(ys)
    den = sum((x - mx) ** 2 for x in xs)
    return (sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / den) * 3600 if den else float("nan")


def evaluate(logger_csv, resources_csv, cycle_s, thr, hours):
    st = cycles(logger_csv, cycle_s)
    periods = [b - a for a, b in zip(st, st[1:])]
    med = statistics.median(periods) if periods else float("nan")
    dev = [abs(p - med) * 1000 for p in periods]
    sl = slope_mb_per_hour(resources_csv)
    e = thr["endurance"]
    out = {"cycles": len(st), "hours": hours, "period_s": summary(periods), "period_dev_ms": summary(dev), "private_mb_per_hour": sl}
    out["checks"] = {"duration": hours >= e["duration_hours_min"], "memory_growth": sl <= e["private_mb_growth_per_hour_max"],
                     "period_stable_p95_ms<=50": pctl(dev, 95) <= 50}
    out["verdict"] = "PASSA" if all(out["checks"].values()) else "NON PASSA"
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--logger", required=True); ap.add_argument("--resources", required=True)
    ap.add_argument("--cycle-s", type=float, required=True); ap.add_argument("--thresholds", default=str(Path(__file__).with_name("thresholds.json")))
    a = ap.parse_args(); thr = json.load(open(a.thresholds))
    last = max((float(r["t_ms"]) for r in csv.DictReader(open(a.logger, encoding="utf-8"))), default=0) / 3.6e6
    print(json.dumps(evaluate(a.logger, a.resources, a.cycle_s, thr, last), indent=1))
    print("NB: gli arresti anomali (crash) si contano a mano dal registro eventi e vanno aggiunti al verdetto.", file=sys.stderr)
