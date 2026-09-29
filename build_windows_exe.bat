@echo off
REM Crea un eseguibile Windows portable (un solo file .exe, nessuna installazione,
REM doppio click per avviare, nessuna finestra di terminale). Va eseguito SU Windows
REM (es. la VM Windows 11), non su Linux: PyInstaller non compila in cross-platform.

py -3 -m venv .venv_win
call .venv_win\Scripts\activate.bat

pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

pyinstaller --noconfirm --onefile --windowed ^
    --name "Mouse Macro Stocazz Superpower" ^
    --icon assets\icon.ico ^
    --add-data "assets;assets" ^
    --paths . ^
    main.py

echo.
echo Fatto! L'eseguibile portable e' in dist\Mouse Macro Stocazz Superpower.exe
pause
