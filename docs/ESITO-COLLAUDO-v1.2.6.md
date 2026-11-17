# Collaudo Windows v1.2.6

## Identità dell’artifact

- Build [43977864481](https://github.com/realfulvio/mouse-macro-stocazz-superpower/actions/runs/43977864481), commit `e558d66444292e7b53fe0f678b3342d45fcdaa4a`.
- ZIP `MouseMacroStocazzSuperpower-Windows-v1.2.6.zip`: **19.053.281 byte**, SHA-256 `4ba5d0221b6b45adf79684706067dada255f2fdf7a8f856847cbdd4c73ddef8c`.
- 360 test, 92 skip di piattaforma, nessun fallimento; manifest, CRC, tutti i 133 file, corrispondenza dei sorgenti e runtime originale verificati.
- La preparazione della release cambia versione, metadati e documentazione. Motore e backend coincidono con l’ottimizzazione qualificata nella PR #48. Soglie congelate invariate.

## Collaudo dell’esatto ZIP contro la release 1.2.5

Run [43978226559](https://github.com/realfulvio/mouse-macro-stocazz-superpower/actions/runs/43978226559), tutti i job completati. Baseline SHA-256 `def843426d25dc0d12a5344c750a156e81f3b5567390df816337908c09174975`, AMD Family 25 Model 17; candidato Intel Family 6 Model 106. Host diversi: le differenze di CPU non dimostrano da sole un effetto del codice.

Exe portabile, alternativa cmd e installazione per utente passano; processo installato dal runtime previsto, versione nel registro e collegamenti presenti. Bambola: 97/97 fotogrammi equivalenti. UIPI: alto→alto 13/13/3; medio→alto 0/0/0, avviso amministratore completo, macro non partita e zero giri in entrambi. Cattura finale dell’avviso ispezionata. Trenta ripetizioni per ZIP, logger esterno.

| Misura | 1.2.5 | 1.2.6 | Lettura |
|---|---:|---:|---|
| Posizione mediana / p95, px | 0 / 0 | 0 / 0 | passa |
| Eventi persi / extra su 870 | 0 / 0 | 0 / 0 | passa |
| Errore intervallo mediano, ms | 4,4030 | 0,7300 | passa ≤5 |
| Errore intervallo p95, ms | 29,5018 | 27,7273 | non passa ≤16 in entrambi; non validabile qui |
| Deriva p95, ms | 38,1237 | 29,2969 | passa ≤50 |
| CPU idle, media 3×20 s, % di un core | 1,5900 | 2,1633 | **passa→non passa, diagnosticato sotto** |
| CPU registrazione, media 3×15 s, % | 3,2967 | 5,1033 | **passa→non passa, diagnosticato sotto** |
| CPU densa, media 3×15 s, % | 12,2900 | 9,2667 | ridotta, ancora sopra ≤5 |
| CPU rada, media 3×15 s, % | 2,1200 | 2,7767 | passa ≤5 |
| CPU idle 60 s, media 57 campioni, % | 1,6688 | 2,2754 | **passa→non passa, diagnosticato sotto** |
| Memoria privata idle max, MiB | 48,39 | 47,67 | passa ≤150 |
| Avvio caldo mediana / p95, s | 0,283 / 0,30950 | 0,3075 / 0,38415 | passa ≤2 / ≤3; 15/15 per lato |

Il verde dei job non significa che ogni soglia sia passata. Le tre regressioni booleane del confronto tra host diversi restano intatte in `comparison.json`; nessuna replica viene eliminata.

## Diagnosi mirata sullo stesso host degli ZIP finali

Prima della pubblicazione, run [44039061976](https://github.com/realfulvio/mouse-macro-stocazz-superpower/actions/runs/44039061976): due coppie in ordine AB/BA, solo registrazione e riposo, finestre da 60 s per ciascuna condizione. Nessuna riproduzione intermedia; gli stessi ZIP sono verificati tramite SHA-256. Il banco di diagnosi risiede sul ramo `bench/windows-126-cpu-check`; nessuna modifica al programma misurato.

Host comune: `AMD64 Family 25 Model 17 Stepping 1, AuthenticAMD`, `Windows-2025Server-10.0.26100-SP0`.

| Carico | Prima, finestre % | Dopo, finestre % | Media prima → dopo % |
|---|---|---|---|
| Riposo | 1,2500 · 1,2000 | 1,3300 · 1,2200 | 1,2250 → 1,2750 |
| Registrazione | 3,8800 · 3,0500 | 3,9100 · 2,9700 | 3,4650 → 3,4400 |

Nessuna soglia prima passata diventa fallita nel confronto controllato. Registrazione e riposo non eseguono la funzione di attesa modificata; codice e runtime identici nelle parti interessate, precedenti prove isolate e confronto controllato sono coerenti con variabilità del runner, senza garantire stabilità su ogni PC. Si conserva il risultato sopra soglia del confronto originale: non viene sostituito con il controllo successivo.

## Attese sullo stesso host e qualificazione dell’ottimizzazione

Il collaudo finale comprende anche 30 coppie AB/BA di 64 scadenze da 8 ms: 1.920 scadenze e 300 richieste di stop per pacchetto. CPU delle sole attese media 3,8114→0,9154% di un core, ritardo mediano 3,0143→0,0899 ms, p95 11,9515→0,2786 ms. Anticipo massimo 0,0498→0,0495 ms, entro la tolleranza preesistente di 50 μs. Attesa interrotta p95 15,7030→15,6817 ms; massimi 16,1610→16,9681 ms. Quest’ultima misura include il timer che imposta lo stop: nessuna promessa di latenza Windows entro 10 ms.

La qualificazione precedente della PR #48 sullo stesso host misurava CPU densa 11,7367→5,1733%, circa −56%, e registrazione isolata 4,47→4,4933%. [Tutti i risultati precedenti e le anomalie](../bench/data/runner-github/ottimizzazione-attese-risultati.md). Le note di release riferiscono questo confronto controllato, non attribuiscono il medesimo valore a tutti i runner.

## Dati e limiti

Dati finali in [`43978226559`](../bench/data/runner-github/43978226559/), diagnosi in [`44039061976`](../bench/data/runner-github/44039061976/). Gli archivi `*-measurements.zip` contengono tutti i CSV/JSON, log e macro degli artifact, esclusi runtime/sorgenti estratti e PNG; la cattura UIPI è conservata separatamente. Estrarre in cartelle `baseline` / `candidate`, copiare `warning-medium.png` in `candidate/acceptance/uipi/`, poi eseguire `compare_packages.py <cartella>` per rigenerare i verdetti. **Il comando termina con stato 1 per le regressioni booleane del confronto originale, mantenute per trasparenza.** La diagnosi successiva ha un sommario separato.

P95 su hardware dedicato, DPI misto, più monitor, giochi, durata ≥4 h, VirusTotal/SmartScreen e usabilità con persone non misurati. CPU densa ancora sopra soglia, nessuna garanzia di prestazioni universali. Pubblicare l’esatto artifact del build indicato, senza ricompilarlo.
