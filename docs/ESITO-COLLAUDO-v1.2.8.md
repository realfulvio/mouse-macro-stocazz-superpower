# Collaudo Windows v1.2.8

## Identità dell’artifact

- Build [44436238808](https://github.com/realfulvio/mouse-macro-stocazz-superpower/actions/runs/44436238808), commit `cb9c27244543ecf495a6ce055eaf596f223b56e4` (merge della PR #58 su `main`).
- ZIP `MouseMacroStocazzSuperpower-Windows-v1.2.8.zip`: **15.300.857 byte**, SHA-256 `5b38242d35eface6a8aa6fdadc437176178ee311c638364f2334d93a4ddd9c62`. È l’esatto file collaudato e poi pubblicato: nessuna ricompilazione fra collaudo e release.
- Suite verde su windows-latest e ubuntu-latest con Python 3.13 e 3.14, sia sulla PR sia nel build di release. `qa/check_package.py` verifica anche che ogni `.pyc` del pacchetto (42 file, hash verificato PEP 552) corrisponda al proprio sorgente e che le WebP della versione Linux non siano nello ZIP.
- La 1.2.8 non cambia il motore di riproduzione né le attese della 1.2.6/1.2.7. Le modifiche sono quelle della PR #58: bytecode nel pacchetto, ingresso corto dei launcher, import pigri, ridisegno parziale della barra compatta, titolo a 1 Hz, sprite sheet restituito dopo la cache, traccia di riproduzione limitata, scritture atomiche, `EndPaint` sempre ed `errore.log` una volta per errore.

## Confronto sullo stesso host contro la 1.2.7 pubblicata

Misura principale per la regola «nessuna regressione»: `bench/ci/paired_compare.py` (workflow `paired.yml`) avvia lo ZIP 1.2.7 pubblicato (SHA-256 `20d02c8d…57f9`) e lo ZIP 1.2.8 **sullo stesso runner**, in ordine ABBA, con `pythonw.exe -B app\windows_main.py` come i launcher. Otto run su cinque tipi di CPU (Intel Family 6 Model 106 e 207, AMD Family 25 Model 1 e 17, AMD Family 26 Model 2), codice identico a quello pubblicato. Mediana delle mediane di ogni run:

| Misura | 1.2.7 | 1.2.8 | Rapporto | Min–max fra i run | Run in cui scende |
|---|---:|---:|---:|---:|---:|
| Avvio: pannello visibile, s | 0,270 | 0,164 | 0,61 | 0,59–0,61 | 8/8 |
| Avvio: pannello pronto (risponde), s | 0,275 | 0,168 | 0,61 | 0,59–0,62 | 8/8 |
| CPU a riposo, % di un core | 1,68 | 1,54 | 0,92 | 0,85–1,10 | 6/8 |
| Memoria privata a riposo, massimo, MiB | 43,7 | 34,0 | 0,78 | 0,77–0,80 | 8/8 |
| CPU in registrazione, % | 5,29 | 4,19 | 0,79 | 0,50–1,11 | 6/8 |
| CPU in riproduzione, flusso denso, % | 4,95 | 4,97 | 1,01 | 0,73–1,39 | 4/8 |
| CPU in riproduzione, macro di riferimento, % | 2,21 | 2,11 | 0,95 | 0,64–1,24 | 5/8 |
| Oggetti GDI a riposo | 25 | 25 | 1,00 | | |
| Crescita di GDI e handle nella finestra di riposo | 0 / 0 | 0 / 0 | | | |
| Pacchetto, MB | 19,06 | 15,30 | 0,80 | | 8/8 |
| Import di `windows_main` (`-X importtime`), ms | 145,7 | 101,3 | 0,70 | 0,67–0,85 | 8/8 |
| Compilazione dello script di avvio a ogni lancio, ms | 18,9 | 1,4 | 0,07 | | 8/8 |

Medie di tutti i giri (32 per lato in attività, 48 a riposo): riposo 1,55 → 1,49, registrazione 5,10 → 4,13, riproduzione densa 4,96 → 4,88, macro di riferimento 2,19 → 1,98 (% di un core). Il rumore del singolo giro è di circa ±1 punto in attività e ±0,5 a riposo: avvio, memoria, pacchetto e registrazione scendono, riposo e riproduzione restano invariati entro il rumore. Nei primi quattro run la riproduzione densa risultava più alta di 0,6 punti medi; quattro run in più sullo stesso codice l’hanno riportata alla pari, e il percorso per evento del motore non è cambiato (la traccia registra solo clic e tasti).

Run: [44426852718](https://github.com/realfulvio/mouse-macro-stocazz-superpower/actions/runs/44426852718), [44427014559](https://github.com/realfulvio/mouse-macro-stocazz-superpower/actions/runs/44427014559), [44427225998](https://github.com/realfulvio/mouse-macro-stocazz-superpower/actions/runs/44427225998), [44427359951](https://github.com/realfulvio/mouse-macro-stocazz-superpower/actions/runs/44427359951), [44430429027](https://github.com/realfulvio/mouse-macro-stocazz-superpower/actions/runs/44430429027), [44430434501](https://github.com/realfulvio/mouse-macro-stocazz-superpower/actions/runs/44430434501), [44430439757](https://github.com/realfulvio/mouse-macro-stocazz-superpower/actions/runs/44430439757), [44432842713](https://github.com/realfulvio/mouse-macro-stocazz-superpower/actions/runs/44432842713) (artifact `paired-compare`).

## Collaudo dell’esatto ZIP contro la release 1.2.7

Run [44436989071](https://github.com/realfulvio/mouse-macro-stocazz-superpower/actions/runs/44436989071), tutti i job completati, verdetto complessivo positivo. Baseline SHA-256 `20d02c8db8999720e67554469e8a7c7000e43a820111535a44c76562359357f9` (ZIP pubblicato della 1.2.7) su AMD Family 25 Model 1; candidato su Intel Family 6 Model 207. **Host diversi**: le differenze di CPU fra le due colonne dipendono anche dalla macchina e non dimostrano da sole un effetto del codice (per questo c’è il confronto sullo stesso host qui sopra).

Exe portabile, alternativa cmd e installazione per utente passano per entrambi i pacchetti (titolo `Mouse Macro 1.2.8 · hcok · …`). Bambola: 97/97 fotogrammi identici fra percorso rapido e completo in entrambi. UIPI: alto→alto 13/13/3; medio→alto 0/0/0 con avviso amministratore, macro non partita e zero giri, in entrambi. Trenta ripetizioni per ZIP, logger esterno.

| Misura | 1.2.7 | 1.2.8 | Lettura |
|---|---:|---:|---|
| Posizione mediana / p95, px | 0 / 0 | 0 / 0 | passa |
| Eventi persi / extra su 870 | 0 / 0 | 0 / 0 | passa |
| Errore intervallo mediano, ms | 0,7215 | 0,7270 | passa ≤5; differenza dentro la variabilità |
| Errore intervallo p95, ms | 28,0532 | 27,9855 | non passa ≤16 in entrambi; non validabile su runner condiviso |
| Deriva p95, ms | 29,3371 | 29,9285 | passa ≤50 |
| CPU idle, media 3×20 s, % di un core | 1,4333 | 1,6667 | passa ≤2 |
| CPU registrazione, media 3×15 s, % | 5,8000 | 4,5833 | 1.2.7 sopra ≤5, 1.2.8 sotto |
| CPU densa, media 3×15 s, % | 4,9300 | 6,8067 | 1.2.8 sopra ≤5 su questo host (un giro a 9,27); stesso host: 4,96 → 4,88 |
| CPU rada (macro di riferimento), media 3×15 s, % | 2,0467 | 2,5333 | passa ≤5 |
| CPU idle 60 s, media 57 campioni, % | 1,3133 | 2,2257 | 1.2.8 sopra ≤2 su questo host; stesso host: 1,55 → 1,49 |
| Memoria privata idle max, MiB | 47,60 | 41,27 | passa ≤150 |
| Avvio caldo, mediana di 14 prove, s | 0,322 | 0,195 | passa ≤2 |
| Avvio a freddo, 1 prova, s | 0,419 | 0,240 | passa ≤3 |
| Pacchetto, MB | 19,06 | 15,30 | passa ≤25 |

Due soglie passate dalla 1.2.7 non passano per la 1.2.8 in questo run: CPU idle 60 s (2,23 contro ≤2) e CPU densa (6,81 contro ≤5). Le due colonne vengono però da macchine diverse, e l’host del candidato è più lento anche sul codice che la 1.2.8 non ha toccato: il gestore del timer dell’animazione, identico nelle due versioni, costa 54 µs a chiamata contro 33 µs (+64%), più di quanto cresca la pittura (553 contro 423 µs, +31%). Sullo stesso host, con lo stesso metodo di avvio e di campionamento, i due valori non crescono (tabella precedente, compresi due run sullo stesso tipo di CPU Intel Model 207: riposo 1,84 → 1,71, riproduzione densa 5,96 → 5,44 in media). Il verdetto di fedeltà delle 30 ripetizioni è «NON PASSA» per entrambi i pacchetti solo per il p95 degli intervalli (`interval_p95`), che su un runner condiviso non è valutabile; tutti gli altri controlli passano.

## Attese sullo stesso host

Trenta coppie AB/BA di 64 scadenze da 8 ms con 10 richieste di stop, eseguite sullo stesso host per i due pacchetti: ritardo mediano 0,045 → 0,049 ms, p95 0,286 → 0,279 ms, CPU media delle sole attese 0,71 → 0,61% di un core, latenza di stop mediana 10,99 → 11,34 ms. Come atteso, la 1.2.8 non modifica le attese.

## Dati e limiti

Dati grezzi negli artifact del run [44436989071](https://github.com/realfulvio/mouse-macro-stocazz-superpower/actions/runs/44436989071) (`package-acceptance-baseline`, `package-acceptance-candidate`) e dei run `paired.yml` elencati sopra, conservati 90 giorni.

P95 su hardware dedicato, DPI misto, più monitor, giochi, durata ≥4 h, VirusTotal/SmartScreen e usabilità con persone non misurati. La traccia limitata delle riproduzioni infinite, la pittura fallita senza ciclo al 100%, `errore.log` scritto una volta e le scritture atomiche sono coperti dai test automatici (inclusi i messaggi Win32 reali sul runner Windows), non da una prova a mano di ore. Nessuna garanzia di prestazioni universali.
