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


def _flags(repeats, speed, slow, human, next_tab) -> str:
    if type(repeats) is not int or not 1 <= repeats <= 999:
        raise ValueError("Imposta da 1 a 999 ripetizioni.")
    if speed not in (1, 2, 1.0, 2.0):
        raise ValueError("Velocità non valida.")
    parts = [f"--repeat {repeats}", f"--speed {int(speed)}"]
    parts += [flag for flag, on in (("--slow", slow), ("--human", human), ("--next-tab", next_tab)) if on]
    return " ".join(parts)


def launcher_text(stem: str, repeats: int = 1, speed: float = 1, slow=False, human=False, next_tab=False) -> str:
    stem = safe_stem(stem)
    flags = _flags(repeats, speed, slow, human, next_tab)
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


def export_launcher(macro: Macro, chosen_path, repeats: int = 1, speed: float = 1,
                    slow=False, human=False, next_tab=False) -> tuple[Path, Path]:
    """Scrive `<nome>.mmr` e `<nome>.cmd` nella cartella scelta. Ritorna (cmd, mmr)."""
    chosen = Path(chosen_path)
    stem = safe_stem(chosen.name)
    text = launcher_text(stem, repeats, speed, slow, human, next_tab)  # valida prima di scrivere
    mmr = chosen.with_name(stem + ".mmr")
    cmd = chosen.with_name(stem + ".cmd")
    macro.save(str(mmr))
    cmd.write_bytes(text.encode("ascii"))
    return cmd, mmr
