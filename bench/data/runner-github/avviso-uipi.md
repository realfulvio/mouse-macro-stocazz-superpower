# Avviso prima della riproduzione verso finestre elevate

Baseline: `cpu-attiva-uipi.md`, run `43941664269`, commit `f146f7c`.
Prima: medio→alto, zero eventi consegnati, pannello «Completati 1 giri.».

La modifica legge TokenIntegrityLevel del processo corrente e dei processi
delle finestre visibili ai punti di clic/rotella della macro; per i tasti usa
la finestra attiva. Il pannello viene prima spostato fuori dai bersagli.
Il controllo è applicato anche all'avvio `.mmr`/`--run`, prima della creazione
del player. Un bersaglio di integrità superiore impedisce l'avvio e produce:

> Bersaglio elevato.
> Riapri con «Esegui come amministratore».

Nessuna elevazione automatica. Nessuna chiamata aggiunta al ciclo temporizzato;
`macro/engine.py` e `macro/windows_backend.py` invariati. Cache di punti e PID
limitata alla singola verifica; gli handle di processo e token vengono chiusi
anche quando la lettura fallisce. I livelli sconosciuti non vengono scambiati
per processi elevati.

Limiti: fotografia delle finestre correnti, non prevede finestre aperte o
spostate dalla macro. Token non leggibili, finestre nascoste/disabilitate,
desktop sicuro e giochi non sono coperti. I passaggi del cursore senza clic
non vengono usati come bersagli. Il controllo non garantisce la consegna di
ogni input; `checked_input` rimane invariato.

Verifiche: mock per livelli uguali/inferiori/superiori, token sconosciuti,
bersagli successivi, cache per avvio e chiusura handle. La prova reale Windows
usa `uipi_test.py --expect-warning`: richiede C con 13/13/3 e un giro completo,
D con 0/0/0, stato errore, macro non partita e avviso esplicito. La mancanza
del risultato atteso fa fallire la CI. Il run `43944349396` (commit `fe3e6a3`) ha verificato tutti questi requisiti: C 13/13/3, pronto, un giro; D 0/0/0, errore, zero giri e `partita=false`. Il testo finale è abbreviato per rientrare nel pannello.

