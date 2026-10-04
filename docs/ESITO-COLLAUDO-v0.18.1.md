# Correzione Windows v0.18.1-beta

La v0.18.0 ereditava due blocchi precedenti: il pannello costruiva `WindowsRecorder(browser_only=True)` e la sessione richiedeva `WindowsPlayer.select_browser()` prima del replay. La registrazione rifiutava programmi diversi da Chrome/Firefox, barre del browser e cambi finestra. Il replay era vincolato al browser attivo.

La v0.18.1 usa la registrazione mouse globale e non lega il replay a un browser o a una sola finestra. Sono ammessi programmi, desktop, barre e cambi finestra effettuati con il mouse. I metadati browser nelle macro precedenti non impongono più quel vincolo. Rimossa anche la condizione che rifiutava una macro senza metadati browser quando il pannello era a DPI maggiori di 96. Il layout non cambia.

Restano: esclusione dei gesti sul pannello, controllo dello schermo e dei bersagli coperti dal pannello prima dell’avvio, validazione dei gesti, rilascio dei pulsanti, F10 e Ctrl+Alt+F11. Il motore e i parametri temporali della v0.18 sono invariati; cambio scheda OFF all’avvio e Ctrl+Tab solo fra i giri se attivato.

Test automatici:

- `win-test`, Windows/Python 3.13.16: mirati **61/61**; suite completa **112 superati, 6 saltati** (118 totali).
- CachyOS `dev`, ambiente del progetto esistente: suite completa **67 superati, 51 saltati** (118 totali).
- Due regressioni aggiunte: eventi fuori dai browser accettati mantenendo l’esclusione del pannello; replay di macro con vecchi metadati browser senza selezionare un browser.
- Build nativa Windows con .NET Framework `csc.exe`; 105 hash del manifest, sorgenti, guida e runtime verificati.

Prova interattiva del pacchetto esatto su Windows 11 LTSC, VM locale predisposta per il collaudo precedente, 1280×800 / 96 DPI:

- Registrazione F9 fra **due finestre native Tk e il desktop**, senza browser.
- Ricevuti nelle finestre: 6 pressioni e 6 rilasci, un doppio click, un evento wheel e un trascinamento. Replay 1× e 2× con gli stessi conteggi, nessun click perso e nessun pulsante lasciato premuto.
- Durata esterna del banco: **6,841 s a 1×; 3,855 s a 2×**.

Il banco nasconde le proprie console per liberare i bersagli e verifica che il punto sul desktop appartenga a Progman/WorkerW. Il bersaglio Tk conta solo rilasci con una pressione corrispondente; Windows/Tk può consegnargli rilasci isolati di click sul desktop o sul pannello. Le prime prove del banco con console sovrapposte sono conservate nei log locali e non contate come collaudi superati.

Regressioni browser: **14 verifiche superate** sullo stesso ZIP (18 totali con il banco globale). Registrazione/caricamento, replay 1×/2× senza click persi, click/doppio click, drag/wheel, pausa di caricamento lunga, Preset 20, cambio scheda OFF/ON e nessun Ctrl+Tab dopo l’ultimo giro. F10: **10,55 ms**; Ctrl+Alt+F11 durante una pressione: **11,29 ms**, con rilascio del mouse. Le disconnessioni HTTP durante la chiusura di Chrome sono messaggi del server del banco; tutti gli assert e il processo di collaudo sono terminati con esito positivo.

Pacchetto: `MouseMacroStocazzSuperpower-Windows-v0.18.1-beta.zip` — 11.876.142 byte.
SHA-256: `14d4d9a7a167034a3d00cc1ec8ec359a4cb674d1768229416cb53c15cd799143`.

Il replay usa coordinate assolute: occorre mantenere finestre e bersagli nella posizione registrata. I cambi di focus non fermano più automaticamente una macro globale. Il programma registra solo il mouse; UAC/desktop sicuro e applicazioni elevate non sono coperti da questo collaudo. Nessuna nuova certificazione per antivirus, Howrse reale o DPI diversi dal 100%.
