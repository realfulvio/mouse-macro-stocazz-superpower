# Mouse Macro 0.18 — guida rapida

Progetto e design: **hcok**.

Estrai **tutto** lo ZIP in una cartella e apri `Mouse Macro v0.18.0-beta.exe`.
Non occorre installare Python. Tieni insieme `runtime`, `app` ed eseguibile.

1. Apri le schede dei cavalli nella stessa finestra di Chrome o Firefox, nell’ordine di lavoro. Attiva la prima. Sposta il pannello fuori dai punti che userai.
2. Premi **F9** (o Registra). Esegui i task di **un solo cavallo**, con le attese necessarie. Non cambiare scheda mentre registri. Premi **F9** per terminare.
3. Apri **Opzioni** e scegli **Ripetizioni** con −/+ oppure **Preset 20**. Il numero comprende la prima scheda. **Scheda successiva tra i giri** parte disattivata. Attivala se vuoi cambiare scheda: il programma invia **Ctrl+Tab una sola volta fra i giri**, senza chiudere schede e senza cambiare dopo l’ultimo. Se il toggle è spento, ripete nella stessa scheda.
4. Scegli Normale o Rapida 2×. Attiva la prima scheda da lavorare e premi **F10** (o Riproduci). Rapida accelera movimenti e pause operative fino a 2 secondi; le attese oltre 2 secondi restano a 1×. Pressione minima: 120 ms; pausa minima fra azioni: 650 ms in Normale, 325 ms in Rapida. I doppi click restano protetti. **Pagine lente** conserva il profilo prudente precedente (pausa minima 1,2 s e attese oltre 350 ms a 1×).
5. Premi **F10** o il pulsante **FERMA** per interrompere. **Ctrl+Alt+F11** è lo stop globale di emergenza, anche con Chrome o Firefox attivi.

Gli eventi e la durata si aggiornano nella card di stato. Durante la registrazione e la riproduzione i controlli delle opzioni sono disabilitati. Per trascinare la finestra usa la fascia superiore; i tre comandi in alto riducono a icona, espandono/riducono le opzioni e chiudono. Per usare i controlli da tastiera attiva esplicitamente il pannello con Alt+Tab, quindi usa Tab/Shift+Tab e Spazio.

Il pannello rimane sopra le finestre normali e i pulsanti principali non sottraggono il focus al browser. Non spostarlo durante una riproduzione. Se copre un gesto il programma impedisce l’avvio. **Opzioni** espande la finestra e mostra Salva macro, Carica macro, Preset 20 e Pagine lente. **Guida** ed **Emergenza** sono nel footer. Senza macro valida, Riproduci e Salva sono disabilitati.

Con il cambio scheda attivo imposta al massimo il numero di schede da lavorare: Ctrl+Tab torna alla prima quando raggiunge la fine. Il programma non conosce il numero dei cavalli né riconosce schede già completate.

Per più finestre: completa una finestra per volta; attiva quella successiva e avvia da lì. Le finestre devono avere posizione, dimensione e scala compatibili con la registrazione. Non cambiare risoluzione, disposizione monitor, scala Windows o zoom del browser. Se cambi la disposizione, registra di nuovo.

Per pagine lente registra pause sufficienti e abilita **Pagine lente** nelle Opzioni. Non esiste un rilevamento garantito del caricamento: la pausa standard è prudente, non una conferma del sito. Il confronto dei pixel è stato rimosso dal flusso Windows perché non prova che un pulsante sia pronto. La macro non registra tasti della tastiera, non cerca i pulsanti per nome e non ritenta i clic automaticamente.

Dopo uno stop controlla lo stato della pagina prima di riavviare: il programma ricomincia il giro, non deduce quali task siano già stati completati. Se il browser perde il primo piano, il pannello copre un bersaglio o la finestra cambia dimensione, la macro si ferma.

Salva/Carica conserva il formato JSON `.mmr`; sono leggibili le macro Windows precedenti con gesti completi. Non sovrascrivere i tuoi originali se vuoi conservarli. I file incompleti o invalidi vengono rifiutati e la macro già caricata resta disponibile.

Le macro precedenti prive di informazioni sulla scala sono ammesse soltanto al 100%; a scale superiori registra di nuovo.

I registri locali sono in `%LOCALAPPDATA%\MouseMacroStocazzSuperpower` (`ultimo-replay.json`, `errore.log`, `errore-avvio.log`). Il programma non salva titoli del browser, URL o credenziali.

Il launcher nuovo non è firmato; il runtime `pythonw.exe` conserva nome e firma PSF originali. Smart App Control, SentinelOne e policy aziendali **non sono certificati** da questa consegna; nessuna protezione Windows viene modificata. Il programma resta visibile sopra finestre normali, non sul desktop sicuro/UAC. Le prove locali non sostituiscono la verifica dei task su Howrse: nessun account reale è stato usato.
