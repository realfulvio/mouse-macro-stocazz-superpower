#!/usr/bin/env python3
"""Usabilita': punteggio SUS, successo e tempi per strumento.

CSV (una riga per persona e strumento): participant,tool,success(0/1),time_s,errors,sus1..sus10  (risposte 1-5)
  python usability_analyze.py data/usabilita.csv [--thresholds thresholds.json]
SUS: per le domande dispari (risp-1), per le pari (5-risp); somma x 2,5 -> 0..100.
Con n < novices_min il verdetto e' 'INSUFFICIENTE'. Il test e' indicativo: riporta sempre anche i dati grezzi.
"""
import argparse, csv, json, statistics, sys
from collections import defaultdict
from pathlib import Path


def sus(row):
    v = [int(row[f"sus{i}"]) for i in range(1, 11)]
    if any(not 1 <= x <= 5 for x in v): raise ValueError("risposte SUS fuori da 1-5")
    return 2.5 * sum((x - 1) if i % 2 == 0 else (5 - x) for i, x in enumerate(v))   # i=0 e' la domanda 1 (dispari)


def evaluate(rows, thr):
    u, by = thr["usability"], defaultdict(list)
    for r in rows: by[r["tool"]].append(r)
    out = {}
    for tool, rs in by.items():
        ok_times = [float(r["time_s"]) for r in rs if r["success"] == "1"]
        d = {"n": len(rs), "success_rate": sum(r["success"] == "1" for r in rs) / len(rs),
             "time_s_median_successful": statistics.median(ok_times) if ok_times else None,
             "sus_median": statistics.median(sus(r) for r in rs), "errors_total": sum(int(r["errors"]) for r in rs)}
        if len(rs) < u["novices_min"]: d["verdict"] = "INSUFFICIENTE"
        else:
            good = (d["success_rate"] >= u["task_success_rate_min"] and d["time_s_median_successful"] is not None
                    and d["time_s_median_successful"] <= u["task_time_s_median_max"] and d["sus_median"] >= u["sus_median_min"])
            d["verdict"] = "PASSA" if good else "NON PASSA"
        out[tool] = d
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("csv"); ap.add_argument("--thresholds", default=str(Path(__file__).with_name("thresholds.json")))
    a = ap.parse_args()
    print(json.dumps(evaluate(list(csv.DictReader(open(a.csv, encoding="utf-8-sig"))), json.load(open(a.thresholds))), indent=1))
