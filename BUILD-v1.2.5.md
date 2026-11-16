# Build Windows v1.2.5

Su Windows x64 con Python 3.13.x e .NET Framework 4:

```powershell
python -m pip install -r requirements.txt -r requirements-windows.txt
python -m unittest discover -v
python build_native_windows.py
python qa/check_package.py
```

Il runtime distribuito è l'embeddable ufficiale Python 3.13.16. Il pacchetto contiene pynput 1.8.1 e six 1.17.0; il rilevamento del mouse usa SetupAPI e Configuration Manager, senza dipendenze aggiuntive o PowerShell.

Per compilare offline, conserva in `vendor/` il runtime `python-3.13.16-embed-amd64.zip` e le due wheel, quindi usa `python build_native_windows.py --offline`.

Gli output sono lo ZIP versionato, l'alias `MouseMacroStocazzSuperpower-Windows-Portable.zip` e `SHA256SUMS-v1.2.5.txt`. Il manifest elenca tutti i file e i relativi hash. Il launcher `.cmd` usa lo stesso runtime e gli stessi sorgenti del launcher `.exe`.

Il workflow `package-acceptance.yml` confronta lo ZIP candidato con quello pubblicato della v1.2.4: launcher exe, alternativa cmd, installazione per utente, manifest e hash, pixel Bambola, tre finestre CPU a riposo/in registrazione/in riproduzione, UIPI e 30 ripetizioni della macro di riferimento. I processi della prova CPU usano il runtime e i sorgenti estratti dal pacchetto; il confronto di fedeltà avvia il suo pythonw.exe con il pannello distribuito.

Prima di pubblicare, esaminare i risultati e le soglie congelate. Il runner condiviso non certifica il p95 degli intervalli, SmartScreen, giochi, DPI misto o più monitor. Pubblicare l'esatto artifact collaudato tramite `publish-release.yml`, senza ricompilarlo. La v1.2.5 aggiunge il controllo dei privilegi prima di avviare il player; motore e backend temporizzato sono invariati rispetto alla v1.2.4.
