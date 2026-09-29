"""Modello dati per gli eventi di una macro e salvataggio/caricamento su file JSON."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field

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


@dataclass
class Macro:
    platform: str            # "linux" o "windows": indica come interpretare gli eventi
    events: list[MacroEvent] = field(default_factory=list)

    def save(self, path: str) -> None:
        data = {
            "platform": self.platform,
            "events": [asdict(e) for e in self.events],
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    @staticmethod
    def load(path: str) -> "Macro":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        events = [MacroEvent(**e) for e in data["events"]]
        return Macro(platform=data["platform"], events=events)
