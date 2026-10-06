@echo off
rem Alternative launcher without an .exe: starts the signed PSF pythonw.exe directly.
rem Useful when Smart App Control / SmartScreen blocks the unsigned "Mouse Macro" .exe.
cd /d "%~dp0"
if not exist "runtime\pythonw.exe" goto missing
if not exist "app\windows_main.py" goto missing
start "" "runtime\pythonw.exe" -B "app\windows_main.py"
exit /b 0
:missing
echo Estrai tutto lo ZIP e mantieni insieme tutti i file.
echo Extract the whole ZIP and keep all files together.
pause
exit /b 1
