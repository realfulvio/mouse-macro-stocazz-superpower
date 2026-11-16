# Avviso prima della riproduzione verso finestre elevate

Baseline: `cpu-attiva-uipi.md`, run `43941664269`, commit `f146f7c`.
Prima: medio→alto, zero eventi consegnati, pannello «Completati 1 giri.».

La modifica legge TokenIntegrityLevel del processo corrente e dei processi
delle finestre visibili ai punti di clic/rotella della macro; per i tasti usa
la finestra attiva. Il pannello viene prima spostato fuori dai bersagli.
Il controllo è applicato anche all'avvio `.mmr`/`--run`, prima della creazione
del player. Un bersaglio di integrità superiore impedisce l'avvio e produce:

> Una finestra bersaglio ha privilegi più alti di Mouse Macro. Windows bloccherebbe i clic o i tasti. Chiudi Mouse Macro e riaprilo con «Esegui come amministratore», poi riprova.

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
del risultato atteso fa fallire la CI. Esiti Windows da acquisire prima del merge.

Fonti primarie:
- [SendInput e UIPI](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-sendinput)
- [GetTokenInformation](https://learn.microsoft.com/en-us/windows/win32/api/securitybaseapi/nf-securitybaseapi-gettokeninformation)
- [WindowFromPoint e finestre escluse](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-windowfrompoint)
