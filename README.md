# Mouse Macro Stocazz Superpower

**Record your mouse once, replay it as many times as you like, without losing clicks.**
A small desktop app for Windows and Linux, in English and Italian.

**v0.14 beta · powered by hcok** · [Italiano](README.it.md) · [Download](#download) · [Build](docs/BUILD.md) · [Validation](COLLAUDO.md)

<p>
<img src="docs/screenshots/main-en.png" width="300" alt="Main window">
<img src="docs/screenshots/settings-en.png" width="300" alt="Settings">
<img src="docs/screenshots/help-en.png" width="300" alt="How to use">
</p>

## Why it exists

It started from a very concrete, very repetitive job: a browser game played across
twenty-odd tabs, where every tab needs the same sequence of clicks, every day.
Existing macro tools could do it at normal speed, but **as soon as playback was
sped up they started losing clicks**: presses got so short, or so close together,
that the page ignored them.

So this app was built around two ideas:

1. **Record faithfully and replay exactly**: absolute cursor positions, real click
   timing, DPI-aware coordinates. Replay forever, N times, or for a set duration.
2. **Go faster without losing clicks**: a *minimum click duration* (150 ms by default,
   in line with a normal human click)
   protects both how long each click is held and the pause before the next one,
   at any speed.

## What it does

- Records mouse movement, left/right/middle clicks and scrolling.
- Replays **indefinitely**, **N times** (e.g. one cycle per open tab) or for a **duration**.
- Speed from 0.1× to 3×; the minimum click/pause duration is always respected, and long
  waits (page loads) are accelerated by at most 1.5×.
- Global shortcuts that also work from the browser: **F9** record/stop, **F10** play/stop,
  **Ctrl+Alt+F11** emergency stop (Windows; on Linux they need the app window focused).
- **Wait for page** (Windows, on by default, on the main screen): before each click, wait
  until the button looks as it did while recording, then click at once. No time is lost when
  the page is ready; it covers pages that update after every click and tabs opened in the
  background, which browsers only load when shown. Only the button itself is compared, so the
  horse's picture and name around it can change. If a page is not ready within 10 s (adjustable),
  playback stops and says which click was waiting.
- Optional, off by default:
  - **Close the tab after each cycle** (Ctrl+W), so the browser moves on to the next tab;
  - **Vary timing each cycle** (experimental).
- Save and load macros (`.mmr`), with checks on the screen layout: a macro recorded at a
  different resolution won't start clicking in the wrong places.

## Download

Get the latest version from the [Releases page](../../releases/latest):

| System | Download | How to start |
| --- | --- | --- |
| **Windows 10/11 (recommended)** | `MouseMacroStocazzSuperpower-Windows-Portable.zip` | Extract it, then double-click `Mouse Macro Stocazz Superpower.exe` (Italian) or `Mouse Macro Stocazz Superpower (English).exe` |
| Windows, single file | `MouseMacroStocazzSuperpower-Windows-EN.exe` / `-IT.exe` | Double-click (may be blocked by Smart App Control, see below) |
| Linux x86_64 | `MouseMacroStocazzSuperpower-Linux-EN.tar.gz` / `-IT.tar.gz` | Extract and run |

`SHA256SUMS.txt` in each release lets you verify the files. Nothing to install.

### Windows: why the portable version

**Smart App Control** (Windows 11) blocks programs that Microsoft's cloud does not know,
unless they are code-signed. This project's own executables are not signed yet, so on a PC
with Smart App Control **on** the single-file `.exe` may be blocked ("An Application Control
policy has blocked this file"): the verdict can even differ from one build to the next.

The **portable version** avoids the problem: it contains no new executable code. The two files
you double-click are the official `pythonw.exe` from python.org, renamed (the Python Software
Foundation signature does not depend on the file name); all the other binaries are the official,
signed Python ones plus standard libraries from PyPI; the program itself is plain `.py` files.
It was tested on Windows 11 with Smart App Control on, downloaded from the internet and
extracted with File Explorer: no blocks. It shows the Python icon because it *is* Python.

The interface opens in a **Microsoft Edge window in app mode** (no address bar, no tabs: it
looks like a normal program window). It is served only to this computer (`127.0.0.1`, on a
random secret path), everything it needs is included, and closing the window closes the program.

The first time, SmartScreen may show **"Windows protected your PC"** for the single-file `.exe`:
click **More info → Run anyway**. PCs managed by a company or school may block any unapproved
program regardless: in that case ask the administrator.

### Linux

Extract the archive and run the executable (`chmod +x` it if needed). It needs GTK 3 and
Zenity, read access to the mouse under `/dev/input` for recording and write access to
`/dev/uinput` for playback. Use your distribution's usual permission setup (e.g. the
`input` group or a udev rule): **do not run the app as root**. On Linux, movements are
replayed relative to where the cursor starts.

## How to use

<img src="docs/screenshots/help-en.png" width="280" align="right" alt="How to use">

1. Open all the browser tabs you need and switch to the first one.
2. Press **F9** and do the job by hand, calmly, with the page already loaded.
3. Press **F9** again to stop.
4. Under **Repeat** choose **N times** and type how many tabs you opened.
5. Go back to the first tab and press **F10**. To stop: **F10**, or **Ctrl+Alt+F11**.

To keep clicks accurate: don't move, resize or zoom the browser between recording and
playback, don't touch the mouse during playback, and record with pages fully loaded.
Use **Save macro** to reuse a recording on the following days.

<br clear="right">

## Version history

| Version | Date | Highlights |
| --- | --- | --- |
| v0.14 beta | 30/09/2026 | Minimum click 150 ms (was 50); *Wait for page* on by default, on the main screen, ignoring the horse's picture around the button; **portable version** that works with Smart App Control; Edge app window instead of the unsigned `flet.exe`; native Windows open/save dialogs; fonts bundled for offline use; 38 MB instead of 64 MB; MIT licence; automated builds |
| — | 30/09/2026 | Linux: F9/F10 shortcuts and tab closing |
| [v0.13 beta](../../releases/tag/v0.13-beta) | 30/09/2026 | English version; safer load/save; self-test diagnostics; Windows and Linux builds |
| v0.4 | 30/09/2026 | First reliable Windows build: DPI awareness, minimum pause between clicks, global shortcuts, *Wait for page*, *Close tab* |
| first version | 29/09/2026 | Record and replay on Linux and Windows |

The full history is in the [commits](../../commits/main).

## Build from source

See [docs/BUILD.md](docs/BUILD.md). In short: `pip install -r requirements.txt pyinstaller`,
then `python build_release.py` builds both languages for the OS you run it on. Releases are
built automatically by [GitHub Actions](.github/workflows/release.yml) when a `v*` tag is pushed.

## Licence

[MIT](LICENSE) © hcok. Bundled fonts: Outfit and a one-glyph subset of Noto Color Emoji,
both under the SIL Open Font License.

Project and design: **hcok**. Developed with assistance from Claude and Codex.
