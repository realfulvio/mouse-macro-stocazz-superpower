<p align="center"><a href="README.md">English</a> · <b>Italiano</b></p>

<h1 align="center">Mouse Macro Stocazz Superpower</h1>

<p align="center">
Registra il mouse e ripeti la sequenza quante volte vuoi.<br>
Un piccolo pannello sempre in primo piano per Windows: niente installer, niente Python da installare.
</p>

<p align="center">
<a href="https://github.com/realfulvio/mouse-macro-stocazz-superpower/releases/tag/v0.19.1-beta"><b>⬇ Scarica per Windows</b></a>
· <a href="GUIDA-ITALIANA.md">Guida italiana</a>
· <a href="docs/ESITO-COLLAUDO-v0.19.1.md">Esito dei controlli</a>
</p>

<p align="center">
<img src="docs/screenshots/v019-compact-real.png" alt="Pannello principale" width="260">
&nbsp;
<img src="docs/screenshots/v019-playing-real.png" alt="Barra durante la riproduzione" width="288">
</p>

## Cosa fa

- Registra movimenti, click, doppi click, trascinamenti e rotella, in qualsiasi programma, sul desktop e sulle barre del browser.
- Riproduce la sequenza da 1 a 999 volte, a velocità normale o **2× più veloce**.
- Durante registrazione e replay il pannello diventa una piccola barra semitrasparente con contatori e pulsante **Stop**, per non dare fastidio.
- Salva e carica le macro in file `.mmr`.
- **Ctrl+Tab tra un giro e l'altro** (facoltativo) per scorrere le schede del browser: spento all'avvio, mai dopo l'ultimo giro.
- Registra solo il mouse: niente tastiera, niente schermate, nessun accesso alla rete.

## Installazione

1. Scarica `MouseMacroStocazzSuperpower-Windows-v0.19.1-beta.zip` dall'[ultima release](https://github.com/realfulvio/mouse-macro-stocazz-superpower/releases/tag/v0.19.1-beta).
2. Estrai **tutto** lo ZIP in una cartella.
3. Apri `Mouse Macro v0.19.1-beta.exe`.

Serve Windows x64 con .NET Framework 4 (già presente in Windows 10/11). Python è incluso. L'interfaccia è in italiano. Il launcher non è firmato: al primo avvio SmartScreen può segnalarlo; lo SHA-256 dello ZIP è pubblicato con ogni release.

## Uso

| Passo | Azione |
|---|---|
| 1 | Sistema le finestre che userai e sposta il pannello lontano dai punti da cliccare |
| 2 | **F9**, esegui la sequenza con il mouse, **F9** di nuovo |
| 3 | Apri **Opzioni**, scrivi le ripetizioni (1–999) o usa **−/+** / **Preset 20**; scegli **Normale** o **Rapida 2×** |
| 4 | Ripristina lo stato iniziale e premi **F10** per riprodurre |
| – | **F10** o **Stop** fermano il replay · **Ctrl+Alt+F11** è l'arresto di emergenza globale |

<p align="center"><img src="docs/screenshots/v019-expanded-real.png" alt="Opzioni espanse" width="560"></p>

**Rapida 2×** accelera movimenti e pause normali; le attese oltre 2 s restano a 1× e pressioni e doppi click restano protetti, quindi la durata totale non si dimezza esattamente. **Pagine lente** aggiunge pause più lunghe e prudenti per le pagine web lente.

## Da sapere

- Il replay usa **coordinate assolute dello schermo**: mantieni posizione delle finestre, risoluzione, disposizione dei monitor e scala di Windows uguali a quelle della registrazione.
- Il pannello non deve coprire un click registrato: l'app sposta la barra in un punto libero oppure non parte.
- Il programma non sa se un sito ha accettato il click e non riprova mai.
- Non coperti: UAC / desktop sicuro e applicazioni con privilegi elevati.
- Non certificato con SentinelOne o Smart App Control. Nessuna protezione viene modificata o aggirata.

## Stato

Beta. Gli ultimi controlli sono nel [rapporto v0.19.1](docs/ESITO-COLLAUDO-v0.19.1.md): suite automatica da 141 test (135 superati, 6 solo-Linux saltati), integrità del pacchetto e avvio reale dell'exe distribuito. La prova fisica di registrazione/replay è stata fatta sulla v0.19.0 e non è ancora ripetuta sulla v0.19.1: il rapporto elenca con precisione cosa resta aperto.

## Compilare dai sorgenti

```powershell
python -m pip install -r requirements.txt
python -m unittest discover -v
python build_native_windows.py
```

Dettagli in [BUILD-v0.19.1.md](BUILD-v0.19.1.md). La vecchia versione Linux (Flet, IT/EN) è nella [release v0.14](https://github.com/realfulvio/mouse-macro-stocazz-superpower/releases/tag/v0.14-beta).

[Tutte le release](https://github.com/realfulvio/mouse-macro-stocazz-superpower/releases) · [Note di design](docs/design/README.md) · [Licenza MIT](LICENSE) · [Licenze di terze parti](THIRD-PARTY-NOTICES.md) · Progetto e design: **hcok**
