"""Macro avviabile: un file .cmd accanto al file .mmr, senza nessun exe nuovo.

Il .cmd cerca Mouse Macro installato sul PC (cartella `Portable` dell'utente) e gli
chiede di riprodurre la macro con `--run`. Non contiene codice eseguibile nuovo: parte
il Python ufficiale firmato già presente, quindi SmartScreen, Smart App Control e gli
antivirus non vedono nessun file sconosciuto da valutare. Il prezzo è che sul PC di
destinazione deve esserci Mouse Macro (versione con `--run`).
"""
from __future__ import annotations

import re
from pathlib import Path, PureWindowsPath

from .events import Macro

PACKAGE_PREFIX = "MouseMacroStocazzSuperpower-Windows-v"
_UNSAFE = re.compile(r"[^A-Za-z0-9 _.()\-]")


def safe_stem(name: str) -> str:
    """Nome file sicuro dentro un .cmd: niente % ! & ^ e altri caratteri speciali."""
    stem = _UNSAFE.sub("_", PureWindowsPath(str(name)).stem).strip(" .") or "macro"
    return stem[:80]


def _flags(repeats, speed, slow, human, next_tab, infinite=False) -> str:
    if not infinite and (type(repeats) is not int or not 1 <= repeats <= 999):
        raise ValueError("Imposta da 1 a 999 ripetizioni.")
    if speed not in (1, 2, 1.0, 2.0):
        raise ValueError("Velocità non valida.")
    parts = ["--infinite" if infinite else f"--repeat {repeats}", f"--speed {int(speed)}"]
    parts += [flag for flag, on in (("--slow", slow), ("--human", human), ("--next-tab", next_tab)) if on]
    return " ".join(parts)


def launcher_text(stem: str, repeats: int = 1, speed: float = 1, slow=False, human=False, next_tab=False,
                  infinite=False) -> str:
    stem = safe_stem(stem)
    flags = _flags(repeats, speed, slow, human, next_tab, infinite)
    lines = [
        "@echo off",
        "rem Macro avviabile creata da Mouse Macro Stocazz Superpower.",
        "rem Non contiene programmi: usa Mouse Macro installato su questo PC.",
        "setlocal",
        'set "BASE=%LOCALAPPDATA%\\MouseMacroStocazzSuperpower\\Portable"',
        'set "APP="',
        f"for /f \"delims=\" %%D in ('dir /b /ad /o:n \"%BASE%\\{PACKAGE_PREFIX}*\" 2^>nul') do "
        'if exist "%BASE%\\%%D\\app\\macro\\runner.py" if exist "%BASE%\\%%D\\runtime\\pythonw.exe" set "APP=%BASE%\\%%D"',
        "if not defined APP goto manca",
        f'start "" "%APP%\\runtime\\pythonw.exe" -B "%APP%\\app\\windows_main.py" --run "%~dp0{stem}.mmr" {flags}',
        "exit /b 0",
        ":manca",
        "echo Mouse Macro Stocazz Superpower non e' installato su questo PC,",
        "echo oppure la versione installata e' troppo vecchia per le macro avviabili.",
        "echo Scaricalo da https://github.com/realfulvio/mouse-macro-stocazz-superpower/releases/latest",
        "pause",
        "exit /b 1",
        "",
    ]
    return "\r\n".join(lines)


def linux_script_text(stem: str, repeats: int = 1, speed: float = 1, slow=False, human=False, next_tab=False,
                      infinite=False) -> str:
    """Script .sh: apre Mouse Macro (installato con install.sh) con la macro già caricata.
    Su Linux non parte da solo: mouse e tastiera vanno consegnati a un programma che gira
    senza finestra, quindi l'ultimo passo (F10) resta tuo."""
    stem = safe_stem(stem)
    flags = _flags(repeats, speed, slow, human, next_tab, infinite)
    lines = [
        "#!/usr/bin/env bash",
        "# Macro avviabile creata da Mouse Macro Stocazz Superpower.",
        "# Apre Mouse Macro con la macro caricata: premi F10 (o Riproduci) per avviarla.",
        'DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"',
        'ROOT="${XDG_DATA_HOME:-$HOME/.local/share}/MouseMacroStocazzSuperpower/current"',
        'for BIN in "$ROOT/MouseMacroStocazzSuperpower-Linux-IT" "$ROOT/MouseMacroStocazzSuperpower-Linux-EN"; do',
        f'    if [[ -x "$BIN" ]]; then exec "$BIN" --open "$DIR/{stem}.mmr" {flags}; fi',
        "done",
        'MESSAGE="Mouse Macro Stocazz Superpower non e'"'"' installato con install.sh su questo PC."',
        'if command -v notify-send >/dev/null 2>&1; then notify-send "Mouse Macro" "$MESSAGE"; fi',
        'echo "$MESSAGE" >&2',
        "echo \"Con l'AppImage: ./MouseMacroStocazzSuperpower-Linux.AppImage --open '$DIR/" + stem + ".mmr' " + flags + "\" >&2",
        "exit 1",
        "",
    ]
    return "\n".join(lines)


def export_launcher(macro: Macro, chosen_path, repeats: int = 1, speed: float = 1,
                    slow=False, human=False, next_tab=False, infinite=False,
                    platform: str = "windows") -> tuple[Path, Path]:
    """Scrive `<nome>.mmr` più `<nome>.cmd` (Windows) o `<nome>.sh` (Linux) nella cartella scelta.
    Ritorna (script, mmr)."""
    chosen = Path(chosen_path)
    stem = safe_stem(chosen.name)
    if platform == "linux":
        text = linux_script_text(stem, repeats, speed, slow, human, next_tab, infinite)
        script = chosen.with_name(stem + ".sh")
        payload = text.encode("ascii")
    else:
        text = launcher_text(stem, repeats, speed, slow, human, next_tab, infinite)
        script = chosen.with_name(stem + ".cmd")
        payload = text.encode("ascii")
    mmr = chosen.with_name(stem + ".mmr")
    macro.save(str(mmr))
    script.write_bytes(payload)
    if platform == "linux":
        script.chmod(0o755)
    return script, mmr
