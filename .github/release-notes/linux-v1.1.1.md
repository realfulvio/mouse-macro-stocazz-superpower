## Mouse Macro Stocazz Superpower Linux v1.1.1

Due correzioni trovate collaudando la v1.1.0 su un mini PC CachyOS. È una release separata (tag `linux-v*`): la release Windows più recente resta quella indicata come *Latest*.

### Correzioni

- **Concedi accesso nella modalità gioco di Steam**: in gamescope (Steam Game Mode) non c'è la finestra per la password, quindi premendo *Concedi accesso* non compariva niente e il pannello diceva "Configurazione annullata". Ora spiega di passare al Desktop e premere di nuovo il pulsante.
- **Avvio senza sessione grafica**: lanciato senza `DISPLAY` né `WAYLAND_DISPLAY` (per esempio da SSH), il programma provava a passare in modalità web e si chiudeva con un errore tecnico. Ora esce subito spiegando che serve la sessione grafica, e lo scrive anche in `~/.config/MouseMacroStocazzSuperpower/errore-avvio.log`.

Il resto è identico alla [v1.1.0](https://github.com/realfulvio/mouse-macro-stocazz-superpower/releases/tag/linux-v1.1.0).

### Avvio con doppio clic

1. Scarica `MouseMacroStocazzSuperpower-Linux-v1.1.1-x86_64.AppImage`.
2. Solo la prima volta: tasto destro → Proprietà → Permessi → *Eseguibile* (oppure `chmod +x`).
3. Doppio clic. Se compare **Concedi accesso**, premilo e inserisci la password.

Chi ha già la v1.0.0 o la v1.1.0 la aggiorna dal pallino in alto.

### Altri formati

- **Da terminale**: `curl -fsSL https://raw.githubusercontent.com/realfulvio/mouse-macro-stocazz-superpower/main/install.sh | bash`.
- **Flatpak** (`MouseMacroStocazzSuperpower-Linux-v1.1.1.flatpak`): dentro il sandbox *Concedi accesso* non è disponibile, i permessi si configurano una volta con `setup-linux-input.sh`.
- **tar.gz** con i binari IT/EN, `setup-linux-input.sh` e `build_info.json`.

Gli SHA-256 di tutti i file sono in `SHA256SUMS-linux-v1.1.1.txt`.
