# Confronto esatto ZIP Windows 1.2.4 → 1.2.5

Run [43951916704](https://github.com/realfulvio/mouse-macro-stocazz-superpower/actions/runs/43951916704), commit `5d12a5e91c2db3b5f28791419f3f3c052b1ec3fd`. Tutti i tre job completati con successo. Artifact originali: baseline `14270952466`, candidato `14268954847`.

I due archivi `*-measurements.zip` conservano tutti i JSON, CSV (30 ripetizioni ciascuno), macro e log di misura degli artifact, esclusi runtime/sorgenti estratti e PNG. Le schermate complete di exe/cmd/installazione restano negli artifact; l’avviso del candidato è conservato qui in `warning-medium.png` e ispezionato visivamente. Gli archivi di misure non sono pacchetti installabili.

Per rigenerare il confronto, dalla radice del repository:

```bash
mkdir -p /tmp/mmss-compare/baseline /tmp/mmss-compare/candidate
unzip bench/data/runner-github/43951916704/baseline-measurements.zip -d /tmp/mmss-compare/baseline
unzip bench/data/runner-github/43951916704/candidate-measurements.zip -d /tmp/mmss-compare/candidate
cp bench/data/runner-github/43951916704/warning-medium.png /tmp/mmss-compare/candidate/acceptance/uipi/
python bench/data/runner-github/43951916704/compare_packages.py /tmp/mmss-compare
```

`comparison.json` contiene valori, verdetti booleani e lista delle soglie passate prima ma fallite dopo (vuota). CPU profilo: media delle tre finestre di uguale durata; ogni finestra resta riportata. Riposo 60 s: stessa media dei campioni usata dall’orchestratore MMSS, 57 campioni; Private Bytes convertiti in MiB. Soglie congelate intatte. Non equivale a certificare il p95 temporale sui runner condivisi o l’assenza di regressioni su ogni PC.

Baseline AMD Family 25 Model 17, candidato AMD Family 25 Model 1: runner separati, hardware diverso. Nessuna selezione delle ripetizioni. Il rapporto completo è in [`docs/ESITO-COLLAUDO-v1.2.5.md`](../../../../docs/ESITO-COLLAUDO-v1.2.5.md).
