# Collaudo Windows v1.2.5

## Pacchetto e provenienza

- Build GitHub [43951421876](https://github.com/realfulvio/mouse-macro-stocazz-superpower/actions/runs/43951421876), commit `5d12a5e91c2db3b5f28791419f3f3c052b1ec3fd`.
- ZIP `MouseMacroStocazzSuperpower-Windows-v1.2.5.zip`: **19.053.039 byte**.
- SHA-256: `def843426d25dc0d12a5344c750a156e81f3b5567390df816337908c09174975`.
- Build: 355 test raccolti, 92 esclusi secondo la piattaforma; nessun fallimento. Manifest, CRC e corrispondenza di tutti i 133 file verificati; runtime ufficiale Python 3.13.16 preservato.
- Baseline: ZIP pubblicato v1.2.4, SHA-256 `b4be1b44f5f49611438a1090d5a2c708236183be0a2bf02b01d53cb1e29814dd`.

## Procedura dell'esatto ZIP

Run [43951916704](https://github.com/realfulvio/mouse-macro-stocazz-superpower/actions/runs/43951916704), stesso script per baseline e candidato, runner Windows separati. Le differenze tra host e il carico condiviso limitano l'interpretazione dei tempi; non è un esperimento su hardware dedicato.

Il banco verifica l'exe portabile, il launcher cmd, l'installazione per utente (processo dal runtime installato, versione nel registro e presenza dei collegamenti), i 97 fotogrammi di Bambola, tre finestre CPU idle da 20 s e attive da 15 s, input verso finestre elevate, e 30 ripetizioni della macro di riferimento con logger esterno. Dopo la fedeltà: 60 s di risorse a riposo e 15 avvii, di cui 14 a caldo. Le prove CPU importano i file estratti dallo ZIP con il runtime incluso; la fedeltà avvia il suo pythonw.exe. Le proposte automatiche di aggiornamento ricevono No nel banco, senza modificare il pacchetto.

## Esiti

Tutti i job completati con successo; exe portabile, cmd e installazione per utente funzionanti in entrambi i pacchetti. Processo installato verificato nella cartella utente; versione del registro e collegamenti verificati. Fotogrammi Bambola equivalenti 97/97 per ciascun pacchetto. Schermata dell’installazione e [avviso reale del candidato](../bench/data/runner-github/43951916704/warning-medium.png) ispezionati.

| Misura | v1.2.4 | v1.2.5 | Soglia / esito |
|---|---:|---:|---|
| Posizione mediana / p95, px | 0 / 0 | 0 / 0 | ≤1 / ≤2, passa entrambe |
| Eventi persi / extra su 870 | 0 / 0 | 0 / 0 | zero, passa entrambe |
| Intervallo mediana, ms | 4,2370 | 4,0180 | ≤5, passa entrambe |
| Intervallo p95, ms | 28,6324 | 28,7958 | ≤16, non passa entrambe; non validabile qui |
| Deriva p95, ms | 36,3941 | 33,9287 | ≤50, passa entrambe |
| CPU idle, media 3×20 s, % di un core | 1,8467 | 1,9567 | ≤2, passa entrambe |
| CPU registrazione, media 3×15 s, % | 5,6600 | 4,9300 | ≤5, prima non passa / dopo passa |
| CPU riproduzione densa, media 3×15 s, % | 13,4367 | 13,1267 | ≤5, non passa entrambe |
| CPU riproduzione rada, media 3×15 s, % | 2,6733 | 2,8467 | ≤5, passa entrambe |
| CPU idle 60 s, media 57 campioni, % | 1,5481 | 1,8094 | ≤2, passa entrambe |
| Memoria privata idle massima, MiB | 47,98 | 48,15 | ≤150, passa entrambe |
| Avvio caldo mediana / p95, s | 0,277 / 0,37445 | 0,361 / 0,37270 | ≤2 / ≤3, passa entrambe |
| Avvii riusciti | 15/15 | 15/15 | 14 a caldo, primo 0,405 / 0,414 s |
| ZIP, byte | 19.051.139 | 19.053.039 | ≤25 MB, passa entrambe |

Finestre CPU conservate senza selezione:

- Idle: 1,87 · 2,19 · 1,48 → 1,80 · 1,80 · 2,27%.
- Registrazione: 6,87 · 3,96 · 6,15 → 5,00 · 5,73 · 4,06%.
- Riproduzione densa: 13,02 · 13,54 · 13,75 → 12,92 · 13,44 · 13,02%.
- Riproduzione rada: 2,40 · 3,33 · 2,29 → 3,02 · 2,81 · 2,71%.

La soglia è sulla CPU media; singole finestre idle/registrazione la superano. I precedenti risultati sopra soglia restano documentati: non si dichiara un miglioramento CPU stabile. Baseline su AMD Family 25 Model 17, candidato su Model 1; differenze di hardware e carico impediscono di attribuire le differenze dei valori al codice.

UIPI: controllo alto→alto **13 down / 13 up / 3 wheel** in entrambe. Medio→alto: input **0/0/0** in entrambe, ma v1.2.4 dichiara un giro completato mentre v1.2.5 rifiuta l’avvio, zero giri, stato errore con istruzione amministratore interamente visibile. Il controllo copre i bersagli esistenti al preflight e leggibili, non finestre future o desktop sicuri.

**Nessuna soglia precedentemente passata diventa fallita** in questo confronto. Il verdetto meccanico della fedeltà resta NON PASSA per il p95, e la CPU densa resta sopra soglia: il verde della CI non significa che tutti gli obiettivi prestazionali siano raggiunti. Motore, backend e velocità di riproduzione non modificati. La modifica grafica interessa la larghezza del messaggio nel solo stato errore compatto.

[Dati grezzi, sommario e comando di riproduzione dell’analisi](../bench/data/runner-github/43951916704/README.md). Soglie in `bench/thresholds.json` invariate.

## Limiti mantenuti

Il p95 degli intervalli non è validabile sui runner condivisi: il riferimento ideale del banco supera la stessa soglia. La riproduzione densa resta un costo noto; l'ottimizzazione delle attese non fa parte di questa release. DPI misto, più monitor, giochi, durata ≥4 ore, SmartScreen e usabilità con persone non sono misurati. VirusTotal non eseguito in assenza di una chiave API disponibile. Nessuna misura Linux inclusa nel confronto.
