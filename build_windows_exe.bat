@echo off
REM Crea un eseguibile Windows portable (un solo file .exe, nessuna installazione,
REM doppio click per avviare, nessuna finestra di terminale). Va eseguito SU Windows
REM (es. la VM Windows 11), non su Linux: PyInstaller non compila in cross-platform.

py -3 -m venv .venv_win
call .venv_win\Scripts\activate.bat

pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

REM Client grafico ufficiale di Flet (stessa versione del pacchetto flet), incorporato
REM nell'exe: cosi' non viene scaricato al primo avvio (funziona offline e non ha il
REM comportamento "scarica ed esegui" che fa scattare gli antivirus).
for /f %%v in ('python -c "import flet_desktop.version as v; print(v.version)"') do set FLET_VER=%%v
if not exist vendor mkdir vendor
if not exist vendor\flet-windows.zip (
    powershell -NoProfile -Command "Invoke-WebRequest -Uri https://github.com/flet-dev/flet/releases/download/v%FLET_VER%/flet-windows.zip -OutFile vendor\flet-windows.zip"
)

REM flet_desktop viene importato solo dinamicamente da flet (hidden-import),
REM e icons.json/cupertino_icons.json sono letti da flet a runtime invece che
REM importati (collect-data): senza questi PyInstaller li ignora e l'exe
REM crasha all'avvio ("ModuleNotFoundError: flet_desktop" oppure
REM "[Errno 2] No such file or directory: ...\flet\controls\material\icons.json").
REM --noupx: la compressione UPX e' una delle cause piu' comuni di falsi
REM positivi antivirus (i motori euristici la associano a packer/malware).
REM --version-file: metadati Windows (azienda/prodotto/descrizione) che
REM rendono l'exe meno "anonimo" agli occhi degli euristici.
pyinstaller --noconfirm --onefile --windowed --noupx ^
    --name "Mouse Macro Stocazz Superpower" ^
    --icon assets\icon.ico ^
    --add-data "assets;assets" ^
    --add-data "vendor\flet-windows.zip;flet_desktop\app" ^
    --hidden-import flet_desktop ^
    --hidden-import flet_desktop.win_taskbar ^
    --hidden-import flet_desktop.version ^
    --collect-data flet ^
    --version-file version_info.txt ^
    --paths . ^
    main.py

echo.
echo Fatto! L'eseguibile portable e' in dist\Mouse Macro Stocazz Superpower.exe
pause
