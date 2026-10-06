# Build Windows v1.0.0

Su Windows x64 con Python 3.13.x e .NET Framework 4:

```powershell
python -m pip install -r requirements.txt
python -m unittest discover -v
python build_native_windows.py
python qa/check_package.py
```

`requirements.txt` serve solo ai test (include Flet per la vecchia interfaccia Linux); il pacchetto Windows contiene soltanto `pynput` e `six`, elencati in `requirements-windows.txt`.

Il runtime distribuito è sempre l'embeddable ufficiale **Python 3.13.16**, scaricato da python.org e confrontato con il suo hash. L'interprete di build installa soltanto le due wheel pure Python, quindi basta una qualsiasi 3.13.x.

Build offline: metti in `vendor/` il runtime `python-3.13.16-embed-amd64.zip` e le wheel `pynput==1.8.1` e `six==1.17.0`, poi:

```powershell
python build_native_windows.py --offline
```

`--pip-python` indica un altro interprete con pip per installare le due wheel.

Output in `dist/windows/`: ZIP versionato e `MouseMacroStocazzSuperpower-Windows-Portable.zip` (identici byte per byte), più `SHA256SUMS-v1.0.0.txt`.

## Collaudo interattivo

I test automatici verificano la logica, non il desktop reale. Prima di pubblicare un nuovo ZIP, provalo su un desktop Windows sbloccato: barra in registrazione e replay, Stop da pulsante, F9/F10/Ctrl+Alt+F11, input 1–999, click, doppio click, trascinamento, rotella, 1×/2×, 20 giri, Salva/Carica, DPI 100%/150%.

`qa/global_windows.py` automatizza una parte di queste prove con due finestre dedicate. È pensato per **una VM 1280×800 con un solo monitor**: su un desktop a più monitor o con altre finestre aperte non usarlo.

## Controllo di privacy

```powershell
python qa/privacy_package.py --deny-list build/privacy-terms.local.json
```

La lista dei nomi riservati è un JSON locale (una stringa per identificativo), escluso dal repository. Richiede Pillow.
