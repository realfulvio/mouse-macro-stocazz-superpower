# Avviso prima della riproduzione verso finestre elevate

Baseline: `cpu-attiva-uipi.md`, run `43941664269`, commit `f146f7c`.
Prima: medio→alto, zero eventi consegnati, pannello «Completati 1 giri.».

La modifica legge TokenIntegrityLevel del processo corrente e dei processi
delle finestre visibili ai punti di clic/rotella della macro; per i tasti usa
la finestra attiva. Il pannello viene prima spostato fuori dai bersagli.
Il controllo è applicato anche all'avvio `.mmr`/`--run`, prima della creazione
del player. Un bersaglio di integrità superiore impedisce l'avvio e produce:

> Bersaglio con privilegi più alti. Riapri Mouse Macro con «Esegui come amministratore» per riprodurre.

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
