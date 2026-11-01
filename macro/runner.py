"""Riproduzione di una macro avviabile: `windows_main.py --run macro.mmr --repeat N ...`.

Niente pannello: una domanda di conferma, poi la riproduzione. Ctrl+Alt+F11 ferma tutto.
Se quel tasto non si può registrare (per esempio il pannello è aperto) non parte nulla.
"""
from __future__ import annotations

import sys
import threading
from dataclasses import dataclass
from pathlib import Path

TITLE = "Mouse Macro Stocazz Superpower"


@dataclass(frozen=True)
class RunRequest:
    path: str
    repeats: int = 1
    speed: int = 1
    slow: bool = False
    human: bool = False
    next_tab: bool = False
    infinite: bool = False


def parse_run_args(argv: list[str], flag: str = "--run") -> RunRequest:
    """Legge gli argomenti dopo `--run` (Windows) o `--open` (Linux). Solleva ValueError se qualcosa non torna."""
    args = list(argv)
    try:
        path = args[args.index(flag) + 1]
    except (ValueError, IndexError):
        raise ValueError(f"Manca il file della macro dopo {flag}.") from None
    if not path.lower().endswith(".mmr"):
        raise ValueError("Il file della macro deve essere un .mmr.")

    def number(flag: str, default: int) -> int:
        if flag not in args:
            return default
        try:
            return int(args[args.index(flag) + 1])
        except (ValueError, IndexError):
            raise ValueError(f"Valore non valido per {flag}.") from None

    repeats, speed = number("--repeat", 1), number("--speed", 1)
    if not 1 <= repeats <= 999:
        raise ValueError("Le ripetizioni vanno da 1 a 999.")
    if speed not in (1, 2):
        raise ValueError("La velocità può essere 1 o 2.")
    return RunRequest(path, repeats, speed, "--slow" in args, "--human" in args, "--next-tab" in args,
                      "--infinite" in args)


def run_from_argv(argv: list[str]) -> int:
    import ctypes

    from .engine import LoopMode, PlaybackOptions
    from .session import Session, State
    from .windows_backend import (HOTKEY_EMERGENCY, GlobalHotkeys, WindowsPlayer,
                                  screen_geometry)

    user32 = ctypes.windll.user32

    def box(text: str, flags: int) -> int:
        return user32.MessageBoxW(None, text, TITLE, flags | 0x40000)  # MB_TOPMOST

    try:
        request = parse_run_args(argv)
        name = Path(request.path).stem
        done = threading.Event()
        session = Session(None, WindowsPlayer, done.set, screen_geometry)
        if not session.load(request.path):
            raise ValueError(session.message)
        times = "all’infinito (finché non la fermi)" if request.infinite else f"{request.repeats} volte"
        if box(f"Riprodurre la macro «{name}» {times}?\n\n"
               "Le finestre devono essere come quando l’hai registrata.\n"
               "Per fermare in qualsiasi momento: Ctrl+Alt+F11.", 0x21) != 1:  # OK/Annulla
            return 0
        hotkeys = GlobalHotkeys(lambda _id: session.request_stop(), ids=(HOTKEY_EMERGENCY,))
        hotkeys.start()
        if hotkeys.failed:
            hotkeys.stop()
            raise ValueError("Ctrl+Alt+F11 è occupato (il pannello di Mouse Macro è aperto?). "
                             "Chiudilo e riprova: senza lo stop di emergenza non parto.")
        try:
            options = PlaybackOptions(
                mode=LoopMode.INFINITE if request.infinite else LoopMode.REPEAT_COUNT,
                repeat_count=None if request.infinite else request.repeats, speed=request.speed,
                pause_threshold_seconds=.35 if request.slow else 2.0,
                max_pause_speedup=1.0, min_click_hold_seconds=.12,
                min_action_gap_seconds=1.2 if request.slow else .65 / request.speed,
                double_click_seconds=user32.GetDoubleClickTime() / 1000,
                double_click_gap_seconds=.08, protect_wheel_actions=True, humanize=request.human)

            def preflight(macro):
                if macro.screen and macro.screen != screen_geometry():
                    raise ValueError("Schermo o monitor diversi da quando hai registrato la macro.")

            session.toggle_play(options, request.next_tab, preflight)
            while session.state in (State.PLAYING, State.STOPPING):
                done.wait(0.2)
                done.clear()
            if session.state == State.ERROR:
                raise ValueError(session.message)
        finally:
            hotkeys.stop()
            session.close()
        return 0
    except Exception as error:
        box(str(error), 0x10)
        return 1


if __name__ == "__main__":
    sys.exit(run_from_argv(sys.argv[1:]))
