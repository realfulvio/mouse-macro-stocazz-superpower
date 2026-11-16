# Dati grezzi dal banco su runner GitHub (2026-11-16)

`<run>/<strumento>/` contiene: `fedelta/run_NN.csv` (log del logger esterno: `t_ms,event,x,y,data,injected`), `sommario_fedelta.json` (mediana, p95, varianza, verdetto), `risorse_riposo.csv`, `inventario.json` (URL, byte, SHA-256, schermo, CPU) e la macro di riferimento usata.

- Run `43912272395`: mmss, ahk, tinytask (1920×1080).
- Run `43918554473`: mmss, ahk, ideal (riferimento SendInput + QPC). Il job tinytask di questa esecuzione non è incluso: i suoi dati, se presenti, sono nel ramo `bench-data/43918554473-tinytask`.

Rifare: `.github/workflows/bench.yml` (push su `bench/**` oppure avvio manuale), oppure in locale su una VM Windows pulita `python bench/ci/run_tool.py --tool mmss|ahk|tinytask|ideal --runs 30 --out results`.
