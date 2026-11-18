# Build Windows v1.2.7

Su Windows x64 con Python 3.13.x e .NET Framework 4:

```powershell
python -m pip install -r requirements.txt -r requirements-windows.txt
python -m unittest discover -v
python build_native_windows.py
python qa/check_package.py
```

Il runtime distribuito è l'embeddable ufficiale Python 3.13.16. Il pacchetto contiene pynput 1.8.1 e six 1.17.0; il rilevamento del mouse usa SetupAPI e Configuration Manager, senza dipendenze aggiuntive o PowerShell.

Per compilare offline, conserva in `vendor/` il runtime `python-3.13.16-embed-amd64.zip` e le due wheel, quindi usa `python build_native_windows.py --offline`.

Gli output sono lo ZIP versionato, l'alias `MouseMacroStocazzSuperpower-Windows-Portable.zip` e `SHA256SUMS-v1.2.7.txt`. Il manifest elenca tutti i file e i relativi hash. Il launcher `.cmd` usa lo stesso runtime e gli stessi sorgenti del launcher `.exe`.

Il workflow `package-acceptance.yml` confronta lo ZIP candidato con quello pubblicato della v1.2.6: launcher exe, alternativa cmd, installazione per utente, manifest e hash, pixel Bambola, tre finestre CPU a riposo/in registrazione/in riproduzione, UIPI e 30 ripetizioni della macro di riferimento. I processi della prova CPU usano il runtime e i sorgenti estratti dal pacchetto; il confronto di fedeltà avvia il suo pythonw.exe con il pannello distribuito.

Prima di pubblicare, esaminare i risultati e le soglie congelate. Il runner condiviso non certifica il p95 degli intervalli, SmartScreen, giochi, DPI misto o più monitor. Pubblicare l'esatto artifact collaudato tramite `publish-release.yml`, senza ricompilarlo. La v1.2.7 è una patch di correzioni dalla revisione completa del codice (PR #53), senza funzioni nuove: validazione dei gesti in cache (la CPU a riposo non cresce più con la lunghezza della macro), pannello che entra nell'area di lavoro a DPI alti, finestra Impostazioni che segue il DPI e il menu del tray, aggiornamento che attende la fine di registrazione o riproduzione e non parte due volte, hash dello ZIP in streaming, `.cmd` delle macro avviabili con confronto numerico delle versioni, icona del tray alla dimensione corretta. Il confronto di riferimento è la v1.2.6: la CPU a riposo, in registrazione e in riproduzione non deve peggiorare. Il pacchetto non cambia la parte di attesa della v1.2.6 (timer ad alta risoluzione, spin residuo massimo di 0,3 ms).

Avviare manualmente `package-acceptance.yml` sul ref candidato indicando il run di build dell’esatto commit. Il workflow rifiuta artifact di altri commit; passare una PR da bozza a pronta non avvia una seconda misura.
