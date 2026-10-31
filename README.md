<p align="center"><b>Italiano</b> · <a href="README.en.md">English</a></p>

<h1 align="center">Mouse Macro Stocazz Superpower</h1>

<p align="center">
Registra il mouse e ripeti la sequenza quante volte vuoi.<br>
Un piccolo pannello sempre in primo piano per Windows e Linux: niente installer, niente Python da installare.
</p>

<p align="center">
<a href="https://github.com/realfulvio/mouse-macro-stocazz-superpower/releases/tag/v1.1.3"><b>⬇ Scarica per Windows</b></a>
· <a href="https://github.com/realfulvio/mouse-macro-stocazz-superpower/releases/tag/linux-v1.1.1"><b>⬇ Scarica per Linux</b></a>
· <a href="GUIDA-ITALIANA.md">Guida italiana</a>
· <a href="docs/ESITO-COLLAUDO-v1.1.1.md">Esito dei controlli</a>
</p>

<p align="center">
<img src="docs/screenshots/v111-windows11-compact.png" alt="Windows 11" width="230">
&nbsp;
<img src="docs/screenshots/v111-windows11-expanded.png" alt="Windows 11" width="440">
</p>

## Avvio rapido da PowerShell

Avvia il programma tramite il runtime Python ufficiale firmato. Niente ZIP da scaricare e niente exe.

**1.** Apri PowerShell (tasto Windows, scrivi `PowerShell`, Invio).

**2.** Incolla questo comando e premi Invio:

```powershell
irm https://raw.githubusercontent.com/realfulvio/mouse-macro-stocazz-superpower/main/install.ps1 | iex
```

<p align="center"><img src="docs/screenshots/guida-powershell.png" alt="Il comando in PowerShell: scarica Mouse Macro e lo avvia" width="720"></p>

**3.** Il pannello si apre. Le volte successive basta lo stesso comando: non riscarica nulla e riavvia solo l'app.

Lo script scarica la release ufficiale da GitHub, ne verifica lo SHA-256, la estrae in `%LOCALAPPDATA%\MouseMacroStocazzSuperpower\Portable` e avvia il programma con il `pythonw.exe` ufficiale di Python, firmato dalla Python Software Foundation. Un file scaricato da PowerShell non ha il Mark of the Web. Puoi leggere [install.ps1](install.ps1) prima di eseguirlo. Nessuna protezione di Windows viene disattivata.

## Altri modi di installare

