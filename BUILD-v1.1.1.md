# Build Windows v1.1.1

Su Windows x64 con Python 3.13.x e .NET Framework 4:

```powershell
python -m pip install -r requirements.txt -r requirements-windows.txt
python -m unittest discover -v
python build_native_windows.py
python qa/check_package.py
```

Il runtime distribuito è l'embeddable ufficiale Python 3.13.16. Il pacchetto contiene pynput 1.8.1 e six 1.17.0; il rilevamento del mouse usa SetupAPI e Configuration Manager, senza dipendenze aggiuntive o PowerShell.

Per compilare offline, conserva in `vendor/` il runtime `python-3.13.16-embed-amd64.zip` e le due wheel, quindi usa `python build_native_windows.py --offline`.

Gli output sono lo ZIP versionato, l'alias `MouseMacroStocazzSuperpower-Windows-Portable.zip` e `SHA256SUMS-v1.1.1.txt`. Il manifest elenca tutti i file e i relativi hash. Il launcher `.cmd` usa lo stesso runtime e gli stessi sorgenti del launcher `.exe`.

Prima di pubblicare, verifica l'esatto ZIP sul desktop interattivo. Non ricompilarlo dopo il collaudo senza ripetere le prove. [Risultati e limiti della v1.1.1](docs/ESITO-COLLAUDO-v1.1.1.md).
