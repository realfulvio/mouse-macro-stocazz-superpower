## Mouse Macro Stocazz Superpower Linux v1.0.0

Prima release della nuova versione Linux, al pari della Windows v1.1.1. È una release separata (tag `linux-v*`): la release Windows più recente resta [v1.1.1](https://github.com/realfulvio/mouse-macro-stocazz-superpower/releases/tag/v1.1.1) e l'aggiornamento automatico di Windows non viene toccato.

### Novità

- **Pannello Linux** leggibile, in italiano o inglese, per X11 e Wayland: Registra/Riproduci grandi, ripetizioni 1–999 sempre visibili, Salva/Carica `.mmr`, Opzioni ed Emergenza nel footer.
- **Barra attiva compatta**: durante registrazione e riproduzione il pannello diventa una barra appena trasparente con il cavallo della skin, i contatori (eventi e tempo, oppure giri e tempo) e un grande **Stop**.
- **Movimento umano** (Opzioni, spento all'avvio): a ogni giro cambiano la forma dei tragitti e le pause. Con i movimenti relativi di Linux la somma degli spostamenti fra un clic e l'altro resta identica, quindi i clic cadono negli stessi punti; la velocità lungo il tragitto non cambia, per non risentire dell'accelerazione del mouse.
- **Pallino aggiornamenti** come su Windows: verde se aggiornato, giallo se c'è una versione nuova. Controlla all'avvio solo le release `linux-v*` (disattivabile), scarica il pacchetto, verifica lo SHA-256 e riavvia la nuova versione.
- **Modello del mouse** visibile nel pannello, anche quando mancano ancora i permessi.
- **Preferenze ricordate**: posizione e dimensione della finestra, skin, mouse scelto, controllo aggiornamenti.
- **Diagnostica** in `~/.config/MouseMacroStocazzSuperpower`: `ultimo-replay.json` con la traccia dell'ultimo replay ed `errore.log`.
- **Emergenza**: Ctrl+Alt+F11 come su Windows, più **Ctrl+Maiusc+F11**, che non fa passare il desktop a una console di testo.

### Installazione

```bash
curl -fsSL https://raw.githubusercontent.com/realfulvio/mouse-macro-stocazz-superpower/main/install.sh | bash
```

Lo script (allegato anche qui come `install.sh`) scarica `MouseMacroStocazzSuperpower-Linux-v1.0.0.tar.gz`, ne verifica lo SHA-256 con `SHA256SUMS-linux-v1.0.0.txt`, installa in `~/.local/share/MouseMacroStocazzSuperpower`, aggiunge l'icona nel menu e avvia il programma. Niente sudo e niente avvii automatici. Opzioni: `--en`, `--permessi`, `--no-start`.

A mano: scarica il tar.gz e il file SHA256SUMS, controlla con `sha256sum -c --ignore-missing SHA256SUMS-linux-v1.0.0.txt`, estrai e apri `MouseMacroStocazzSuperpower-Linux-IT` (o `-EN`).

### Versione portable e Flatpak

- **AppImage** (`MouseMacroStocazzSuperpower-Linux-v1.0.0-x86_64.AppImage`): un unico file, come lo ZIP portable di Windows. Rendilo eseguibile una volta (tasto destro → Proprietà → Permessi → Eseguibile, oppure `chmod +x`) e aprilo con un doppio clic. Si aggiorna da solo dal pallino, con verifica SHA-256.
- **Flatpak** (`MouseMacroStocazzSuperpower-Linux-v1.0.0.flatpak`): aprilo con il gestore software oppure `flatpak install --user MouseMacroStocazzSuperpower-Linux-v1.0.0.flatpak`. Usa il runtime GNOME 51 di Flathub. Gli aggiornamenti si fanno installando il nuovo `.flatpak`; la pubblicazione su Flathub è in preparazione (ricetta in `flatpak/`).

### Permessi e limiti

- **Permessi, una volta sola**: `bash ~/.local/share/MouseMacroStocazzSuperpower/current/setup-linux-input.sh` installa una regola udev `uaccess` (chiede la password di sudo), valida solo per l'utente della sessione locale attiva. Poi esci e rientra. Non avviare il programma come root.
- **Movimenti relativi**: su Wayland non si può leggere o impostare la posizione del cursore, quindi il replay parte da dove si trova il puntatore. Riporta il cursore al punto di partenza prima di ogni replay e mantieni sensibilità, accelerazione e scala; per la massima precisione usa il profilo di accelerazione piatto.
- Su Wayland la posizione della finestra e il "sempre in primo piano" dipendono dal compositor.
- Serve Linux x86_64; i binari sono compilati su Ubuntu 22.04 (glibc 2.35 o più recente).

Esito dei controlli e limiti: [PR #3](https://github.com/realfulvio/mouse-macro-stocazz-superpower/pull/3). Gli SHA-256 di tutti i file sono in `SHA256SUMS-linux-v1.0.0.txt`.
