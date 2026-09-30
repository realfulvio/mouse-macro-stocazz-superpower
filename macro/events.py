"""Modello dati per gli eventi di una macro e salvataggio/caricamento su file JSON."""
from __future__ import annotations

import json
import math
import os
import tempfile
from dataclasses import asdict, dataclass, field
from pathlib import Path

# Tipi di evento supportati (indipendenti dal backend)
MOVE_REL = "move_rel"    # spostamento relativo (dx, dy) — usato su Linux (evdev)
MOVE_ABS = "move_abs"    # posizione assoluta (x, y) — usato su Windows
LEFT_DOWN = "left_down"
LEFT_UP = "left_up"
RIGHT_DOWN = "right_down"
RIGHT_UP = "right_up"
MIDDLE_DOWN = "middle_down"
MIDDLE_UP = "middle_up"
WHEEL = "wheel"

# Associazione tra evento di rilascio e nome del tasto (usata per il rilascio di sicurezza)
BUTTON_OF_DOWN = {LEFT_DOWN: "left", RIGHT_DOWN: "right", MIDDLE_DOWN: "middle"}
BUTTON_OF_UP = {LEFT_UP: "left", RIGHT_UP: "right", MIDDLE_UP: "middle"}


@dataclass
class MacroEvent:
    t: float                # secondi trascorsi dall'inizio della registrazione
    kind: str
    dx: float = 0.0
    dy: float = 0.0
    x: int = 0
    y: int = 0
    wheel: float = 0.0
    # Ritaglio di schermo attorno al click (solo Windows, zlib+base64): in riproduzione
    # si aspetta che quel punto torni uguale prima di cliccare.
    snap: str = ""


@dataclass
class Macro:
    platform: str            # "linux" o "windows": indica come interpretare gli eventi
    events: list[MacroEvent] = field(default_factory=list)
    # [x, y, larghezza, altezza] del desktop al momento della registrazione (Windows):
    # se in riproduzione è diverso, le coordinate assolute non corrispondono più.
    screen: list[int] = field(default_factory=list)

    def save(self, path: str) -> None:
        data = {
            "platform": self.platform,
            "screen": self.screen,
            "events": [asdict(e) for e in self.events],
        }
        target = Path(path)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=target.parent,
                prefix=".macro-", suffix=".tmp", delete=False,
            ) as f:
                temporary = Path(f.name)
                json.dump(data, f)
            # Sostituisce il file solo dopo aver completato la scrittura.
            os.replace(temporary, target)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)

    @staticmethod
    def load(path: str) -> "Macro":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict) or data.get("platform") not in ("windows", "linux"):
            raise ValueError("Il file non contiene una macro Windows o Linux valida.")
        screen = data.get("screen", [])
        if not isinstance(screen, list) or (screen and (
            len(screen) != 4 or any(type(n) is not int for n in screen)
            or screen[2] <= 0 or screen[3] <= 0
        )):
            raise ValueError("Le dimensioni dello schermo nella macro non sono valide.")
        if not isinstance(data.get("events"), list):
            raise ValueError("La macro deve contenere una lista di eventi.")
        events = [MacroEvent(**e) for e in data["events"]]
        kinds = set(BUTTON_OF_DOWN) | set(BUTTON_OF_UP) | {WHEEL}
        kinds.add(MOVE_ABS if data["platform"] == "windows" else MOVE_REL)
        previous = 0.0
        for event in events:
            values = (event.t, event.dx, event.dy, event.x, event.y, event.wheel)
            if any(isinstance(n, bool) or not isinstance(n, (int, float))
                   or not math.isfinite(n) for n in values):
                raise ValueError("La macro contiene coordinate o tempi non validi.")
            if event.t < previous:
                raise ValueError("Gli eventi della macro devono avere tempi crescenti o uguali.")
            if event.kind not in kinds or not isinstance(event.snap, str):
                raise ValueError("La macro contiene un tipo di evento non valido.")
            previous = event.t
        return Macro(platform=data["platform"], events=events, screen=screen)
