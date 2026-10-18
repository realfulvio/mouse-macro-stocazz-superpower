# Mouse Macro 1.1.1 — guida rapida

Progetto e design: **hcok**.

Estrai **tutto** lo ZIP in una cartella e apri `Mouse Macro v1.1.1.exe`.
Non occorre installare Python. Tieni insieme `runtime`, `app` ed eseguibile.

1. Prepara i programmi e le finestre da usare. Sposta il pannello fuori dai punti che userai.
2. Premi **F9** (o Registra). Esegui i gesti del mouse, anche passando fra programmi, desktop e schede, con le attese necessarie. Premi **F9** per terminare.
3. Apri **Opzioni** e scrivi il numero di **Ripetizioni**, da 1 a 999, oppure usa −/+ e **Preset 20**. Il numero comprende il primo giro. **Scheda successiva tra i giri** parte disattivata. Attivala se vuoi cambiare scheda: il programma invia **Ctrl+Tab una sola volta fra i giri**, senza chiudere schede e senza cambiare dopo l’ultimo. Se il toggle è spento, ripete la sequenza senza inviare Ctrl+Tab.
4. Scegli Normale o Rapida 2×. Ripristina lo stato iniziale delle finestre e premi **F10** (o Riproduci). Rapida accelera movimenti e pause operative fino a 2 secondi; le attese oltre 2 secondi restano a 1×. Pressione minima: 120 ms; pausa minima fra azioni: 650 ms in Normale, 325 ms in Rapida. I doppi click restano protetti. **Pagine lente** conserva il profilo prudente precedente (pausa minima 1,2 s e attese oltre 350 ms a 1×).
5. Premi **F10** o il pulsante **FERMA** per interrompere. **Ctrl+Alt+F11** è lo stop globale di emergenza, anche con altri programmi attivi.

Durante registrazione e riproduzione il pannello diventa una barra di 288 × 64 pixel alla scala 100%, appena trasparente, con stato, contatori e **Stop**. Parte al centro dell'area di lavoro del monitor e conserva gli spostamenti della barra finché l'app resta aperta. Puoi trascinarla da qualsiasi punto esterno a Stop durante la preparazione o la registrazione. F9 termina la registrazione, F10 ferma la riproduzione e Ctrl+Alt+F11 resta l'emergenza globale. Dopo l'arresto o un errore torna il pannello completo nella posizione precedente, conservando le opzioni.

I testi dei controlli usano Segoe UI; il logo conserva Outfit. Dimensioni e geometria seguono il DPI della finestra; la barra usa scritte da 11–16 pixel logici e il pannello opaco usa ClearType.

Gli eventi e la durata si aggiornano nella card di stato. Durante la registrazione e la riproduzione i controlli delle opzioni sono disabilitati. Nel pannello completo, per trascinare la finestra usa la fascia superiore; i tre comandi in alto riducono a icona, espandono/riducono le opzioni e chiudono. Per usare i controlli da tastiera attiva esplicitamente il pannello con Alt+Tab, quindi usa Tab/Shift+Tab e Spazio.

Il pannello rimane sopra le finestre normali e i pulsanti principali non sottraggono il focus al programma attivo. Non spostarlo durante una riproduzione. Prima del replay, se la barra copre un gesto registrato cerca una posizione libera vicina; se non la trova impedisce l'avvio. La trasparenza non lascia passare i click. **Opzioni** espande la finestra e mostra Salva macro, Carica macro, Preset 20 e Pagine lente. **Guida** ed **Emergenza** sono nel footer. Senza macro valida, Riproduci e Salva sono disabilitati.

Con il cambio scheda attivo imposta al massimo il numero di schede da lavorare: Ctrl+Tab torna alla prima quando raggiunge la fine. Ctrl+Tab viene inviato al programma attivo: abilita questa opzione solo se desideri questo comando.

La registrazione e il replay non sono limitati a Chrome/Firefox o a una singola finestra. Le finestre devono avere posizione, dimensione e scala compatibili con la registrazione. Non cambiare risoluzione, disposizione monitor, scala Windows o zoom del browser. Se cambi la disposizione, registra di nuovo.

Per pagine lente registra pause sufficienti e abilita **Pagine lente** nelle Opzioni. Non esiste un rilevamento garantito del caricamento: la pausa standard è prudente, non una conferma del sito. Il confronto dei pixel è stato rimosso dal flusso Windows perché non prova che un pulsante sia pronto. La macro non registra tasti della tastiera, non cerca i pulsanti per nome e non ritenta i clic automaticamente.

Dopo uno stop controlla lo stato dei programmi prima di riavviare: il programma ricomincia il giro. Il replay usa coordinate assolute, segue anche i cambi finestra e non controlla il programma destinatario. Prima dell’avvio controlla che ogni bersaglio sia nella posizione registrata; il pannello non deve coprire i gesti.

Salva/Carica conserva il formato JSON `.mmr`; sono leggibili le macro Windows precedenti con gesti completi. Non sovrascrivere i tuoi originali se vuoi conservarli. I file incompleti o invalidi vengono rifiutati e la macro già caricata resta disponibile.

Le macro precedenti restano leggibili, anche se contengono metadati del browser. Mantieni la scala usata nella registrazione.

I registri locali sono in `%LOCALAPPDATA%\MouseMacroStocazzSuperpower` (`ultimo-replay.json`, `errore.log`, `errore-avvio.log`). Il programma non salva titoli del browser, URL o credenziali.

