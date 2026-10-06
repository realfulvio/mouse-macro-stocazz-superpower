<p align="center"><b>English</b> · <a href="README.it.md">Italiano</a></p>

<h1 align="center">Mouse Macro Stocazz Superpower</h1>

<p align="center">
Record your mouse, replay it as many times as you need.<br>
A small always-on-top panel for Windows: no installer, no Python to install.
</p>

<p align="center">
<a href="https://github.com/realfulvio/mouse-macro-stocazz-superpower/releases/tag/v0.19.1-beta"><b>⬇ Download for Windows</b></a>
· <a href="GUIDA-ITALIANA.md">Italian guide</a>
· <a href="docs/ESITO-COLLAUDO-v0.19.1.md">Test report</a>
</p>

<p align="center">
<img src="docs/screenshots/v019-compact-real.png" alt="Main panel" width="260">
&nbsp;
<img src="docs/screenshots/v019-playing-real.png" alt="Activity bar while replaying" width="288">
</p>

## What it does

- Records mouse movement, clicks, double clicks, dragging and the scroll wheel, across any program, the desktop and browser toolbars.
- Replays the sequence 1–999 times at normal speed or **2× faster**.
- While recording or replaying, the panel shrinks to a small translucent bar with the counters and a **Stop** button, so it stays out of the way.
- Save and load macros as `.mmr` files.
- Optional **Ctrl+Tab between cycles** to move through browser tabs (off by default; never after the last cycle).
- Records the mouse only: no keyboard keys, no screenshots, no network access.

## Install

1. Download `MouseMacroStocazzSuperpower-Windows-v0.19.1-beta.zip` from the [latest release](https://github.com/realfulvio/mouse-macro-stocazz-superpower/releases/tag/v0.19.1-beta).
2. Extract the **whole** ZIP into a folder.
3. Run `Mouse Macro v0.19.1-beta.exe`.

Requires x64 Windows and .NET Framework 4 (included in Windows 10/11). Python is bundled. The interface is in Italian. The launcher is not code-signed, so Windows SmartScreen may warn on first run; the SHA-256 of the ZIP is published with each release.

## Use

| Step | Action |
|---|---|
| 1 | Arrange the windows you will use and move the panel out of the way |
| 2 | **F9**, perform the mouse sequence, **F9** again |
| 3 | Open **Opzioni** and type the number of repeats (1–999) or use **−/+** / **Preset 20**; pick **Normale** or **Rapida 2×** |
| 4 | Restore the starting state and press **F10** to play |
| – | **F10** or **Stop** stops playback · **Ctrl+Alt+F11** is the global emergency stop |

<p align="center"><img src="docs/screenshots/v019-expanded-real.png" alt="Options expanded" width="560"></p>

**Rapida 2×** speeds up movement and ordinary pauses; waits longer than 2 s stay at 1×, and click holds and double clicks stay protected, so the total time is not exactly halved. **Pagine lente** adds longer, more cautious pauses for slow web pages.

## Good to know

- Replay uses **absolute screen coordinates**. Keep window positions, resolution, monitor layout and Windows scaling the same as when you recorded.
- The panel must not sit on top of a recorded click; the app moves the bar to a free spot or refuses to start.
- The app cannot tell whether a website accepted a click, and it never retries.
- Not covered: UAC / secure desktop and elevated applications.
- Not certified with SentinelOne or Smart App Control. No protection is changed or bypassed.

## Status

Beta. The latest checks are in the [v0.19.1 report](docs/ESITO-COLLAUDO-v0.19.1.md): automated suite of 141 tests (135 passed, 6 Linux-only skipped), package integrity and a real launch of the shipped exe. Physical record/replay was verified on v0.19.0; it has not yet been repeated on v0.19.1, and the report lists exactly what is still open.

## Build from source

```powershell
python -m pip install -r requirements.txt
python -m unittest discover -v
python build_native_windows.py
```

Details in [BUILD-v0.19.1.md](BUILD-v0.19.1.md). The older Linux version (Flet, IT/EN) is in the [v0.14 release](https://github.com/realfulvio/mouse-macro-stocazz-superpower/releases/tag/v0.14-beta).

[All releases](https://github.com/realfulvio/mouse-macro-stocazz-superpower/releases) · [Design notes](docs/design/README.md) · [PolyForm Noncommercial License](LICENSE): free for personal and non-commercial use, no commercial resale · [Third-party notices](THIRD-PARTY-NOTICES.md) · Project and design: **hcok**