Fonti primarie:
- [SendInput e UIPI](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-sendinput)
- [GetTokenInformation](https://learn.microsoft.com/en-us/windows/win32/api/securitybaseapi/nf-securitybaseapi-gettokeninformation)
- [WindowFromPoint e finestre escluse](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-windowfrompoint)

## Condizione del banco per gli aggiornamenti

Il profilo `43944349209` è rimasto nello step pixel dopo la pubblicazione esterna della v1.2.4, mentre il checkout riportava ancora v1.2.3. Il messaggio modale di aggiornamento può bloccare il ciclo di messaggi della verifica. Il banco risponde ora No alla sola proposta automatica: mantiene controllo rete e gestione del rifiuto, senza modificare updater o sorgenti del pacchetto. La stessa condizione vale prima e dopo; non è una prova dell'installazione di aggiornamenti.

## Confronto di fedeltà dal sorgente

Run [43944349328](https://github.com/realfulvio/mouse-macro-stocazz-superpower/actions/runs/43944349328), 30 ripetizioni prima e dopo con stesso logger, macro e analizzatore. Baseline `6ecbf002`, checkout dopo `898569be` (merge di `fe3e6a3`). Sommari completi nella cartella del run; CSV negli artifact `source-fidelity-before` e `source-fidelity-after`.

| Metrica | Prima | Dopo | Soglia |
|---|---:|---:|---|
| Posizione mediana / p95 | 0 / 0 px | 0 / 0 px | passa in entrambi |
| Eventi persi / extra | 0 / 0 su 870 | 0 / 0 su 870 | passa in entrambi |
| Intervallo mediana | 4,3065 ms | 4,2390 ms | passa ≤5 in entrambi |
| Intervallo p95 | 28,8923 ms | 28,4945 ms | supera 16 in entrambi; non validabile su questo runner |
| Deriva p95 | 32,4054 ms | 31,9729 ms | passa ≤50 in entrambi |

Nessuna soglia cambia da passa a non passa. Il verdetto meccanico globale resta NON PASSA per il p95, come nel riferimento ideale del banco. Questi dati non dimostrano un aumento di velocità e non sono il collaudo dello ZIP. Gli SHA-256 di `macro/engine.py` e `macro/windows_backend.py` sono identici prima/dopo, registrati nei sommari.

## Verifica intermedia dell’avviso e CPU

Sul commit `d1761c3`, il run `43947163037` conferma ancora C=13/13/3, pronto, un giro; D=0/0/0, errore, zero giri, `partita=false` e testo abbreviato completo. Il run `43947162655` completa la verifica pixel (97/97) e le misure con rifiuto automatico della proposta di aggiornamento nel banco: idle 1,48 · 0,70 · 2,19%; registrazione 3,75 · 3,44 · 3,44%; densa 13,02 · 8,02 · 8,65%; rada 1,15 · 3,23 · 1,56%. Densa sopra soglia, rada sotto; idle non stabile fra le finestre. La variabilità tra runner impedisce di attribuire un miglioramento CPU al preflight; il confronto del pacchetto usa una procedura identica fra baseline e candidato. I 480 WM_PAINT per 20 s rimangono in tutte le tre finestre idle. La misura con cProfile (0,81% su 25 s) è esclusa dai confronti.

Il secondo A/B dal sorgente, sul testo finale (`43947162649`, baseline `6ecbf002`, dopo `60ff47e8`), conferma 30 ripetizioni, posizione 0/0 px e zero eventi persi/extra. Mediana intervalli 4,8515→4,7195 ms (passa ≤5); p95 28,3683→28,6431 ms (sopra soglia in entrambi, non validabile qui); deriva p95 29,5413→40,4686 ms (passa ≤50 in entrambi). Quindi nessuna soglia passa→non passa, ma i numeri non migliorano tutti: nessuna pretesa di aumento prestazionale. Hash di motore/backend ancora identici. Sommario nella cartella del run.

Il testo finale è ridotto a due frasi brevi, con a capo esplicito, per il riquadro del pannello compatto (172×64, font effettivo 16). La prova UIPI con avviso acquisisce `warning-medium.png` dal vero pannello a integrità media prima della chiusura. La pausa di un secondo è nel banco dopo il risultato, non nella riproduzione.

La cattura del run `43950328529` ha mostrato che il messaggio era ancora troncato con Bambola compatta: la mascotte lasciava soltanto 100 px di larghezza. In stato errore la scheda compatta usa ora tutta la larghezza del messaggio e omette la mascotte decorativa. Layout e animazione negli stati pronto/registrazione/riproduzione restano identici. La correzione viene verificata su una nuova cattura prima del rilascio.

## Avviso leggibile: verifica finale dal sorgente

Run [43951420288](https://github.com/realfulvio/mouse-macro-stocazz-superpower/actions/runs/43951420288), commit `c5a7c5d`: conferma C 13/13/3, pronto, un giro; D 0/0/0, errore, zero giri e macro non partita. La [cattura del vero pannello compatto](43951420288/warning-medium.png) è stata ispezionata: entrambe le frasi, compresa l’istruzione amministratore, sono interamente visibili. JSON e conteggi grezzi sono conservati nella stessa cartella. Nessun cambiamento a motore, backend, velocità o attese.

Il profilo del layout definitivo (`43951420324`, `c5a7c5d`) verifica ancora 97/97 fotogrammi identici. CPU dal sorgente, in % di un core: idle 2,03 · 2,03 · 1,87; registrazione 6,15 · 4,37 · 3,85; densa 13,96 · 13,96 · 14,06; rada 3,12 · 2,60 · 3,44. La media delle tre finestre idle è 1,98%, registrazione 4,79%, ma singole finestre superano le soglie e le tornate precedenti restano valide: risultati non stabili sul runner. La riproduzione densa resta sopra soglia e quella rada sotto. Il record con cProfile (2,25% su 25 s) è separato. Dati in `43951420324/profile.json`.

## Confronti del layout definitivo

| Run | Mediana intervalli prima → dopo, ms | P95 intervalli prima → dopo, ms | Deriva p95 prima → dopo, ms |
|---|---:|---:|---:|
| 43951420250 (PR #44) | 4,6440 → 3,6695 | 28,7903 → 28,9750 | 34,9862 → 40,0532 |
| 43951432413 (candidato 1.2.5) | 3,9005 → 4,2355 | 28,9234 → 28,6542 | 32,3149 → 33,5396 |

Entrambi usano 30 ripetizioni per lato: 0 px mediana/p95, zero eventi persi/extra su 870. Le medesime soglie passano prima e dopo (il p95 degli intervalli continua a non passare meccanicamente e non è validabile nel runner condiviso). I tempi non migliorano in modo uniforme; non si deduce un miglioramento prestazionale. Baseline `1d6e792`, checkout dopo `de756daf` e `e5cfa0a5`; hash motore/backend identici. Sommari completi nelle cartelle dei run.
