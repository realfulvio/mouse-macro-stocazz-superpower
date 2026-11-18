# Collaudo Windows v1.2.7

## Identità dell’artifact

- Build [44281268820](https://github.com/realfulvio/mouse-macro-stocazz-superpower/actions/runs/44281268820), commit `a25b3177cd78aae2ec788a01c42c4c29ea0cb152` (merge della PR #54 su `main`).
- ZIP `MouseMacroStocazzSuperpower-Windows-v1.2.7.zip`: **19.056.242 byte**, SHA-256 `20d02c8db8999720e67554469e8a7c7000e43a820111535a44c76562359357f9`. È l’esatto file collaudato e poi pubblicato: nessuna ricompilazione fra collaudo e release.
- 372 test in locale (105 saltati perché specifici di Windows o Linux), nessun fallimento; stessa suite verde su ubuntu e windows con Python 3.13 e 3.14. Manifest e contenuto del pacchetto verificati da `qa/check_package.py` nel build.
- La 1.2.7 non cambia la parte di attesa della 1.2.6 (timer ad alta risoluzione, spin residuo massimo di 0,3 ms). Le correzioni sono quelle della PR #53: cache della validazione dei gesti, adattamento del pannello al DPI, Impostazioni che segue DPI e tray, riavvio dell’aggiornamento rinviato e senza doppio download, hash dello ZIP in streaming, versione numerica nel `.cmd`, icona del tray.

## Collaudo dell’esatto ZIP contro la release 1.2.6

Run [44282581722](https://github.com/realfulvio/mouse-macro-stocazz-superpower/actions/runs/44282581722), tutti i job completati. Baseline SHA-256 `4ba5d0221b6b45adf79684706067dada255f2fdf7a8f856847cbdd4c73ddef8c` (ZIP pubblicato della 1.2.6), Intel Family 6 Model 106; candidato AMD Family 25 Model 17. Host diversi: le differenze di CPU non dimostrano da sole un effetto del codice.

Exe portabile, alternativa cmd e installazione per utente passano per entrambi i pacchetti. Bambola: 97/97 fotogrammi equivalenti in entrambi. UIPI: alto→alto 13/13/3; medio→alto 0/0/0 con avviso amministratore, macro non partita e zero giri, in entrambi. Trenta ripetizioni per ZIP, logger esterno.

| Misura | 1.2.6 | 1.2.7 | Lettura |
|---|---:|---:|---|
| Posizione mediana / p95, px | 0 / 0 | 0 / 0 | passa |
| Eventi persi / extra su 870 | 0 / 0 | 0 / 0 | passa |
| Errore intervallo mediano, ms | 0,7145 | 0,7260 | passa ≤5; differenza dentro la variabilità |
| Errore intervallo p95, ms | 27,4073 | 28,0437 | non passa ≤16 in entrambi; non validabile su runner condiviso |
| Deriva p95, ms | 29,4120 | 29,4048 | passa ≤50 |
| CPU idle, media 3×20 s, % di un core | 1,9800 | 1,5600 | passa ≤2 |
| CPU registrazione, media 3×15 s, % | 4,8600 | 4,4800 | passa ≤5 |
| CPU densa, media 3×15 s, % | 5,6567 | 4,3067 | 1.2.6 sopra ≤5, 1.2.7 sotto |
| CPU rada (macro di riferimento), media 3×15 s, % | 2,8467 | 2,4300 | passa ≤5 |
| CPU idle 60 s, media 57 campioni, % | 1,7588 | 1,6100 | passa ≤2 |
| Memoria privata idle max, MiB | 47,80 | 47,90 | passa ≤150 |
| Pacchetto, MB | 19,05 | 19,06 | passa ≤25 |

Nessuna soglia prima passata diventa fallita. Il verdetto di fedeltà delle 30 ripetizioni è «NON PASSA» per entrambi i pacchetti solo per il p95 degli intervalli (`interval_p95`), che su un runner condiviso non è valutabile; tutti gli altri controlli passano. L’avvio caldo (15 prove per pacchetto, tutte riuscite) è sotto le soglie ≤2 / ≤3 s per entrambi; i valori fra host diversi non vanno confrontati fra loro.

## Attese sullo stesso host

Il collaudo comprende le 30 coppie AB/BA di 64 scadenze da 8 ms con 10 richieste di stop, eseguite sullo stesso host per i due pacchetti. Ritardo mediano 0,049 ms in entrambi, p95 0,293 → 0,289 ms, CPU media delle sole attese 1,32 → 0,81% di un core, latenza di stop mediana 11,40 ms in entrambi. Come atteso, la 1.2.7 non modifica le attese.

## Dati e limiti

Dati grezzi negli artifact del run [44282581722](https://github.com/realfulvio/mouse-macro-stocazz-superpower/actions/runs/44282581722) (`package-acceptance-baseline`, `package-acceptance-candidate`, conservati 90 giorni).

P95 su hardware dedicato, DPI misto, più monitor, giochi, durata ≥4 h, VirusTotal/SmartScreen e usabilità con persone non misurati. Il comportamento a 1024×768 al 125%, la finestra Impostazioni al cambio di DPI e l’aggiornamento durante una registrazione sono coperti dai test automatici (inclusi i messaggi Win32 reali sul runner Windows), non da una prova a mano su schermo. Nessuna garanzia di prestazioni universali.
