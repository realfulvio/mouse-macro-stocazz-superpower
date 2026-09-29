"""Backend Windows: usa pynput, che internamente si appoggia agli hook nativi di basso
livello di Windows (SetWindowsHookEx / SendInput) — permette di registrare e riprodurre
posizioni ASSOLUTE del cursore, cosa che su Windows non ha le restrizioni di sicurezza
presenti su Wayland.

NOTA: questo backend non è stato testato su una vera macchina Windows in questa sessione
(l'ambiente di sviluppo è Linux); pynput è però una libreria matura e ampiamente usata
per questo scopo su Windows.
"""
from __future__ import annotations

import threading
import time

from pynput import mouse

from .events import (
    LEFT_DOWN,
    LEFT_UP,
    MIDDLE_DOWN,
    MIDDLE_UP,
    MOVE_ABS,
    RIGHT_DOWN,
    RIGHT_UP,
    WHEEL,
    MacroEvent,
)

_CLICK_KIND = {
    (mouse.Button.left, True): LEFT_DOWN,
    (mouse.Button.left, False): LEFT_UP,
    (mouse.Button.right, True): RIGHT_DOWN,
    (mouse.Button.right, False): RIGHT_UP,
    (mouse.Button.middle, True): MIDDLE_DOWN,
    (mouse.Button.middle, False): MIDDLE_UP,
}


class WindowsRecorder:
    def __init__(self):
        self._events: list[MacroEvent] = []
        self._lock = threading.Lock()
        self._listener: mouse.Listener | None = None
        self._base_t: float | None = None

    def start(self) -> None:
        self._events = []
        self._base_t = None
        self._listener = mouse.Listener(
            on_move=self._on_move, on_click=self._on_click, on_scroll=self._on_scroll
        )
        self._listener.start()

    def _now(self) -> float:
        t = time.perf_counter()
        if self._base_t is None:
            self._base_t = t
        return t - self._base_t

    def _append(self, evt: MacroEvent) -> None:
        with self._lock:
            self._events.append(evt)

    def _on_move(self, x, y) -> None:
        self._append(MacroEvent(t=self._now(), kind=MOVE_ABS, x=int(x), y=int(y)))

    def _on_click(self, x, y, button, pressed) -> None:
        kind = _CLICK_KIND.get((button, pressed))
        if kind:
            self._append(MacroEvent(t=self._now(), kind=kind, x=int(x), y=int(y)))

    def _on_scroll(self, x, y, dx, dy) -> None:
        self._append(MacroEvent(t=self._now(), kind=WHEEL, x=int(x), y=int(y), wheel=float(dy)))

    def stop(self) -> list[MacroEvent]:
        if self._listener:
            self._listener.stop()
            self._listener = None
        with self._lock:
            return list(self._events)

    @property
    def current_event_count(self) -> int:
        with self._lock:
            return len(self._events)


class WindowsPlayer:
    def __init__(self):
        self._ctrl = mouse.Controller()

    def apply_event(self, evt: MacroEvent) -> None:
        if evt.kind == MOVE_ABS:
            self._ctrl.position = (evt.x, evt.y)
        elif evt.kind == LEFT_DOWN:
            self._ctrl.position = (evt.x, evt.y)
            self._ctrl.press(mouse.Button.left)
        elif evt.kind == LEFT_UP:
            self._ctrl.position = (evt.x, evt.y)
            self._ctrl.release(mouse.Button.left)
        elif evt.kind == RIGHT_DOWN:
            self._ctrl.position = (evt.x, evt.y)
            self._ctrl.press(mouse.Button.right)
        elif evt.kind == RIGHT_UP:
            self._ctrl.position = (evt.x, evt.y)
            self._ctrl.release(mouse.Button.right)
        elif evt.kind == MIDDLE_DOWN:
            self._ctrl.position = (evt.x, evt.y)
            self._ctrl.press(mouse.Button.middle)
        elif evt.kind == MIDDLE_UP:
            self._ctrl.position = (evt.x, evt.y)
            self._ctrl.release(mouse.Button.middle)
        elif evt.kind == WHEEL:
            self._ctrl.position = (evt.x, evt.y)
            self._ctrl.scroll(0, evt.wheel)

    def release_held(self, held: set[str]) -> None:
        mapping = {"left": mouse.Button.left, "right": mouse.Button.right, "middle": mouse.Button.middle}
        for name in held:
            btn = mapping.get(name)
            if btn:
                self._ctrl.release(btn)

    def close(self) -> None:
        pass