Se Windows blocca l'exe, usa `Mouse Macro v1.1.1 (senza exe).cmd` incluso nello ZIP: avvia direttamente `runtime\pythonw.exe` con gli stessi file. Il launcher nuovo non è firmato; il runtime `pythonw.exe` conserva nome e firma PSF originali. Smart App Control, SentinelOne e policy aziendali **non sono certificati** da questa consegna; nessuna protezione Windows viene modificata. Il programma resta visibile sopra finestre normali, non sul desktop sicuro/UAC. Le prove locali non sostituiscono la verifica dei task su Howrse: nessun account reale è stato usato.

## Skin e aggiornamenti

- Il tondo con i puntini in alto apre il menu delle **skin** (Unicorno, Palio). La scelta viene ricordata.
- Il **pallino** accanto è verde se sei aggiornato, giallo se c'è una versione nuova, grigio se non si riesce a controllare. Cliccalo per controllare ora, installare l'ultima versione (con verifica SHA-256 e riavvio) o disattivare il controllo all'avvio.
- Il controllo è l'unica richiesta di rete del programma: legge in modo anonimo l'ultima release su GitHub. Non viene installato nulla senza un tuo clic. La verifica SHA-256 protegge da download corrotti; non sostituisce una firma digitale dell'editore.

## Movimento umano

Interruttore nelle Opzioni, **spento all'avvio**. Quando è acceso, a ogni giro il cursore segue una curva leggermente diversa tra un clic e l'altro, con velocità non uniforme (parte piano, accelera, rallenta), e le pause variano fino a circa un quarto di secondo. Le pressioni, i rilasci e la rotella restano nelle stesse coordinate della registrazione, e i trascinamenti non vengono modificati. Non è una garanzia contro i controlli dei siti: leggi i loro termini d'uso.

## Ripetizioni e modello del mouse

Apri le opzioni, clicca sul numero e usa Ctrl+A per sostituirlo. Sono ammessi da 1 a 999 giri. I valori vuoti o fuori intervallo impediscono la riproduzione: 1000 non viene trasformato in 100.

Il pannello mostra il modello comunicato dal driver del mouse. Se rileva più dispositivi, indica il primo modello e quanti altri sono presenti; il replay resta globale. I dispositivi senza un nome di prodotto possono comparire come HID o PS/2.

## Linux (release linux-v1.0.0)

La versione Linux si scarica dalla release [linux-v1.0.0](https://github.com/realfulvio/mouse-macro-stocazz-superpower/releases/tag/linux-v1.0.0) oppure con un comando nel terminale:

```bash
curl -fsSL https://raw.githubusercontent.com/realfulvio/mouse-macro-stocazz-superpower/main/install.sh | bash
```

Il comando verifica lo SHA-256, installa in `~/.local/share/MouseMacroStocazzSuperpower`, aggiunge l’icona nel menu e avvia il pannello. Nessun avvio automatico, nessun sudo.

In alternativa:
- **AppImage portable**: un solo file da scaricare dalla release. Rendilo eseguibile una volta (tasto destro → Proprietà → Permessi → Eseguibile) e poi aprilo con un doppio clic, come la versione portable di Windows. Si aggiorna da solo dal pallino.
- **Flatpak**: apri il file `.flatpak` della release con il gestore software. Gli aggiornamenti si fanno installando il nuovo `.flatpak`.

1. **Permessi, una volta sola.** Per leggere il mouse e i tasti F9/F10 serve l’accesso ai dispositivi di input. Lancia `bash ~/.local/share/MouseMacroStocazzSuperpower/current/setup-linux-input.sh` (chiede la password di sudo): installa una regola udev `uaccess` valida solo per chi usa la sessione locale attiva. Esci e rientra, poi premi **Aggiorna elenco**. Non avviare il programma come root.
2. **Il cursore riparte da dove si trova.** Su Linux la macro salva spostamenti relativi, non coordinate: prima di registrare e prima di ogni replay porta il cursore nello stesso punto di partenza. Non cambiare sensibilità, accelerazione del mouse o scala dello schermo; per la massima precisione scegli il profilo di accelerazione **piatto** nelle impostazioni del mouse.
3. **Registra e riproduci** come su Windows: F9 inizia e termina, F10 riproduce e ferma. Durante l’attività il pannello diventa una barra compatta, appena trasparente, con contatori e un grande **Stop**. Se fermi con il pulsante Stop, il clic su Stop non entra nella macro.
4. **Opzioni**: ripetizioni, Normale/Rapida 2×, Cambia scheda (Ctrl+Tab fra i giri), Pagine lente, **Movimento umano**, modalità (N volte, Infinito, Durata), doppio clic, skin e aggiornamenti. Il Movimento umano cambia la forma dei tragitti e le pause ma conserva la somma degli spostamenti fra due clic: i clic cadono negli stessi punti.
5. **Emergenza**: Ctrl+Alt+F11. Su molti desktop questa combinazione passa anche a una console di testo nera: la macro è comunque ferma, torna al desktop con Ctrl+Alt+F1, F2 o F7. **Ctrl+Maiusc+F11** ferma senza cambiare console.
6. **Aggiornamenti**: il pallino in alto è verde se sei aggiornato, giallo se c’è una versione Linux nuova, viola/grigio se non si riesce a controllare. Il controllo all’avvio si spegne dal dialogo Aggiornamenti.
7. **Se qualcosa va storto**: in `~/.config/MouseMacroStocazzSuperpower` trovi `ultimo-replay.json` (traccia dell’ultimo replay), `errore.log` e le preferenze (posizione e dimensione della finestra, skin, controllo aggiornamenti, mouse scelto).

Le macro Linux e Windows non sono intercambiabili: Windows salva coordinate assolute, Linux spostamenti relativi.

