# Build and runtime / Compilazione e avvio

Tested: Python 3.14.7, Flet 1.0.3, PyInstaller 6.22.3.
Build on the target OS. Windows binaries cannot run natively on Linux.

## Windows

```powershell
python -m venv .venv_win
& .\.venv_win\Scripts\python.exe -m pip install -r requirements.txt pyinstaller==6.22.3
& .\.venv_win\Scripts\python.exe -m unittest discover -v
& .\.venv_win\Scripts\python.exe build_release.py
```

Outputs: `dist/windows/MouseMacroStocazzSuperpower-Windows-IT.exe` and `-EN.exe`.
Desktop client and images are embedded. Outfit font uses an online resource,
with a fallback when unavailable.

## Linux

```bash
bash build_linux.sh
```

Outputs: `dist/linux/MouseMacroStocazzSuperpower-Linux-IT` and `-EN`.
The script creates `.venv_linux`, tests and builds both languages. It embeds
the matching desktop client downloaded from official Flet releases. Native
debug symbols are stripped to avoid exposing compilation paths.

Tested on CachyOS x86_64; this is not a universal Linux package. Older distros
may need a native build because of glibc/library compatibility. GTK 3 and Zenity
must be installed. Recording requires read access to the selected `/dev/input`
mouse; playback requires write access to `/dev/uinput`. Use the system's existing
device permission policy; do not run the app as root.

Extract the tar.gz package and run the executable. If copying removed its execute bit:

```bash
chmod +x MouseMacroStocazzSuperpower-Linux-IT
./MouseMacroStocazzSuperpower-Linux-IT
```

Use `-EN` for English. F9/F10 require app focus on Linux. Tab closing and visual
page readiness settings are Windows-only and hidden on Linux.

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
