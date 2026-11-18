## Mouse Macro Stocazz Superpower Linux v1.2.1

Aggiornamento Linux di sola manutenzione, dalla revisione completa del codice. È una release separata (tag `linux-v*`): la release Windows più recente resta quella indicata come *Latest*.

### Correzioni

- **CPU durante registrazione e riproduzione con macro lunghe**: il pannello rivalidava tutta la macro a ogni aggiornamento, quindi il consumo cresceva con la lunghezza (con 150 mila movimenti, circa 9 ms per controllo). Ora la risposta è in cache.
- Nessun'altra modifica a registrazione, riproduzione, tray, Impostazioni e mod rispetto alla [linux-v1.2.0](https://github.com/realfulvio/mouse-macro-stocazz-superpower/releases/tag/linux-v1.2.0).

### Avvio con doppio clic

1. Scarica `MouseMacroStocazzSuperpower-Linux-v1.2.1-x86_64.AppImage`.
2. Solo la prima volta: tasto destro → Proprietà → Permessi → *Eseguibile* (oppure `chmod +x`).
3. Doppio clic. Se compare **Concedi accesso**, premilo e inserisci la password.

Chi ha già la v1.2.0 (o una precedente) la aggiorna dal pallino in alto.

### Altri formati

- **Da terminale**: `curl -fsSL https://raw.githubusercontent.com/realfulvio/mouse-macro-stocazz-superpower/main/install.sh | bash`.
- **Flatpak** (`MouseMacroStocazzSuperpower-Linux-v1.2.1.flatpak`): dentro il sandbox *Concedi accesso* non è disponibile, i permessi si configurano una volta con `setup-linux-input.sh`.
- **tar.gz** con i binari IT/EN, `setup-linux-input.sh` e `build_info.json`.

### Limiti

- Tray e finestra Impostazioni non sono stati provati su GNOME né nel Flatpak. Su Wayland nascondere e mostrare il pannello dipende dal compositor.
- I movimenti su Linux sono relativi: riporta il cursore al punto di partenza prima di ogni replay.
- I touchpad non sono supportati per la registrazione: serve un mouse.

Gli SHA-256 di tutti i file sono in `SHA256SUMS-linux-v1.2.1.txt`.
