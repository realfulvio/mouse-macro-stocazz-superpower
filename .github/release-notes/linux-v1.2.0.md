## Mouse Macro Stocazz Superpower Linux v1.2.0

Release unica con la versione Windows [v1.2.0](https://github.com/realfulvio/mouse-macro-stocazz-superpower/releases/tag/v1.2.0): stesse novità, adattate a Linux. È una release separata (tag `linux-v*`): la release Windows più recente resta quella indicata come *Latest*.

### Novità

- **Skin Bambola, predefinita**: cavalla animata nella scheda di stato e barra compatta di 300×72 pixel in registrazione e riproduzione. Unicorno e Palio restano disponibili.
- **Icona nell'area di notifica (tray)**: Mostra/Nascondi, Registra, Riproduci, Ferma tutto, Impostazioni e mod, *Chiudi nel tray* (spento di default), Esci. Funziona dove esiste uno StatusNotifierWatcher: KDE Plasma, e GNOME con l'estensione AppIndicator. In modalità gioco di Steam (gamescope) e senza watcher l'icona non compare e il pannello funziona come prima.
- **Impostazioni e mod (`.mmmod`)**: pacchetti di soli dati con un tema o una raccolta di macro, con riepilogo e SHA-256 prima dell'installazione. Le macro di una raccolta si caricano da *Carica*, nella cartella dei mod.
- **Tastiera facoltativa**: interruttore *Registra anche la tastiera*, **spento a ogni avvio**. I tasti finiscono nel file in chiaro, password comprese. F9, F10 e F11 non vengono mai registrati. Se la tastiera non è leggibile, la registrazione si ferma e rimanda a *Concedi accesso* (la regola udev già includeva le tastiere).
- **Macro avviabile (.sh)**: dalle Opzioni si salva `nome.sh` (eseguibile) più `nome.mmr`. Lo script apre il programma con la macro **già caricata, ma non avviata**: si parte con F10. Con l'AppImage: `./MouseMacroStocazzSuperpower-Linux-v1.2.0-x86_64.AppImage --open nome.mmr`.
- Nuova dipendenza di sistema: nessuna. La libreria `jeepney` (D-Bus, puro Python) è dentro i binari, quindi anche nell'AppImage e nel Flatpak. Il Flatpak ottiene il permesso `--talk-name=org.kde.StatusNotifierWatcher` per il tray.

### Avvio con doppio clic

1. Scarica `MouseMacroStocazzSuperpower-Linux-v1.2.0-x86_64.AppImage`.
2. Solo la prima volta: tasto destro → Proprietà → Permessi → *Eseguibile* (oppure `chmod +x`).
3. Doppio clic. Se compare **Concedi accesso**, premilo e inserisci la password.

Chi ha già la v1.0.0, v1.1.0 o v1.1.1 la aggiorna dal pallino in alto.

### Altri formati

- **Da terminale**: `curl -fsSL https://raw.githubusercontent.com/realfulvio/mouse-macro-stocazz-superpower/main/install.sh | bash`.
- **Flatpak** (`MouseMacroStocazzSuperpower-Linux-v1.2.0.flatpak`): dentro il sandbox *Concedi accesso* non è disponibile, i permessi si configurano una volta con `setup-linux-input.sh`.
- **tar.gz** con i binari IT/EN, `setup-linux-input.sh` e `build_info.json`.

### Limiti

- Correzione: al primo avvio senza la cartella `~/.flet` il download della finestra Flet falliva su alcune distribuzioni per i certificati; ora viene usato il bundle di sistema (o quello incluso).
- Tray e finestra Impostazioni non sono stati provati su GNOME né nel Flatpak. Su Wayland nascondere e mostrare il pannello dipende dal compositor.
- I movimenti su Linux sono relativi: riporta il cursore al punto di partenza prima di ogni replay.
- I touchpad non sono supportati per la registrazione: serve un mouse.

Gli SHA-256 di tutti i file sono in `SHA256SUMS-linux-v1.2.0.txt`.
