# Build Windows v1.2.8

Su Windows x64 con Python 3.13.x e .NET Framework 4:

```powershell
python -m pip install -r requirements.txt -r requirements-windows.txt
python -m unittest discover -v
python build_native_windows.py
python qa/check_package.py
```

Il runtime distribuito è l'embeddable ufficiale Python 3.13.16. Il pacchetto contiene pynput 1.8.1 e six 1.17.0, con il bytecode di app e `runtime/Lib` già compilato (`.pyc` con hash verificato, PEP 552: usato solo se l'hash del `.py` accanto coincide, a prescindere dalle date dei file; per questo la build richiede Python 3.13). Le WebP animate servono solo al pannello Linux e non entrano nello ZIP Windows; il rilevamento del mouse usa SetupAPI e Configuration Manager, senza dipendenze aggiuntive o PowerShell.

Per compilare offline, conserva in `vendor/` il runtime `python-3.13.16-embed-amd64.zip` e le due wheel, quindi usa `python build_native_windows.py --offline`.

Gli output sono lo ZIP versionato, l'alias `MouseMacroStocazzSuperpower-Windows-Portable.zip` e `SHA256SUMS-v1.2.8.txt`. Il manifest elenca tutti i file e i relativi hash. Il launcher `.cmd` usa lo stesso runtime e gli stessi sorgenti del launcher `.exe`. Tutti i launcher avviano `app\windows_main.py`, che dalla 1.2.8 è un ingresso di poche righe: il pannello sta in `windows_panel.py`, caricato dal bytecode (Python ricompila sempre lo script avviato).

Il workflow `package-acceptance.yml` confronta lo ZIP candidato con quello pubblicato della v1.2.7: launcher exe, alternativa cmd, installazione per utente, manifest e hash, pixel Bambola, tre finestre CPU a riposo/in registrazione/in riproduzione, UIPI e 30 ripetizioni della macro di riferimento. I processi della prova CPU usano il runtime e i sorgenti estratti dal pacchetto; il confronto di fedeltà avvia il suo pythonw.exe con il pannello distribuito. Il workflow `paired.yml` (a ogni PR che tocca il pannello) misura candidato e v1.2.7 sullo stesso runner, alternati ABBA: avvio fino al pannello che risponde, CPU, memoria, oggetti GDI e handle a riposo con la loro crescita, CPU in registrazione e riproduzione, tempo di import.

Prima di pubblicare, esaminare i risultati e le soglie congelate. Il runner condiviso non certifica il p95 degli intervalli, SmartScreen, giochi, DPI misto o più monitor. Pubblicare l'esatto artifact collaudato tramite `publish-release.yml`, senza ricompilarlo. La v1.2.8 è una patch di manutenzione, senza funzioni nuove: avvio più rapido (bytecode nel pacchetto, ingresso corto, moduli di rete e archivi caricati solo quando servono), meno CPU nella barra compatta e meno lavoro per Explorer (titolo al massimo una volta al secondo), traccia della riproduzione limitata e scritta fuori dal thread dell'interfaccia, pittura che non può più restare bloccata in un ciclo di errori, impostazioni scritte in modo atomico, ZIP più leggero di circa 4 MB. Il confronto di riferimento è la v1.2.7: avvio, CPU a riposo, in registrazione e in riproduzione non devono peggiorare. La parte di attesa resta quella della v1.2.6 (timer ad alta risoluzione, spin residuo massimo di 0,3 ms).

Avviare manualmente `package-acceptance.yml` sul ref candidato indicando il run di build dell’esatto commit. Il workflow rifiuta artifact di altri commit; passare una PR da bozza a pronta non avvia una seconda misura.
