# Build Windows v0.18.1-beta

Correzione della limitazione a Chrome/Firefox, derivata dalla release v0.18.0-beta. Procedura nativa invariata:

```powershell
python -m unittest test_session test_windows_backend test_windows_timing test_engine -v
python -m unittest discover -v
python build_native_windows.py
python qa/check_package.py
python qa/global_windows.py evidence/local-windows/global
python qa/rapid_windows.py evidence/local-windows/browser
```

I due banchi interattivi richiedono un desktop Windows sbloccato. Il primo usa due finestre native Tk e il desktop; il secondo verifica le regressioni browser. Output: `MouseMacroStocazzSuperpower-Windows-v0.18.1-beta.zip` e `SHA256SUMS-v0.18.1.txt`.

[Esito](docs/ESITO-COLLAUDO-v0.18.1.md).
