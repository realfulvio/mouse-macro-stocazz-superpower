# Ottimizzazione CPU della riproduzione Windows

Candidato app `11751f9e7f9f23985d0a96ded139cee0197009e2`, build [43960296764](https://github.com/realfulvio/mouse-macro-stocazz-superpower/actions/runs/43960296764), 360 test / 92 skip di piattaforma, nessun fallimento. ZIP candidato sperimentale ancora etichettato 1.2.5, **non pubblicato**: 19.053.281 byte, SHA-256 `1bfeecda34a77dc8ca2e79ee3f2c7843107cbcd4cf6bac79396fcd9729b9b80f`. La release pubblica 1.2.5 è la baseline: 19.053.039 byte, SHA-256 `def843426d25dc0d12a5344c750a156e81f3b5567390df816337908c09174975`. Versione e asset pubblici non sostituiti.

## Modifica e contratto

Solo `_wait_until` su Windows: attesa tramite `time.sleep` (timer ad alta risoluzione nel runtime distribuito Python 3.13), spin finale da 2–3 ms a massimo 0,3 ms. Sleep richiesto a tranche ≤10 ms, controllo Event prima e dopo; per attese lunghe resta `Event.wait`. Scadenze e tolleranza di anticipo preesistente di 50 μs, sequenza, coordinate, velocità, pause e durata minima delle azioni invariati. Nessuna modifica al backend. Percorso Linux invariato.

I 10 ms sono la tranche richiesta, **non una garanzia di latenza di Windows**: scheduler e timer che imposta lo stop possono ritardare. I cinque nuovi test verificano scadenze, sospensione invece di spin, stop, risveglio tardivo e scadenza già superata. I test esistenti coprono durata delle pressioni, cicli e cleanup.

## Confronto degli esatti ZIP

Run [43960726750](https://github.com/realfulvio/mouse-macro-stocazz-superpower/actions/runs/43960726750), stessa procedura, 30 ripetizioni per lato e logger esterno. Baseline su AMD Family 25 Model 17; candidato su Intel Family 6 Model 106. Non è una misura comparativa su hardware dedicato.

| Misura | Prima | Dopo | Soglia / lettura |
|---|---:|---:|---|
| Posizione mediana / p95, px | 0 / 0 | 0 / 0 | passa ≤1 / ≤2 |
| Eventi persi / extra su 870 | 0 / 0 | 0 / 0 | passa |
| Errore intervallo mediano, ms | 4,3175 | 0,6935 | passa ≤5 |
| Errore intervallo p95, ms | 28,7270 | 26,9566 | non passa ≤16 in entrambi; non validabile qui |
| Deriva p95, ms | 34,1407 | 29,1881 | passa ≤50 |
| CPU idle, media 3×20 s, % di un core | 1,4033 | 1,9267 | passa ≤2 |
| CPU registrazione, media 3×15 s, % | 3,6100 | 5,1367 | **passa→non passa: richiede diagnosi sullo stesso host** |
| CPU riproduzione densa, media 3×15 s, % | 11,6700 | 5,9333 | −49,2%; ancora sopra soglia ≤5 |
| CPU riproduzione rada, media 3×15 s, % | 2,3600 | 2,7100 | passa ≤5 |
| CPU idle 60 s, media, % | 1,3739 | 1,8077 | passa ≤2 |
| Memoria privata idle max, MiB | 48,20 | 47,62 | passa ≤150 |
| Avvio caldo mediana / p95, s | 0,281 / 0,29535 | 0,320 / 0,36480 | passa ≤2 / ≤3; 15/15 per lato |

Pixel 97/97, exe/cmd, installazione e prova UIPI riusciti per entrambi. C alto→alto 13/13/3; D medio→alto fermato prima dell’avvio con avviso. Dati completi, comprese tutte le finestre CPU, in `43960726750/comparison.json`. Il confronto originario mantiene la regressione booleana della registrazione: nessuna sua misura è stata scartata.

## Attese sullo stesso host, 30 coppie AB/BA

Nello stesso run, sul runner del candidato, entrambi gli ZIP eseguono 30 repliche da 64 scadenze a 8 ms, ordine alternato. 1.920 scadenze e 300 richieste di stop per lato; nessuna iniezione di input in questa prova. Sono le funzioni degli esatti pacchetti, con i rispettivi runtime, in processi nuovi.

| Misura | Prima | Dopo |
|---|---:|---:|
| CPU media delle attese, % di un core | 7,0869 | 0,7120 |
| Ritardo mediano, ms | 2,8114 | 0,0466 |
| Ritardo p95, ms | 11,5940 | 0,2443 |
| Ritardo massimo, ms | 13,2075 | 0,5298 |
| Anticipo massimo, ms | 0,0498 | 0,0496 |
| Durata attesa interrotta, mediana / p95, ms | 11,4900 / 15,6655 | 11,4067 / 15,6891 |
| Durata attesa interrotta massima, ms | 15,9281 | 17,8094 |

CPU delle sole attese −89,95%. Mediana e p95 del ritardo migliorano sullo stesso host; anticipo resta entro i 50 μs preesistenti. La durata interrotta include il timer che richiede lo stop dopo 3 ms, non misura soltanto la reazione dopo l’effettiva impostazione dell’Event. Code di scheduler presenti, nessuna promessa di stop reale entro 10 ms. Dati grezzi nell’archivio candidato, sommario `43960726750/wait-probe-summary.json`.

## Registrazione: diagnosi sullo stesso host

Run 43965391957, tre coppie AB/BA/AB degli stessi ZIP sullo stesso host. CPU registrazione: baseline 4,79 · 4,27 · 4,48% (media 4,5133), candidato 4,69 · 3,75 · 8,02% (media 5,4867): la terza finestra del candidato mantiene il passaggio sopra soglia. CPU densa 11,46 · 12,60 · 11,15 → 5,31 · 5,52 · 4,69% (media 11,7367→5,1733, −55,9%); rada 2,57→1,8767%. Tutti i risultati in `43965391957/`.

Il codice di registrazione non chiama `_wait_until`, ma ciò da solo non risolve il verdetto. È stata quindi definita una prova diagnostica diversa prima di eseguirla: tre coppie AB/BA/AB di sole registrazioni, finestre di 60 s invece di 15 s, con entrambi gli ZIP intatti sullo stesso host e senza riproduzione intermedia. Non sostituisce né elimina i risultati precedenti. Serve a verificare se il superamento resta in una finestra più lunga, isolando il carico in cui l’ottimizzazione non è eseguita. Run [43967066526](https://github.com/realfulvio/mouse-macro-stocazz-superpower/actions/runs/43967066526), ramo separato `bench/recording-isolation`, commit del banco `4cb72475`, modifiche limitate al banco; candidato del programma invariato.

Esito registrazione isolata, tre finestre da 60 s per lato, stesso host Intel Family 6 Model 207 (diverso dall’AMD del primo confronto, uguale per entrambi i pacchetti in questa prova):

- Baseline: **4,35 · 4,58 · 4,48%**, media **4,4700%**.
- Candidato: **3,98 · 4,58 · 4,92%**, media **4,4933%**.
- Tutte le finestre e le due medie passano ≤5%; differenza media +0,0233 punti percentuali. Circa 7.400 eventi registrati per finestra. Nessuna regressione sostenuta rilevata nella registrazione isolata; non è una prova di equivalenza statistica su tutti i PC.

La registrazione non esegue la funzione cambiata, il confronto isolato lungo mantiene la soglia e le finestre brevi mostrano variazioni anche a codice invariato: queste evidenze sono coerenti con rumore/carico del banco, senza attribuire un miglioramento della registrazione al nuovo timer. Il passaggio sopra soglia nelle prove brevi resta esplicito nel JSON originario. Non si dichiara «tutte le soglie sono sempre rispettate». La CPU densa migliora in tutti i confronti sullo stesso host ma resta mediamente poco sopra il 5%; ottimizzazione accettata per riduzione CPU con precisione/tempi preservati nelle prove eseguite, con questi limiti.

## Riproducibilità e limiti

Gli archivi `43960726750/*-measurements.zip` contengono tutti i CSV/JSON, macro e log originali, esclusi runtime/sorgenti estratti e PNG. Gli artifact originali conservano anche schermate e file estratti. Per rigenerare `comparison.json`, estrarre gli archivi in directory `baseline` e `candidate`; recuperare dall’artifact candidato la cattura `acceptance/uipi/warning-medium.png` richiesta dalla verifica UIPI. Il sommario mantiene la lista delle soglie passa→non passa, non la azzera dopo la diagnosi.

L’analisi della fedeltà è `bench/analyze.py`; il protocollo delle attese è `ottimizzazione-attese-protocollo.md`. Il profilo dal sorgente 43960301646 è distinto: riproduzione densa 10,42 · 4,17 · 6,04%, pixel 97/97. I valori dimostrano variabilità del runner, non un limite CPU garantito su ogni PC. Restano non misurati p95 su hardware dedicato, DPI misto, monitor multipli, giochi, durata ≥4 h, VirusTotal/SmartScreen e usabilità con persone. Soglie congelate intatte.
