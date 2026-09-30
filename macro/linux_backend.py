"""Backend Linux: legge gli eventi grezzi del mouse via evdev (funziona sia su X11 sia
su Wayland, perché opera sotto il compositor) e li riproduce creando un mouse virtuale
tramite uinput. Il mouse è un dispositivo a movimento RELATIVO: non esiste un modo
generico e sicuro per leggere/impostare la posizione assoluta del cursore su Wayland,
quindi la riproduzione parte sempre dalla posizione attuale del cursore al momento
della riproduzione (esattamente come farebbe una persona che sposta di nuovo il mouse).
"""
from __future__ import annotations

import select
import threading

from evdev import InputDevice, UInput, ecodes, list_devices

from .events import (
    LEFT_DOWN,
    LEFT_UP,
    MIDDLE_DOWN,
    MIDDLE_UP,
    MOVE_REL,
    RIGHT_DOWN,
    RIGHT_UP,
    WHEEL,
    MacroEvent,
)

VIRTUAL_DEVICE_NAME = "MouseMacroStudio Virtual Mouse"


def list_mice() -> list[tuple[str, str]]:
    """Elenca i dispositivi che sembrano un mouse (hanno tasti e assi relativi X/Y),
    escludendo il mouse virtuale creato da questa stessa applicazione."""
    mice: list[tuple[str, str]] = []
    for path in list_devices():
        try:
            dev = InputDevice(path)
        except OSError:
            continue
        caps = dev.capabilities()
        keys = caps.get(ecodes.EV_KEY, [])
        rels = caps.get(ecodes.EV_REL, [])
        if ecodes.BTN_LEFT in keys and ecodes.REL_X in rels and ecodes.REL_Y in rels:
            if dev.name != VIRTUAL_DEVICE_NAME:
                mice.append((path, dev.name))
        dev.close()
    return mice


class LinuxRecorder:
    def __init__(self, device_path: str):
        self.device_path = device_path
        self._thread: threading.Thread | None = None
        self._events: list[MacroEvent] = []
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._base_ts: float | None = None
        self._pending_dx = 0
        self._pending_dy = 0
        self._device: InputDevice | None = None

    def start(self) -> None:
        # Open synchronously so permission/missing-device errors reach the UI.
        self._device = InputDevice(self.device_path)
        self._events = []
        self._base_ts = None
        self._pending_dx = 0
        self._pending_dy = 0
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        try:
            self._thread.start()
        except Exception:
            self._device.close()
            self._device = None
            raise

    def _run(self) -> None:
        dev = self._device
        try:
            while not self._stop.is_set():
                r, _, _ = select.select([dev.fd], [], [], 0.2)
                if not r:
                    continue
                for event in dev.read():
                    self._handle(event)
        except OSError:
            pass
        finally:
            dev.close()
            self._device = None

    def _handle(self, event) -> None:
        if self._base_ts is None:
            self._base_ts = event.timestamp()
        t = event.timestamp() - self._base_ts

        if event.type == ecodes.EV_REL:
            if event.code == ecodes.REL_X:
                self._pending_dx += event.value
            elif event.code == ecodes.REL_Y:
                self._pending_dy += event.value
            elif event.code == ecodes.REL_WHEEL:
                self._flush_move(t)
                self._append(MacroEvent(t=t, kind=WHEEL, wheel=float(event.value)))
        elif event.type == ecodes.EV_KEY and event.value in (0, 1):
            self._flush_move(t)
            kind = {
                ecodes.BTN_LEFT: (LEFT_DOWN, LEFT_UP),
                ecodes.BTN_RIGHT: (RIGHT_DOWN, RIGHT_UP),
                ecodes.BTN_MIDDLE: (MIDDLE_DOWN, MIDDLE_UP),
            }.get(event.code)
            if kind:
                self._append(MacroEvent(t=t, kind=kind[0] if event.value == 1 else kind[1]))
        elif event.type == ecodes.EV_SYN and event.code == ecodes.SYN_REPORT:
            self._flush_move(t)

    def _flush_move(self, t: float) -> None:
        if self._pending_dx or self._pending_dy:
            self._append(MacroEvent(t=t, kind=MOVE_REL, dx=float(self._pending_dx), dy=float(self._pending_dy)))
            self._pending_dx = 0
            self._pending_dy = 0

    def _append(self, evt: MacroEvent) -> None:
        with self._lock:
            self._events.append(evt)

    def stop(self) -> list[MacroEvent]:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=1.0)
        with self._lock:
            return list(self._events)

    @property
    def current_event_count(self) -> int:
        with self._lock:
            return len(self._events)


_CAPABILITIES = {
    ecodes.EV_KEY: [ecodes.BTN_LEFT, ecodes.BTN_RIGHT, ecodes.BTN_MIDDLE],
    ecodes.EV_REL: [ecodes.REL_X, ecodes.REL_Y, ecodes.REL_WHEEL],
}


class LinuxPlayer:
    def __init__(self):
        self._ui: UInput | None = None

    def _ensure(self) -> UInput:
        if self._ui is None:
            self._ui = UInput(_CAPABILITIES, name=VIRTUAL_DEVICE_NAME)
        return self._ui

    def apply_event(self, evt: MacroEvent) -> None:
        ui = self._ensure()
        if evt.kind == MOVE_REL:
            if evt.dx:
                ui.write(ecodes.EV_REL, ecodes.REL_X, int(evt.dx))
            if evt.dy:
                ui.write(ecodes.EV_REL, ecodes.REL_Y, int(evt.dy))
            ui.syn()
        elif evt.kind == LEFT_DOWN:
            self._button(ecodes.BTN_LEFT, 1)
        elif evt.kind == LEFT_UP:
            self._button(ecodes.BTN_LEFT, 0)
        elif evt.kind == RIGHT_DOWN:
            self._button(ecodes.BTN_RIGHT, 1)
        elif evt.kind == RIGHT_UP:
            self._button(ecodes.BTN_RIGHT, 0)
        elif evt.kind == MIDDLE_DOWN:
            self._button(ecodes.BTN_MIDDLE, 1)
        elif evt.kind == MIDDLE_UP:
            self._button(ecodes.BTN_MIDDLE, 0)
        elif evt.kind == WHEEL:
            ui.write(ecodes.EV_REL, ecodes.REL_WHEEL, int(evt.wheel))
            ui.syn()

    def _button(self, code: int, value: int) -> None:
        ui = self._ensure()
        ui.write(ecodes.EV_KEY, code, value)
        ui.syn()

    def release_held(self, held: set[str]) -> None:
        mapping = {"left": ecodes.BTN_LEFT, "right": ecodes.BTN_RIGHT, "middle": ecodes.BTN_MIDDLE}
        for name in held:
            code = mapping.get(name)
            if code is not None:
                self._button(code, 0)

    def close(self) -> None:
        if self._ui is not None:
            self._ui.close()
            self._ui = None
