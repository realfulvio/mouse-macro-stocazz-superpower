# Build and runtime / Compilazione e avvio

Tested: Python 3.13, Flet 1.0.3, PyInstaller 6.22.3.
Build on the target OS. Windows binaries cannot run natively on Linux.

## Windows

```powershell
python -m venv .venv_win
& .\.venv_win\Scripts\python.exe -m pip install -r requirements.txt pyinstaller==6.22.3
& .\.venv_win\Scripts\python.exe -m unittest discover -v
& .\.venv_win\Scripts\python.exe build_release.py
```

Outputs: `dist/windows/MouseMacroStocazzSuperpower-Windows-IT.exe` and `-EN.exe`, plus
`SHA256SUMS.txt`.

On Windows the interface is not shown by the Flet desktop client (`flet.exe`): that helper
is unsigned and Windows 11 Smart App Control blocks it. `app_launcher.py` instead serves the
Flet UI on `127.0.0.1` under a random path and opens it in a Microsoft Edge window in app mode
(`--app`, dedicated profile in `%LOCALAPPDATA%\MouseMacroStocazzSuperpower\window`). The exe
embeds the Flet web client (without the unused Pyodide runtime) and the fonts in
`assets/fonts`, so nothing is loaded from the internet. Closing the window ends the program.
Open/Save use the native Windows dialogs (`macro/win_dialogs.py`), because the Flet file
picker in a browser window cannot return file paths.

## Linux

```bash
bash build_linux.sh
```

Outputs: `dist/linux/MouseMacroStocazzSuperpower-Linux-IT` and `-EN`.
The script creates `.venv_linux`, tests and builds both languages. It embeds
the matching desktop client downloaded from official Flet releases. Native
debug symbols are stripped to avoid exposing compilation paths.

This is not a universal Linux package: the release builds are made on Ubuntu 22.04, and
v0.13 was tested on CachyOS x86_64. Very old distros may need a native build because of
glibc/library compatibility. GTK 3 and Zenity must be installed. Recording requires read
access to the selected `/dev/input` mouse; playback requires write access to `/dev/uinput`.
Use the system's existing device permission policy; do not run the app as root.

Extract the tar.gz package and run the executable. If copying removed its execute bit:

```bash
chmod +x MouseMacroStocazzSuperpower-Linux-IT
./MouseMacroStocazzSuperpower-Linux-IT
```

Use `-EN` for English. On Linux F9/F10 require app focus; visual page readiness
("Wait for page") is Windows-only.

## Releases

`.github/workflows/release.yml` runs the tests and builds all four binaries on GitHub
Actions (Windows and Ubuntu 22.04). Pushing a tag such as `v0.14-beta` publishes them,
with `SHA256SUMS.txt`, as a GitHub Release.

## Headless diagnostics

```powershell
& .\MouseMacroStocazzSuperpower-Windows-IT.exe --self-test report.json
```

```bash
./MouseMacroStocazzSuperpower-Linux-IT --self-test report.json
```

Diagnostics test imports, files, timing, translations and UI construction without
desktop input. Linux creates/closes a virtual uinput device without emitting events.
This does not validate native dialogs or website click results. Distribution files
include SHA256 checksums.