1. Scarica `MouseMacroStocazzSuperpower-Windows-v1.1.3.zip` dalla [release](https://github.com/realfulvio/mouse-macro-stocazz-superpower/releases/tag/v1.1.3).
2. Estrai **tutto** lo ZIP in una cartella.
3. Apri `Mouse Macro v1.1.3.exe` e rispondi **Sì**: lo installa nella tua cartella utente (senza permessi da amministratore) e crea i collegamenti nel menu Start e sul desktop; si disinstalla da *Impostazioni → App installate*. Con **No** lo avvia dallo ZIP senza installare. Se Windows blocca l'exe, apri invece `Mouse Macro v1.1.3 (senza exe).cmd`.

Serve Windows x64; l'exe richiede anche .NET Framework 4 (già presente in Windows 10/11), il `.cmd` no. Python è incluso. L'interfaccia è in italiano. Lo SHA-256 dello ZIP è pubblicato con ogni release.

### Windows blocca l'exe?

Il launcher `.exe` non è firmato: SmartScreen o il *Controllo intelligente delle app* (Smart App Control) di Windows 11 possono bloccarlo (*"Un criterio di controllo dell'applicazione ha bloccato il file"*). Le due vie senza exe, cioè il comando PowerShell qui sopra e il file **`Mouse Macro v1.1.3 (senza exe).cmd`** nello ZIP, sono state provate con Smart App Control nella v1.1.0 (Windows 11 build 26300, [rapporto precedente](docs/ESITO-COLLAUDO-v1.1.0.md)); la verifica SAC non è stata ripetuta per le v1.1.1, v1.1.2 e v1.1.3. Il `.cmd` avvia direttamente il `pythonw.exe` firmato PSF con gli stessi file. Se SmartScreen avvisa, usa *Ulteriori informazioni → Esegui comunque*; se blocca ancora, tasto destro sullo ZIP → *Proprietà* → **Sblocca** prima di estrarlo.

Se anche queste vie vengono bloccate sul tuo PC, scrivilo nelle [Issues](https://github.com/realfulvio/mouse-macro-stocazz-superpower/issues).

La v1.1.3 si installa con un doppio clic sull'exe (menu Start, desktop, *App installate*) e all'avvio controlla gli aggiornamenti; motore invariato rispetto alla v1.1.2. [Download Portable](https://github.com/realfulvio/mouse-macro-stocazz-superpower/releases/download/v1.1.3/MouseMacroStocazzSuperpower-Windows-Portable.zip).

## Cosa fa

- Registra movimenti, click, doppi click, trascinamenti e rotella, in qualsiasi programma, sul desktop e sulle barre del browser.
- Riproduce la sequenza da 1 a 999 volte, a velocità normale o **2× più veloce**.
- Durante registrazione e replay il pannello diventa una piccola barra semitrasparente con contatori e pulsante **Stop**, per non dare fastidio.
- Salva e carica le macro in file `.mmr`.
- **Ctrl+Tab tra un giro e l'altro** (facoltativo) per scorrere le schede del browser: spento all'avvio, mai dopo l'ultimo giro.
- **Movimento umano** (facoltativo, spento all'avvio): a ogni giro il cursore segue una curva leggermente diversa, con velocità non uniforme, e le pause variano un poco. I clic cadono sempre negli stessi punti registrati; i trascinamenti e la rotella non cambiano. Non rende invisibile l'automazione: molti siti la vietano nei loro termini.
- Registra solo il mouse: niente tastiera, niente schermate. L'unico accesso alla rete è il controllo aggiornamenti, anonimo e disattivabile.


## Skin e aggiornamenti

<p align="center">
<img src="docs/screenshots/v110-unicorno-compatto.png" alt="Skin Unicorno" width="250">
&nbsp;
<img src="docs/screenshots/v110-palio-compatto.png" alt="Skin Palio" width="250">
&nbsp;
<img src="docs/screenshots/v110-palio-esteso.png" alt="Skin Palio con le opzioni aperte" width="420">
</p>

- **Skin**: il tondo con i puntini in alto, accanto ai pulsanti della finestra, apre il menu delle skin: *Unicorno* (viola scuro, predefinita) e *Palio* (chiara, un sauro con i nastri di contrada). La scelta viene ricordata. Durante registrazione e riproduzione il pannello torna alla barra compatta, con il cavallo della skin scelta.
- **Aggiornamenti**: il pallino accanto al tondo è **verde** se hai l'ultima versione, **giallo** se ne è uscita una nuova, **grigio** se non si riesce a controllare. Cliccandolo puoi controllare subito, scaricare e installare l'ultima versione (verifica lo SHA-256 e poi riavvia) oppure disattivare il controllo all'avvio.
- **Rete**: l'unica richiesta di rete del programma è la lettura anonima dell'ultima release su GitHub. Non viene scaricato né installato nulla senza un tuo clic, e il controllo si può spegnere dal menu del pallino.

## Uso

| Passo | Azione |
|---|---|
| 1 | Sistema le finestre che userai e sposta il pannello lontano dai punti da cliccare |
| 2 | **F9**, esegui la sequenza con il mouse, **F9** di nuovo |
| 3 | Apri **Opzioni**, scrivi le ripetizioni (1–999) o usa **−/+** / **Preset 20**; scegli **Normale** o **Rapida 2×** |
| 4 | Ripristina lo stato iniziale e premi **F10** per riprodurre |
| – | **F10** o **Stop** fermano il replay · **Ctrl+Alt+F11** è l'arresto di emergenza globale |

<p align="center"><img src="docs/screenshots/v100-expanded.png" alt="Opzioni espanse" width="560"></p>

**Rapida 2×** accelera movimenti e pause normali; le attese oltre 2 s restano a 1× e pressioni e doppi click restano protetti, quindi la durata totale non si dimezza esattamente. **Pagine lente** aggiunge pause più lunghe e prudenti per le pagine web lente.

## Da sapere

- Il replay usa **coordinate assolute dello schermo**: mantieni posizione delle finestre, risoluzione, disposizione dei monitor e scala di Windows uguali a quelle della registrazione.
- Il pannello non deve coprire un click registrato: l'app sposta la barra in un punto libero oppure non parte.
- Il programma non sa se un sito ha accettato il click e non riprova mai.
- Non coperti: UAC / desktop sicuro e applicazioni con privilegi elevati.
- Non certificato con SentinelOne. Le precedenti prove Smart App Control sono documentate nel rapporto v1.1.0 e non sono state ripetute per questo aggiornamento. Nessuna protezione viene modificata.

## Stato

Stabile. La v1.1.1 corregge l'inserimento delle ripetizioni e aggiunge il modello del mouse. Sull'esatto ZIP sono passati 11 controlli nativi sia su Windows 11 sia su Windows Server 2022: conteggi effettivi 1/3/7/20, Rapida 2×, registrazione/replay, Stop/F10/emergenza e valori invalidi. Suite automatica: 163 passati, 6 Linux saltati. Il motore è invariato. [Rapporto e limiti](docs/ESITO-COLLAUDO-v1.1.1.md).

## Linux

<p align="center">
<img src="docs/screenshots/linux-v100-pannello.png" alt="Pannello Linux" width="250">
&nbsp;
<img src="docs/screenshots/linux-v100-barra.png" alt="Barra attiva durante la riproduzione" width="330">
</p>

La versione Linux ha una release separata, **[linux-v1.1.1](https://github.com/realfulvio/mouse-macro-stocazz-superpower/releases/tag/linux-v1.1.1)**, con le stesse funzioni della Windows: barra attiva compatta e semitrasparente con contatori e Stop, ripetizioni 1–999, Normale/Rapida 2×, Ctrl+Tab tra i giri, Pagine lente, **Movimento umano**, skin Unicorno/Palio, modello del mouse, pallino aggiornamenti con installazione verificata, preferenze e diagnostica. Interfaccia in italiano o inglese; serve Linux x86_64 con X11 o Wayland.

**Doppio clic (consigliato).** Scarica [`MouseMacroStocazzSuperpower-Linux-v1.1.1-x86_64.AppImage`](https://github.com/realfulvio/mouse-macro-stocazz-superpower/releases/download/linux-v1.1.1/MouseMacroStocazzSuperpower-Linux-v1.1.1-x86_64.AppImage): è un unico file che contiene tutto, come lo ZIP portable di Windows.
1. La prima volta rendilo eseguibile: tasto destro → Proprietà → Permessi → *Eseguibile* (oppure `chmod +x` sul file). I browser tolgono questo permesso a ogni file scaricato, quindi serve una volta sola.
2. Doppio clic. Parte in italiano se il sistema è in italiano, altrimenti in inglese, e da quel momento compare anche nel menu delle applicazioni con la sua icona.
3. Se in alto compare **Concedi accesso**, premilo: il sistema chiede la password (la normale finestra di autorizzazione del desktop, niente terminale) e il mouse e i tasti F9/F10 funzionano subito. Nella modalità gioco di Steam (gamescope) la finestra della password non c'è: passa al Desktop e premilo lì.

Dal pallino aggiornamenti l'AppImage si aggiorna da sola: scarica la nuova AppImage accanto a quella vecchia, ne verifica lo SHA-256 e la sostituisce. Se manca una libreria di sistema (per esempio `libsecret`), al doppio clic compare un messaggio con il pacchetto da installare invece di non succedere nulla.

**Installazione da terminale** (non usa sudo, non crea avvii automatici):

```bash
curl -fsSL https://raw.githubusercontent.com/realfulvio/mouse-macro-stocazz-superpower/main/install.sh | bash
```

Lo script cerca l'ultima release `linux-v*`, scarica il pacchetto, ne verifica lo SHA-256, lo estrae in `~/.local/share/MouseMacroStocazzSuperpower`, aggiunge l'icona nel menu delle applicazioni e avvia il programma. Le volte successive avvia la versione installata senza riscaricare. Opzioni: `--en` (inglese), `--permessi` (configura subito i permessi), `--no-start`. In alternativa scarica `MouseMacroStocazzSuperpower-Linux-v1.1.1.tar.gz` e `SHA256SUMS-linux-v1.1.1.txt`, controlla con `sha256sum -c --ignore-missing SHA256SUMS-linux-v1.1.1.txt`, estrai e apri `MouseMacroStocazzSuperpower-Linux-IT`.

**Flatpak.** Scarica [`MouseMacroStocazzSuperpower-Linux-v1.1.1.flatpak`](https://github.com/realfulvio/mouse-macro-stocazz-superpower/releases/download/linux-v1.1.1/MouseMacroStocazzSuperpower-Linux-v1.1.1.flatpak) e aprilo con il gestore software, oppure `flatpak install --user MouseMacroStocazzSuperpower-Linux-v1.1.1.flatpak`. Usa il runtime GNOME 51 di Flathub, che viene scaricato in automatico. Nel Flatpak l'app non si aggiorna da sola: per una nuova versione installa il nuovo `.flatpak`. Il sandbox concede l'accesso ai dispositivi (`--device=all`, necessario per leggere il mouse e usare uinput), la rete solo per il controllo aggiornamenti e la cartella home per Salva/Carica. Dentro il Flatpak il pulsante *Concedi accesso* non è disponibile: i permessi si configurano una volta con lo script qui sotto.

**Permessi.** Su Linux il programma legge il mouse e i tasti F9/F10 direttamente dai dispositivi (`/dev/input/event*`) e riproduce con un mouse virtuale (`/dev/uinput`). Il pulsante **Concedi accesso** del pannello installa, con la finestra di autorizzazione del sistema (`pkexec`), una regola udev con `TAG+="uaccess"` per mouse, tastiere e uinput. In alternativa, da terminale: `bash ~/.local/share/MouseMacroStocazzSuperpower/current/setup-linux-input.sh` (oppure lo script [`scripts/setup-linux-input.sh`](scripts/setup-linux-input.sh)), poi esci e rientra. L'accesso vale solo per l'utente seduto alla sessione locale attiva e viene tolto quando cambia utente o sessione; finché la regola è attiva, anche altri programmi della tua sessione possono leggere quei dispositivi. Non avviare l'app come root. Senza permessi il pannello mostra comunque il modello del mouse con la nota *senza permessi*. I touchpad non sono supportati per la registrazione: usa un mouse.

**Limite dei movimenti relativi.** Su Wayland nessun programma può leggere o impostare la posizione del cursore: la macro Linux registra gli spostamenti relativi e il replay parte dalla posizione attuale del puntatore. Prima di ogni replay riporta il cursore nel punto di partenza, e non cambiare sensibilità, accelerazione del mouse o scala dello schermo. Con l'accelerazione attiva lo stesso spostamento può arrivare in un punto leggermente diverso se il ritmo cambia: per risultati ripetibili usa il profilo di accelerazione **piatto** (Impostazioni di sistema → Mouse). Il **Movimento umano** cambia la forma dei tragitti e le pause, ma mantiene identica la somma degli spostamenti fra un clic e l'altro e non tocca la velocità lungo il tragitto, così i clic cadono negli stessi punti.

**Scorciatoie.** F9 registra/ferma, F10 riproduce/ferma, Ctrl+Alt+F11 è l'emergenza. Su molti desktop Ctrl+Alt+F11 passa anche a una console di testo: la macro si ferma comunque e si torna con Ctrl+Alt+F1, F2 o F7. **Ctrl+Maiusc+F11** ferma tutto senza cambiare console. Su Wayland la posizione della finestra e il "sempre in primo piano" dipendono dal compositor.

**Aggiornamenti e diagnostica.** Il pallino in alto controlla all'avvio solo le release `linux-v*` (disattivabile nel dialogo Aggiornamenti), scarica il tar.gz, verifica lo SHA-256 e riavvia la nuova versione. Preferenze, `ultimo-replay.json` ed `errore.log` sono in `~/.config/MouseMacroStocazzSuperpower`.

## Compilare dai sorgenti

```powershell
python -m pip install -r requirements.txt
python -m unittest discover -v
python build_native_windows.py
```

Dettagli in [BUILD-v1.1.1.md](BUILD-v1.1.1.md). Su Linux: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt 'pyinstaller==6.22.3'`, poi `.venv/bin/python build_release.py && .venv/bin/python package_linux.py` (pacchetto, `install.sh` e SHA256SUMS in `dist/linux`). La vecchia versione Linux v0.14 resta nella [release v0.14](https://github.com/realfulvio/mouse-macro-stocazz-superpower/releases/tag/v0.14-beta); quella attuale è [linux-v1.1.1](https://github.com/realfulvio/mouse-macro-stocazz-superpower/releases/tag/linux-v1.1.1).

[Tutte le release](https://github.com/realfulvio/mouse-macro-stocazz-superpower/releases) · [Materiale promozionale](docs/promo/PRESENTAZIONE.md) · [Note di design](docs/design/README.md) · [Licenza PolyForm Noncommercial](LICENSE): uso libero personale e non commerciale, vietata la rivendita · [Licenze di terze parti](THIRD-PARTY-NOTICES.md) · Progetto e design: **hcok**
