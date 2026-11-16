# Banco di prova comparativo (Windows)

Confronto riproducibile di Mouse Macro Stocazz Superpower con TinyTask, AutoHotkey, Pulover's Macro Creator, Jitbit Macro Recorder, Mini Mouse Macro, OP Auto Clicker e Actiona.
Perimetro: **solo Windows** (richiesta di Luca, 2026-11-16).

| File | A cosa serve |
|---|---|
| `PREREGISTRAZIONE.md` + `thresholds.json` | soglie passa/non passa, fissate prima di misurare |
| `RIVALI.md` | perché questi rivali e cosa è verificato su fonti primarie |
| `PROCEDURA.md` | come rifare tutto, passo per passo |
| `USABILITA.md`, `usability_analyze.py` | test con utenti nuovi, punteggio SUS |
| `matrice-funzioni.csv` | funzioni verificate a mano (colonne "non verificato" = ancora da provare) |
| `logger/inputlogger.py` | logger di input esterno (WH_MOUSE_LL/WH_KEYBOARD_LL, QPC) |
| `reference_macro.py`, `macros/` | macro di riferimento identica per tutti (spec, .mmr, .ahk) |
| `analyze.py`, `analyze_endurance.py` | statistiche: mediana, p95, varianza; verdetti |
| `tools/` | orchestratore, risorse, avvio, inventario/hash, VirusTotal, finestra obiettivo, metronomo |
| `data/` | dati grezzi (vedi `data/STATO-MISURE.md`) |
| `tests/` | test dell'analisi (`python -m unittest discover -s bench/tests`) |

Rapporto: `docs/analisi/confronto-rivali.md` e `/mnt/project-files/analisi/confronto-rivali.md`.
