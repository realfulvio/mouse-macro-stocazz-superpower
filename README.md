<p align="center"><b>Italiano</b> · <a href="README.en.md">English</a></p>

<h1 align="center">Mouse Macro Stocazz Superpower</h1>

<p align="center">
Registra il mouse e ripeti la sequenza quante volte vuoi.<br>
Un piccolo pannello sempre in primo piano per Windows: niente installer, niente Python da installare.
</p>

<p align="center">
<a href="https://github.com/realfulvio/mouse-macro-stocazz-superpower/releases/tag/v1.1.1"><b>⬇ Scarica per Windows</b></a>
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

1. Scarica `MouseMacroStocazzSuperpower-Windows-v1.1.1.zip` dalla [release](https://github.com/realfulvio/mouse-macro-stocazz-superpower/releases/tag/v1.1.1).
2. Estrai **tutto** lo ZIP in una cartella.
3. Apri `Mouse Macro v1.1.1.exe`. Se Windows lo blocca, apri invece `Mouse Macro v1.1.1 (senza exe).cmd`.

Serve Windows x64; l'exe richiede anche .NET Framework 4 (già presente in Windows 10/11), il `.cmd` no. Python è incluso. L'interfaccia è in italiano. Lo SHA-256 dello ZIP è pubblicato con ogni release.

### Windows blocca l'exe?

Il launcher `.exe` non è firmato: SmartScreen o il *Controllo intelligente delle app* (Smart App Control) di Windows 11 possono bloccarlo (*"Un criterio di controllo dell'applicazione ha bloccato il file"*). Le due vie senza exe, cioè il comando PowerShell qui sopra e il file **`Mouse Macro v1.1.1 (senza exe).cmd`** nello ZIP, sono state provate con Smart App Control nella v1.1.0 (Windows 11 build 26300, [rapporto precedente](docs/ESITO-COLLAUDO-v1.1.0.md)); la verifica SAC non è stata ripetuta per la v1.1.1. Il `.cmd` avvia direttamente il `pythonw.exe` firmato PSF con gli stessi file. Se SmartScreen avvisa, usa *Ulteriori informazioni → Esegui comunque*; se blocca ancora, tasto destro sullo ZIP → *Proprietà* → **Sblocca** prima di estrarlo.

Se anche queste vie vengono bloccate sul tuo PC, scrivilo nelle [Issues](https://github.com/realfulvio/mouse-macro-stocazz-superpower/issues).

La v1.1.1 corregge la digitazione delle ripetizioni e mostra il modello del mouse. [Download Portable](https://github.com/realfulvio/mouse-macro-stocazz-superpower/releases/download/v1.1.1/MouseMacroStocazzSuperpower-Windows-Portable.zip).

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

## Compilare dai sorgenti

```powershell
python -m pip install -r requirements.txt
python -m unittest discover -v
python build_native_windows.py
```

Dettagli in [BUILD-v1.1.1.md](BUILD-v1.1.1.md). La vecchia versione Linux (Flet, IT/EN) è nella [release v0.14](https://github.com/realfulvio/mouse-macro-stocazz-superpower/releases/tag/v0.14-beta).

[Tutte le release](https://github.com/realfulvio/mouse-macro-stocazz-superpower/releases) · [Note di design](docs/design/README.md) · [Licenza PolyForm Noncommercial](LICENSE): uso libero personale e non commerciale, vietata la rivendita · [Licenze di terze parti](THIRD-PARTY-NOTICES.md) · Progetto e design: **hcok**
