<p align="center"><b>🇬🇧 English</b> &nbsp;·&nbsp; <a href="README.it.md"><b>🇮🇹 Leggi in italiano</b></a></p>

<h1 align="center">Mouse Macro Stocazz Superpower</h1>

<p align="center">Record your mouse clicks once. Replay them accurately, as many times as you need.</p>

<p align="center"><b>Windows users: download the Portable ZIP.</b> No installation required.</p>

<p align="center"><a href="https://github.com/realfulvio/mouse-macro-stocazz-superpower/releases/tag/v0.15.1-beta"><b>⬇ Download the latest release</b></a></p>

<p align="center">
<img src="docs/screenshots/main-en.png" width="520" alt="Main window">
</p>

<p align="center">
<img src="docs/screenshots/settings-en.png" width="260" alt="Settings">
&nbsp;
<img src="docs/screenshots/help-en.png" width="260" alt="Built-in help">
</p>

## What it does

- Records mouse movement, clicks and scrolling.
- Replays a macro once, a set number of times or continuously.
- Supports English and Italian, with keyboard shortcuts to record and play.
- Saves recordings so you can use them again.

## Download

Open the **[latest release](https://github.com/realfulvio/mouse-macro-stocazz-superpower/releases/tag/v0.15.1-beta)** and choose the file for your system:

| Your system | Download this file |
| --- | --- |
| **Windows 10/11 — recommended** | **`MouseMacroStocazzSuperpower-Windows-Portable.zip`** |
| Linux x86_64 — v0.14 beta ([previous release](../../releases/tag/v0.14-beta)) | `MouseMacroStocazzSuperpower-Linux-EN.tar.gz` or `-IT.tar.gz` |

### Windows: use the portable version

1. Download `MouseMacroStocazzSuperpower-Windows-Portable.zip`.
2. Extract the ZIP.
3. Open the extracted folder and double-click **`Mouse Macro Stocazz Superpower.exe`** for Italian or **`Mouse Macro Stocazz Superpower (English).exe`** for English.

The portable version needs no installer. It is the recommended choice for Windows. This v0.15 beta release contains the Windows portable package; older single-file builds remain in previous releases.

## Quick start

1. Open the app and the page where you want to use the macro.
2. Press **F9**, perform the actions, then press **F9** again.
3. Press **F10** to play. Use **F10** again to stop.

Keep the screen layout unchanged between recording and playback. More details and troubleshooting are in the in-app help.

## v0.15 beta

Click hold time and the pause after release are independent. Longer recorded pauses are protected at high playback speed. Playback stops on focus loss or an obscured target and never retries clicks automatically. Optional diagnostics record sent inputs, without claiming that a website accepted them.

85 automated tests passed (6 Linux tests skipped) and 20 native Windows checks passed on a controlled local target. Howrse was not accessed. Native UI file dialogs and real browser tab cycling remain unverified; see [test results](docs/ESITO-COLLAUDO-v0.15.md).

## More

- [All releases](../../releases)
- [Build from source](docs/BUILD.md)
- [Licence](LICENSE)

Project and design: **hcok**.

## v0.15.1 beta

Turn off 'Check the click target window' on the main screen to replay at recorded coordinates without checking the initial target, foreground window or overlays. Visual matching is independent: turn off 'Compare the button before clicking' to skip it too.
