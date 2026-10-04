# Build Windows v0.18.0-beta

Candidato derivato da `main` `ceee60d2399cd06af00fd029a042dde58b9b32e0`, dopo la release v0.17.0-beta. Nessuna modifica al layout o al motore. Procedura Windows nativa identica a [v0.17](BUILD-v0.17.md), con Python **3.13.16** e .NET Framework 4:

```powershell
python -m pip install -r requirements-windows.txt -r requirements.txt
python -m unittest test_windows_timing test_engine test_session test_windows_backend -v
python -m unittest discover -v
python build_native_windows.py
python qa/check_package.py
```

Output: `dist/windows/MouseMacroStocazzSuperpower-Windows-v0.18.0-beta.zip` e `SHA256SUMS-v0.18.txt`. Il workflow manuale produce soltanto un candidato, senza pubblicare release.

Misura deterministica prima/dopo, inclusa l'attesa finale del giro:

```powershell
python qa/playback_timing.py
```

Collaudo mirato del pacchetto esatto, con Chrome installato e desktop Windows interattivo sbloccato:

```powershell
python -m pip install -r qa/requirements.txt
python qa/rapid_windows.py evidence/v018/desktop
```

Il banco riutilizza pagina, dialoghi e input nativi del collaudo v0.17. Verifica registrazione/caricamento, replay 1×/2× con contatori reali, doppio click, trascinamento, wheel, 20 giri, cambio scheda OFF/ON e hotkey di stop. Non ripete il collaudo grafico completo. Il tempo del motore viene letto da `ultimo-replay.json`; viene conservato anche il tempo esterno del banco.

[Esito e limiti](docs/ESITO-COLLAUDO-v0.18.md).
