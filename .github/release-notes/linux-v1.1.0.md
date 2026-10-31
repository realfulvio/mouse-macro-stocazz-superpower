## Mouse Macro Stocazz Superpower Linux v1.1.0

Release dedicata all'avvio con un doppio clic e alla precisione del replay. È una release separata (tag `linux-v*`): la release Windows più recente resta quella indicata come *Latest*.

### Novità e correzioni

- **Concedi accesso dal pannello**: se il programma non può leggere il mouse, i tasti F9/F10 o creare il mouse virtuale, in cima al pannello compare un avviso con il pulsante **Concedi accesso**. Apre la normale finestra di autorizzazione del desktop (`pkexec`), installa la regola udev `uaccess` e il mouse funziona subito, senza terminale e di solito senza uscire dalla sessione. Prima l'avviso era in fondo al pannello, fuori dalla parte visibile.
- **Scorciatoie globali riattivate da sole**: dopo aver concesso l'accesso (o premuto *Aggiorna elenco*) F9/F10/Ctrl+Alt+F11 ripartono senza riavviare il programma.
- **Replay più preciso**: il mouse virtuale ora viene creato prima di partire e il programma aspetta mezzo secondo che il desktop lo riconosca. Prima i primi movimenti del primo giro potevano andare persi e tutti i clic successivi finivano spostati. Anche l'ultimo rilascio del tasto non viene più perso alla chiusura.
- **Messaggi chiari se manca qualcosa**: se all'avvio manca una libreria di sistema (per esempio `libsecret`), invece di non succedere nulla compare un messaggio con il pacchetto da installare per Ubuntu/Debian, Fedora e Arch/CachyOS; i dettagli vanno in `~/.config/MouseMacroStocazzSuperpower/errore-avvio.log`. Se `/dev/uinput` non è accessibile, la riproduzione dice cosa fare invece di mostrare un errore tecnico.
- **AppImage nel menu**: dopo il primo doppio clic l'AppImage compare anche nel menu delle applicazioni con la sua icona, e la voce segue l'AppImage quando si aggiorna o la sposti.
- **Icona corretta nella barra delle applicazioni** per le installazioni da `install.sh`, AppImage e Flatpak.
- I pulsanti non disponibili (per esempio *Riproduci* senza una macro) ora appaiono attenuati.
- Il self-test (`--self-test report.json`) riporta anche lo stato dei permessi e le eventuali librerie mancanti.

### Avvio con doppio clic

1. Scarica `MouseMacroStocazzSuperpower-Linux-v1.1.0-x86_64.AppImage`.
2. Solo la prima volta: tasto destro → Proprietà → Permessi → *Eseguibile* (oppure `chmod +x`). I browser tolgono questo permesso ai file scaricati.
3. Doppio clic. Se compare **Concedi accesso**, premilo e inserisci la password.

Chi ha già la v1.0.0 la aggiorna dal pallino in alto.

### Altri formati

- **Da terminale**: `curl -fsSL https://raw.githubusercontent.com/realfulvio/mouse-macro-stocazz-superpower/main/install.sh | bash` (verifica lo SHA-256, installa in `~/.local/share/MouseMacroStocazzSuperpower`, aggiunge l'icona nel menu).
- **Flatpak** (`MouseMacroStocazzSuperpower-Linux-v1.1.0.flatpak`): dentro il sandbox *Concedi accesso* non è disponibile, i permessi si configurano una volta con `setup-linux-input.sh`.
- **tar.gz** con i binari IT/EN, `setup-linux-input.sh` e `build_info.json`.

### Limiti

- I movimenti su Linux sono relativi: riporta il cursore al punto di partenza prima di ogni replay e usa il profilo di accelerazione piatto per la massima precisione.
- I touchpad non sono supportati per la registrazione: serve un mouse.
- Il pulsante *Concedi accesso* richiede `pkexec` e un agente polkit (presenti su GNOME, KDE, XFCE, Cinnamon e simili) e un sistema con systemd-logind per il tag `uaccess`.
- Serve Linux x86_64; i binari sono compilati su Ubuntu 22.04 (glibc 2.35 o più recente).

Gli SHA-256 di tutti i file sono in `SHA256SUMS-linux-v1.1.0.txt`.
