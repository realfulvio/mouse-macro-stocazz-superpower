<p align="center"><b>English</b> · <a href="README.it.md">Italiano</a></p>

<h1 align="center">Mouse Macro Stocazz Superpower</h1>

<p align="center">
Record your mouse, replay it as many times as you need.<br>
A small always-on-top panel for Windows: no installer, no Python to install.
</p>

<p align="center">
<a href="https://github.com/realfulvio/mouse-macro-stocazz-superpower/releases/tag/v1.0.1"><b>⬇ Download for Windows</b></a>
· <a href="GUIDA-ITALIANA.md">Italian guide</a>
· <a href="docs/ESITO-COLLAUDO-v1.0.1.md">Test report</a>
</p>

<p align="center">
<img src="docs/screenshots/v100-compact.png" alt="Main panel" width="260">
&nbsp;
<img src="docs/screenshots/v100-playing.png" alt="Activity bar while replaying" width="288">
</p>

## What it does

- Records mouse movement, clicks, double clicks, dragging and the scroll wheel, across any program, the desktop and browser toolbars.
- Replays the sequence 1–999 times at normal speed or **2× faster**.
- While recording or replaying, the panel shrinks to a small translucent bar with the counters and a **Stop** button, so it stays out of the way.
- Save and load macros as `.mmr` files.
- Optional **Ctrl+Tab between cycles** to move through browser tabs (off by default; never after the last cycle).
- Records the mouse only: no keyboard keys, no screenshots, no network access.

## Install

1. Download `MouseMacroStocazzSuperpower-Windows-v1.0.1.zip` from the [release](https://github.com/realfulvio/mouse-macro-stocazz-superpower/releases/tag/v1.0.1).
2. Extract the **whole** ZIP into a folder.
3. Run `Mouse Macro v1.0.1.exe`. If Windows blocks it (see below), run `Mouse Macro v1.0.1 (senza exe).cmd` instead.

Requires x64 Windows; the exe also needs .NET Framework 4 (included in Windows 10/11), the `.cmd` does not. Python is bundled. The interface is in Italian. The SHA-256 of the ZIP is published with each release.

### Windows blocks the exe?

The `.exe` launcher is not code-signed, so SmartScreen or Windows 11 *Smart App Control* may block it (*"An application control policy has blocked this file"*). Two exe-free alternatives, **tested with Smart App Control enforced** (Windows 11 build 26300, see the [report](docs/ESITO-COLLAUDO-v1.0.1.md)):

- **`Mouse Macro v1.0.1 (senza exe).cmd`**, in the same ZIP: starts the official Python `pythonw.exe` (signed by the Python Software Foundation) directly with the same files. If SmartScreen warns, choose *More info → Run anyway*; if it still blocks, right-click the ZIP → *Properties* → **Unblock** before extracting.
- **From PowerShell**, with nothing to download by hand:

```powershell
irm https://raw.githubusercontent.com/realfulvio/mouse-macro-stocazz-superpower/main/install.ps1 | iex
```

The script downloads the official release from GitHub, verifies its SHA-256, extracts it to `%LOCALAPPDATA%\MouseMacroStocazzSuperpower\Portable` and starts the app with the PSF-signed `pythonw.exe`; later runs just relaunch it. A file downloaded by PowerShell carries no Mark of the Web. Read [install.ps1](install.ps1) first if you want to see what it runs.

No protection needs to be turned off. If these are blocked on your PC too, please open an [issue](https://github.com/realfulvio/mouse-macro-stocazz-superpower/issues).
## Use

| Step | Action |
|---|---|
| 1 | Arrange the windows you will use and move the panel out of the way |
| 2 | **F9**, perform the mouse sequence, **F9** again |
| 3 | Open **Opzioni** and type the number of repeats (1–999) or use **−/+** / **Preset 20**; pick **Normale** or **Rapida 2×** |
| 4 | Restore the starting state and press **F10** to play |
| – | **F10** or **Stop** stops playback · **Ctrl+Alt+F11** is the global emergency stop |

<p align="center"><img src="docs/screenshots/v100-expanded.png" alt="Options expanded" width="560"></p>

**Rapida 2×** speeds up movement and ordinary pauses; waits longer than 2 s stay at 1×, and click holds and double clicks stay protected, so the total time is not exactly halved. **Pagine lente** adds longer, more cautious pauses for slow web pages.

## Good to know

- Replay uses **absolute screen coordinates**. Keep window positions, resolution, monitor layout and Windows scaling the same as when you recorded.
- The panel must not sit on top of a recorded click; the app moves the bar to a free spot or refuses to start.
- The app cannot tell whether a website accepted a click, and it never retries.
- Not covered: UAC / secure desktop and elevated applications.
- Not certified with SentinelOne. With Smart App Control enforced the exe is blocked, while the `.cmd` and the PowerShell command were tested and work. No protection is changed or bypassed.

## Status

Stable. v1.0.1 only adds the exe-free launch options; the recorder/replay code is unchanged from v1.0.0. Checks on this release ([report](docs/ESITO-COLLAUDO-v1.0.1.md)): 141 automated tests (135 passed, 6 Linux-only skipped), package integrity, and real launches of the `.cmd` and of the PowerShell command with Smart App Control enforced (the unsigned exe is blocked, as expected). The physical record/replay results come from the [v1.0.0 report](docs/ESITO-COLLAUDO-v1.0.0.md) and were not repeated. Not covered: UAC/elevated apps, other DPI scalings on real monitors.

## Build from source

```powershell
python -m pip install -r requirements.txt
python -m unittest discover -v
python build_native_windows.py
```

Details in [BUILD-v1.0.1.md](BUILD-v1.0.1.md). The older Linux version (Flet, IT/EN) is in the [v0.14 release](https://github.com/realfulvio/mouse-macro-stocazz-superpower/releases/tag/v0.14-beta).

[All releases](https://github.com/realfulvio/mouse-macro-stocazz-superpower/releases) · [Design notes](docs/design/README.md) · [PolyForm Noncommercial License](LICENSE): free for personal and non-commercial use, no commercial resale · [Third-party notices](THIRD-PARTY-NOTICES.md) · Project and design: **hcok**
