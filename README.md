<p align="center"><b>English</b> · <a href="README.it.md">Italiano</a></p>

# Mouse Macro Stocazz Superpower

Record mouse movement, clicks, dragging and scrolling. Replay the sequence from a compact, expandable Windows window that stays on top. Outfit, horses and the plum, pink, purple and yellow palette follow the approved visual direction.

**[Download v0.17.0 beta for Windows](https://github.com/realfulvio/mouse-macro-stocazz-superpower/releases/tag/v0.17.0-beta)** · Project and design: **hcok**.

![Windows v0.17 panel (Italian UI)](docs/screenshots/v017-compact-100.png)

## Start

1. Download `MouseMacroStocazzSuperpower-Windows-v0.17.0-beta.zip` from the release.
2. Extract the **entire** ZIP folder.
3. Open `Mouse Macro v0.17.0-beta.exe`.

Requires x64 Windows with .NET Framework 4; tested on Windows 11. Python is bundled: no Python installation or first-run download is needed. The launcher is unsigned. The Windows interface is **Italian only**. These screenshots show real controls and counters in the running application.

## Record and replay

1. Activate Chrome or Firefox and move the panel away from the recorded targets.
2. Press **F9**, perform the sequence on one tab, then press **F9** again.
3. Choose repeat count and speed. Press **F10** to play or stop.
4. Use **Ctrl+Alt+F11** for the emergency stop.

**Scheda successiva** sends Ctrl+Tab between cycles. Open the tabs beforehand in the same browser window; activate another window manually. Keep browser position, zoom, screen resolution and scaling consistent with the recording.

![Real Windows application: expanded options at 100%](docs/screenshots/v017-expanded-100.png)

Open **Opzioni** for Save/Load, the 20-repeat preset, speed and **Pagine lente** (slow pages). Help and Emergency remain in the footer. Play and Save are disabled until a valid macro exists. Rapid 2× speeds up movement while preserving long pauses, so total runtime may improve only modestly. Slow-page mode adds more cautious pauses; it does not detect page readiness.

![Real Windows application while recording](docs/screenshots/v017-recording-100.png)

## Tested behavior and limits

The exact new ZIP passed **57 acceptance checks** against its specific hash: Chrome and Firefox, 20 cycles per speed with no lost actions on a local test page, five tabs/two windows, stop and held-button release, native file dialogs, 100%/150% display scaling, and offline startup. Windows unit suite: 102 passed, 6 skipped.

The app sends inputs at recorded coordinates. It cannot confirm a website accepted them and never retries automatically. The new panel does not record keyboard keys, close tabs or repeat infinitely. Real Howrse accounts, SentinelOne and Smart App Control were not tested. See the [full acceptance report](docs/ESITO-COLLAUDO-v0.17.md).

## Linux and development

Linux retains the historical Flet IT/EN interface; this release updates Windows. Linux binaries remain available in [v0.14 beta](https://github.com/realfulvio/mouse-macro-stocazz-superpower/releases/tag/v0.14-beta).

- [Italian guide](GUIDA-ITALIANA.md)
- [v0.17 build and acceptance instructions](BUILD-v0.17.md)
- [All releases](https://github.com/realfulvio/mouse-macro-stocazz-superpower/releases)
- [Approved UI implementation](docs/design/README.md)
- [License](LICENSE)
