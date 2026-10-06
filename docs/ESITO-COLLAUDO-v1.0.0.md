# Esito dei controlli v1.0.0

Prima versione stabile. Parte dalla v0.19 (barra operativa, ripetizioni digitabili). Il motore di riproduzione e i tempi non cambiano rispetto alla v0.18.1.

## Novità rispetto alla v0.19.0

- **Opzioni più chiare**: «Cambia scheda» (Ctrl+Tab tra un giro e l'altro) e «Pagine lente» (pause più lunghe tra i click) hanno un sottotitolo; la Guida le spiega in dettaglio.
- **Testo più leggibile**: caratteri ingranditi di 1–2 px in tutta l'interfaccia; pulsante Stop della barra ridisegnato per non troncare la scritta.
- **Chiusura robusta**: finestra e tasti globali si chiudono sempre, anche se la cartella impostazioni non è scrivibile o il player è lento a fermarsi; la posizione del pannello viene salvata anche chiudendo durante registrazione o replay.
- **Registrazione**: nessuna eccezione nell'hook del mouse se la finestra del pannello sparisce.
- **File macro**: eventi incompleti o con campi sconosciuti producono un messaggio leggibile.
- **Licenza**: PolyForm Noncommercial 1.0.0 (dalla v0.19.2-beta); le versioni fino alla v0.19.1-beta restano MIT.

## Verifiche eseguite su questo ZIP

- **Suite automatica**: 141 test, 135 superati, 6 saltati (backend Linux), Python 3.13 su Windows 11.
- **Pacchetto**: CRC validi, 106 hash del manifest, sorgenti e asset identici, file originali del runtime preservati; runtime identico al pacchetto ufficiale di python.org.
- **Avvio reale** dell'exe estratto dallo ZIP: finestra «Pronto» in italiano, nessun file di errore.
- **Rendering** dell'interfaccia a 96/120/144/192 DPI su bitmap in memoria (compatta, estesa, registrazione, riproduzione, arresto).
- **Registrazione e replay con input fisico** (Windows 11, 96 DPI, finestra di prova sul monitor principale, backend e sessione del programma): 21 eventi registrati (3 click nel riquadro A, 1 nel B, un doppio click, una rotella, un trascinamento). Replay di 2 giri a **1×** in 9,0 s e a **2×** in 5,1 s, entrambi con i conteggi attesi esatti (8 pressioni, 8 rilasci, 2 doppi click, 2 rotelle): nessun click perso. Arresto durante un'azione in **5,1 ms** e nessun pulsante rimasto premuto.

## Non verificato

Il pannello grafico non è stato pilotato con mouse reale in questa versione (pulsante Stop, input numerico, Salva/Carica, DPI diversi dal 100% su monitor reali, avvio senza rete, cambio scheda nel browser). Le prove interattive della v0.19.0 su questi punti restano valide per il codice invariato.

## Limiti

Coordinate assolute; nessuna conferma che un sito abbia accettato il click; nessun retry. Launcher non firmato; nessuna certificazione SentinelOne o Smart App Control; UAC/desktop sicuro e applicazioni con privilegi elevati non coperti.

SHA-256 del ZIP: nel file `SHA256SUMS-v1.0.0.txt` allegato alla release.
