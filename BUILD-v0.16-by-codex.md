# Build Windows v0.16 — by codex

Base: tag `v0.15.1-beta`, commit `7dbdc83b44dacd6c3853584b10e011c647be93d1`.
Questo ramo locale usa il nuovo pannello Win32; la UI Flet resta per Linux.
Gli script storici di build sono conservati; per **questa** consegna Windows usare quello seguente.

Su Windows x64 con Python **3.13.16** e .NET Framework 4 (presente nella VM Windows 11):

```powershell
python -m venv .venv_win
.\.venv_win\Scripts\python.exe -m pip install -r requirements-windows.txt
.\.venv_win\Scripts\python.exe build_native_windows.py
```

Per aprire il pannello direttamente dai sorgenti Windows: `.\.venv_win\Scripts\python.exe windows_main.py` oppure `main.py`. Il launcher distribuito avvia esplicitamente `windows_main.py`.

Risultato: `dist/windows/MouseMacroStocazzSuperpower-Windows-v0.16.0-beta-by-codex.zip` e `SHA256SUMS-v0.16.txt`.

Se Windows non è raggiungibile, è disponibile anche la compilazione del launcher su Linux:

```sh
.venv/bin/python build_native_windows.py --cross
```

Richiede SDK .NET **10.0.112**, nel percorso `/usr/share/dotnet/sdk/10.0.112`; il builder usa Roslyn e le reference assemblies Microsoft .NET Framework **4.8**, pacchetto NuGet **1.0.3**. Include lo stesso runtime Windows embeddable e le stesse dipendenze fissate. Questa opzione produce un candidato Windows: **non sostituisce l'esecuzione e il collaudo di quel pacchetto nella VM**. Il manifest identifica il compilatore usato. Il rapporto distingue l'ultima compilazione locale dai pacchetti precedenti effettivamente avviati in Windows.
Il builder scarica il runtime embeddable **solo durante la build**, dal sito ufficiale Python; ne registra SHA256 nel manifest. Il prodotto distribuito non scarica nulla al primo avvio. Il runtime originale mantiene nome e firma; il piccolo launcher .NET nuovo è **non firmato**. Nessun `sitecustomize`, client Flet o server web viene incluso nel prodotto Windows. L’archivio contiene il manifest degli hash di tutti i file.

Per ripetere l’intera suite dei sorgenti (comprende la UI Linux storica):

```powershell
.\.venv_win\Scripts\python.exe -m pip install flet==1.0.3 flet-web==1.0.3
.\.venv_win\Scripts\python.exe -m unittest discover -v
```

Per il banco di accettazione Windows:

```powershell
.\.venv_win\Scripts\python.exe -m pip install -r qa/requirements.txt
.\.venv_win\Scripts\python.exe qa/run_desktop.py evidence/desktop-final
```

Il banco richiede un **desktop interattivo sbloccato**, Chrome e Firefox installati. Può essere avviato con un task temporaneo `InteractiveToken` dell’utente della sessione. Il comando eseguito nella sola sessione SSH non sostituisce questa prova. Selenium prepara pagine e schede, legge i contatori; la registrazione e la riproduzione usano input nativi nel browser visibile. Selenium Manager può scaricare i driver del banco, che non fanno parte del prodotto.

Il banco estrae il ZIP, avvia il suo launcher con Python escluso dal PATH e confronta contatori reali. Le vecchie run e gli errori rimangono nelle evidenze. Il processo di build è ripetibile con queste versioni; il compilatore .NET e i timestamp ZIP possono produrre hash diversi fra due build. La validazione è riferita all’hash del pacchetto specifico indicato nel rapporto, non a qualunque ricompilazione successiva.


## Collaudo mirato

`qa/run_desktop.py <output> --dpi-smoke` controlla due giri per velocità e cinque schede/due finestre a DPI maggiori di 96. `--firefox-only` limita la prova a Firefox.

`qa/offline_startup.py` verifica l’avvio del pacchetto con il runtime incluso. Per provare l’assenza di rete disconnettere solo la scheda virtuale della VM. Gli esiti della release sono in [docs/ESITO-COLLAUDO-v0.16.md](docs/ESITO-COLLAUDO-v0.16.md).
