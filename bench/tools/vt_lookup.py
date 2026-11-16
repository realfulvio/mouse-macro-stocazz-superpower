#!/usr/bin/env python3
"""Cerca su VirusTotal gli SHA-256 dell'inventario (API v3, SOLO ricerca per hash: non carica nulla).

  set VT_API_KEY=...   (chiave gratuita personale; 4 richieste/minuto)
  python vt_lookup.py data/inventory.csv data/virustotal.csv

Un file mai visto da VirusTotal risulta 'sconosciuto': non e' un esito pulito. Per quelli, caricamento manuale
dal sito DOPO aver deciso che il file puo' diventare pubblico (il nostro ZIP lo e' gia'; i rivali sono pubblici).
"""
import csv, json, os, sys, time, urllib.request, urllib.error

key = os.environ.get("VT_API_KEY") or sys.exit("imposta VT_API_KEY")
rows = list(csv.DictReader(open(sys.argv[1], encoding="utf-8-sig")))
out = []
for r in rows:
    req = urllib.request.Request("https://www.virustotal.com/api/v3/files/" + r["sha256"], headers={"x-apikey": key})
    try:
        d = json.load(urllib.request.urlopen(req, timeout=30))["data"]["attributes"]
        s = d["last_analysis_stats"]
        out.append({"file": r["file"], "sha256": r["sha256"], "malicious": s["malicious"], "suspicious": s["suspicious"],
                    "undetected": s["undetected"], "harmless": s["harmless"], "last_analysis": d.get("last_analysis_date"),
                    "engines_flagging": ";".join(sorted(k for k, v in d["last_analysis_results"].items() if v["category"] in ("malicious", "suspicious")))})
    except urllib.error.HTTPError as e:
        out.append({"file": r["file"], "sha256": r["sha256"], "malicious": "", "suspicious": "", "undetected": "", "harmless": "",
                    "last_analysis": "", "engines_flagging": "sconosciuto" if e.code == 404 else f"HTTP {e.code}"})
    time.sleep(16)
with open(sys.argv[2], "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
print(open(sys.argv[2], encoding="utf-8").read())
