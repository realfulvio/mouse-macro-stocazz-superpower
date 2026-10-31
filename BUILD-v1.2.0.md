# Build Windows v1.2.0

Su Windows x64 con Python 3.13.x e .NET Framework 4:

```powershell
python -m pip install -r requirements.txt -r requirements-windows.txt
python -m unittest discover -v
python build_native_windows.py
python qa/check_package.py
python build_windows_installer.py   # serve Inno Setup 6
```

Il runtime distribuito è l'embeddable ufficiale Python 3.13.16. Il pacchetto contiene pynput 1.8.1 e six 1.17.0; il rilevamento del mouse usa SetupAPI e Configuration Manager, senza dipendenze aggiuntive o PowerShell.

Per compilare offline, conserva in `vendor/` il runtime `python-3.13.16-embed-amd64.zip` e le due wheel, quindi usa `python build_native_windows.py --offline`.

Gli output sono lo ZIP versionato, l'alias `MouseMacroStocazzSuperpower-Windows-Portable.zip`, il setup `MouseMacroStocazzSuperpower-Setup-v1.2.0.exe` (Inno Setup 6, script in `installer/`) e `SHA256SUMS-v1.2.0.txt`, che contiene gli hash di tutti e tre. Il manifest elenca tutti i file e i relativi hash. Il launcher `.cmd` usa lo stesso runtime e gli stessi sorgenti del launcher `.exe`.

Prima di pubblicare, verifica l'esatto ZIP sul desktop interattivo. Non ricompilarlo dopo il collaudo senza ripetere le prove. Rispetto alla v1.1.2 cambiano solo il setup e la proposta di aggiornamento all’avvio.
