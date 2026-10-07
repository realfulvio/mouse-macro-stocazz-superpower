# Collaudo v1.1.1 — 7 ottobre 2026

## Modifiche

- Cliccando sul numero delle ripetizioni, il pannello prende esplicitamente il focus della tastiera. Gli altri controlli mantengono il comportamento senza attivazione durante il replay.
- Ctrl+A consente di sostituire il numero. Il testo vuoto o fuori intervallo non viene sovrascritto dal valore precedente: la riproduzione viene rifiutata. Digitare 1000 non produce più il valore troncato 100.
- Il pannello mostra il modello del mouse comunicato da Windows. La ricerca usa SetupAPI e Configuration Manager, senza programmi esterni, rete o privilegi amministrativi. I dispositivi generici restano identificati con il nome del driver; in presenza di più dispositivi si mostra il primo modello e il numero degli altri. Il replay rimane globale.

## Pacchetto esatto

- ZIP: `MouseMacroStocazzSuperpower-Windows-v1.1.1.zip`, 12.114.231 byte.
- SHA-256: `5ca14c27da7ea61fb665edcfd81d94e8a6e321db012ff3700afc891620877065`.
- Alias Portable byte-identico; CRC e tutti i 113 hash del manifest verificati. Sorgenti inclusi identici al checkout.
- Runtime ufficiale Python 3.13.16 preservato byte per byte; firma PSF di pythonw.exe valida. Il launcher del progetto non è firmato.

## Risultati

169 test automatici eseguiti su Windows: **163 passati, 6 Linux saltati**. Dopo la restrizione della ricerca ai soli antenati USB/HID/Bluetooth, ripetuti e superati i 23 test mirati di pannello e dispositivi.

Il confronto nativo con la v1.1.0 ha riprodotto il difetto: cliccare sul campo non portava il pannello in primo piano e i tasti finivano nell'altra finestra. La correzione ha consentito la digitazione di 20, la sostituzione con Ctrl+A e la conservazione del campo vuoto durante la modifica. La lettura del campo da un altro processo è stata verificata tramite WM_GETTEXT, evitando il testo memorizzato restituito da GetWindowText.

Sull'esatto ZIP indicato sopra, **11 controlli nativi passati su ciascuno dei due sistemi**:

| Sistema | Prove | Risultato |
|---|---:|---|
| Windows 11 Pro, build 26200, DPI 100% | 11 | Passate |
| Windows Server 2022 Datacenter, build 20348, DPI 100% | 11 | Passate |

Le prove inviano clic e tasti nella sessione desktop interattiva e leggono i contatori di un bersaglio WinForms distinto dall'app. Su Server il banco è avviato come attività interattiva; SSH serve al trasferimento e alla lettura delle evidenze.

- Inserimento da tastiera di 0 e 1000: errore, nessun clic eseguito, testo originale conservato.
- Inserimento di 1, 3, 7 e 20: ricevuti rispettivamente **1, 3, 7 e 20 clic**, messaggio finale con il conteggio corrispondente e nessun pulsante del mouse premuto.
- 20 giri in Rapida 2×: **20 clic ricevuti**.
- Stop da pulsante, F10 e Ctrl+Alt+F11: esecuzione interrotta, contatore stabile e pulsanti rilasciati. Non sono misure della latenza di arresto.
- Registrazione di un clic reale e replay impostato a 3: **3 clic ricevuti**.

Rilevamento reale: SteelSeries Prime Wireless e un dispositivo HID generico su Windows 11; dispositivi VMware nella VM. Screenshot app-only autentici della v1.1.1 acquisiti su Windows 11 e controllati. Verificato anche il rendering offscreen a 100%, 125%, 150% e 200%: il rendering non sostituisce un collaudo su monitor fisici con quelle scale.

## Limiti

Non è una certificazione per tutti i PC, mouse o driver. Non sono stati ripetuti i collaudi completi di browser, cambi scheda, più monitor, DPI reali diversi dal 100%, avvio offline, Smart App Control e aggiornamento online dopo la pubblicazione. Motore di registrazione/replay e aggiornamento invariati, salvo la versione. Nessuna prova su account Howrse reali.

SentinelAgent era attivo durante il collaudo Windows 11; nel registro locale dell'intervallo non è emersa una nuova rilevazione attribuibile al pacchetto. Questo non certifica la policy EDR né risolve la [segnalazione SentinelOne #1](https://github.com/realfulvio/mouse-macro-stocazz-superpower/issues/1), che resta aperta. Nessuna protezione o esclusione antivirus modificata.

Attribuzione: hcok.
