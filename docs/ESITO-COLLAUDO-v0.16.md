# Windows v0.16 — acceptance results

Validation date: 2026-10-04. Tested artifact: `MouseMacroStocazzSuperpower-Windows-v0.16.0-beta-by-codex.zip` (11,551,493 bytes).

SHA256: `ebb488c8b58a0183d22702f6fa935350784a8806fd1e475ed58f645bfdbee4f2`.

The exact ZIP was extracted and its launcher started on an interactive Windows 11 x64 desktop. No product rebuild followed acceptance. Selenium prepared a local test page and read DOM counters; recording and replay used native mouse input. No real Howrse account was used.

## Results

41 acceptance checks passed across the recorded runs. Windows unit tests: 108 total, 102 passed, 6 Linux-specific tests skipped. Earlier failed attempts involved the acceptance harness; the final checks use the same artifact SHA256.

| Browser (100% scaling) | Normal: 20 cycles | Rapid: 20 cycles | Verified totals per speed |
| --- | ---: | ---: | --- |
| Chrome 154.0.8037.98 | 98.37 s | 93.13 s | 20 A, 20 B, 20 double clicks, 20 drags, 20 wheel events; zero lost |
| Firefox 157.0 | 97.16 s | 92.18 s | 20 A, 20 B, 20 double clicks, 20 drags, 20 wheel events; zero lost |

Each run also verified 40 single-click events belonging to the double clicks and 20 drag down/up pairs. Rapid mode protects pauses; these results do not imply a 2× gain for the complete task.

- Five tabs in one window received exactly one A/B pair each. A second window stayed untouched until manually activated. All tabs remained open.
- F10, panel Stop and emergency Stop interrupted a ten-second pause/held drag. Measured stop latencies ranged from 11.36 to 46.51 ms in this environment.
- Closing the panel during a held native button released it and exited successfully (60.63 ms measured).
- Focus loss and obscured targets stopped replay; save/load dialogs, invalid-file preservation, global F9/F10 and single-instance behavior passed.
- At actual 150% scaling (144 DPI, 1920×1200), each browser passed two cycles per speed with complete gestures and the five-tab/two-window flow. No actions were lost.
- A simulated 900 ms page delay intentionally lost one action with standard pauses. Slow-page mode completed 20 A/B pairs without losses in each browser. This demonstrates a fixed-delay limit, not automatic readiness detection.
- Offline startup succeeded in 0.78 s while the VM network link was disconnected. The child process ran from the bundled `runtime/pythonw.exe`, with Python removed from PATH. Python was installed for the test harness; this is not a pristine no-Python-installation test.

## Limits

Windows UI is Italian only. No keyboard recording, infinite/duration mode, random timing, tab closing, visual comparison or automatic click retry in the new panel. Ctrl+Tab is sent between cycles, never after the last cycle. Old recordings without DPI metadata are accepted only at 100% scaling.

No certification for Howrse account behavior, corporate policies, SentinelOne, Smart App Control, ARM, UAC/elevation, multiple monitors or mixed-DPI displays. An unsigned launcher may be handled differently by security policies. Screen coordinates still require unchanged layout and sufficient recorded pauses.
