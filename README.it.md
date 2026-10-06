<p align="center"><a href="README.md">English</a> · <b>Italiano</b></p>

<h1 align="center">Mouse Macro Stocazz Superpower</h1>

<p align="center">
Registra il mouse e ripeti la sequenza quante volte vuoi.<br>
Un piccolo pannello sempre in primo piano per Windows: niente installer, niente Python da installare.
</p>

<p align="center">
<a href="https://github.com/realfulvio/mouse-macro-stocazz-superpower/releases/tag/v1.0.0"><b>⬇ Scarica per Windows</b></a>
· <a href="GUIDA-ITALIANA.md">Guida italiana</a>
· <a href="docs/ESITO-COLLAUDO-v1.0.0.md">Esito dei controlli</a>
</p>

<p align="center">
<img src="docs/screenshots/v100-compact.png" alt="Pannello principale" width="260">
&nbsp;
<img src="docs/screenshots/v100-playing.png" alt="Barra durante la riproduzione" width="288">
</p>

## Cosa fa

- Registra movimenti, click, doppi click, trascinamenti e rotella, in qualsiasi programma, sul desktop e sulle barre del browser.
- Riproduce la sequenza da 1 a 999 volte, a velocità normale o **2× più veloce**.
- Durante registrazione e replay il pannello diventa una piccola barra semitrasparente con contatori e pulsante **Stop**, per non dare fastidio.
- Salva e carica le macro in file `.mmr`.
- **Ctrl+Tab tra un giro e l'altro** (facoltativo) per scorrere le schede del browser: spento all'avvio, mai dopo l'ultimo giro.
- Registra solo il mouse: niente tastiera, niente schermate, nessun accesso alla rete.

## Installazione

1. Scarica `MouseMacroStocazzSuperpower-Windows-v1.0.0.zip` dalla [release](https://github.com/realfulvio/mouse-macro-stocazz-superpower/releases/tag/v1.0.0).
2. Estrai **tutto** lo ZIP in una cartella.
3. Apri `Mouse Macro v1.0.0.exe`.

**Windows blocca l'exe?** Il launcher `.exe` non è firmato, quindi SmartScreen o il *Controllo intelligente delle app* (Smart App Control) di Windows 11 possono bloccarlo. C'è un'alternativa senza exe: il comando PowerShell qui sotto (funziona con la release v1.0.0 attuale), oppure `launcher.cmd`, incluso nello ZIP delle release successive alla v1.0.0 e disponibile nel repository (copialo accanto a `runtime` e `app`, poi eseguilo). Avvia direttamente il `pythonw.exe` ufficiale di Python (firmato dalla Python Software Foundation) con gli stessi file. Se SmartScreen avvisa, usa *Ulteriori informazioni → Esegui comunque*; se blocca ancora, tasto destro sullo ZIP → *Proprietà* → **Sblocca** prima di estrarlo. Non serve disattivare nessuna protezione.

**Oppure da PowerShell**, senza scaricare nulla a mano:

```powershell
irm https://raw.githubusercontent.com/realfulvio/mouse-macro-stocazz-superpower/main/install.ps1 | iex
```

Lo script scarica la release ufficiale da GitHub, ne verifica lo SHA-256, la estrae in `%LOCALAPPDATA%\MouseMacroStocazzSuperpower\Portable` e avvia il programma con il `pythonw.exe` firmato PSF; dalla seconda volta riavvia solo l'app. Un file scaricato da PowerShell non ha il Mark of the Web. Leggi prima [install.ps1](install.ps1) se vuoi sapere cosa esegue.

Queste alternative non sono certificate con Smart App Control. Se anche il `.cmd` viene bloccato, scrivilo nelle [Issues](https://github.com/realfulvio/mouse-macro-stocazz-superpower/issues).

Serve Windows x64 con .NET Framework 4 (già presente in Windows 10/11). Python è incluso. L'interfaccia è in italiano. Il launcher non è firmato: al primo avvio SmartScreen può segnalarlo; lo SHA-256 dello ZIP è pubblicato con ogni release.

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
- Non certificato con SentinelOne o Smart App Control. Nessuna protezione viene modificata o aggirata.

## Stato

Stabile. Controlli su questa release ([rapporto](docs/ESITO-COLLAUDO-v1.0.0.md)): 141 test automatici (135 superati, 6 solo-Linux saltati), integrità del pacchetto, avvio reale dell'exe distribuito e prova fisica di registrazione/replay a 1× e 2× con conteggi esatti e stop in 5 ms. Non coperti: UAC/applicazioni elevate, altre scale DPI su monitor reali.

## Compilare dai sorgenti

```powershell
python -m pip install -r requirements.txt
python -m unittest discover -v
python build_native_windows.py
```

Dettagli in [BUILD-v1.0.0.md](BUILD-v1.0.0.md). La vecchia versione Linux (Flet, IT/EN) è nella [release v0.14](https://github.com/realfulvio/mouse-macro-stocazz-superpower/releases/tag/v0.14-beta).

[Tutte le release](https://github.com/realfulvio/mouse-macro-stocazz-superpower/releases) · [Note di design](docs/design/README.md) · [Licenza PolyForm Noncommercial](LICENSE): uso libero personale e non commerciale, vietata la rivendita · [Licenze di terze parti](THIRD-PARTY-NOTICES.md) · Progetto e design: **hcok**
