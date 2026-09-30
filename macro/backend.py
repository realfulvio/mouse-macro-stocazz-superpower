"""Selezione del backend di sistema corretto in base al sistema operativo."""
from __future__ import annotations

import sys


def current_platform() -> str:
    return "windows" if sys.platform == "win32" else "linux"


def make_recorder(device_path: str | None = None):
    if sys.platform == "win32":
        from .windows_backend import WindowsRecorder

        return WindowsRecorder()
    from .linux_backend import LinuxRecorder

    if not device_path:
        raise ValueError("Su Linux è necessario indicare il device del mouse da registrare.")
    return LinuxRecorder(device_path)


def make_player():
    if sys.platform == "win32":
        from .windows_backend import WindowsPlayer

        return WindowsPlayer()
    from .linux_backend import LinuxPlayer

    return LinuxPlayer()


def list_mice():
    if sys.platform == "win32":
        return []
    from .linux_backend import list_mice as _list_mice

    return _list_mice()


HOTKEY_RECORD = 1
HOTKEY_PLAY = 2
HOTKEY_EMERGENCY = 3


def make_hotkeys(on_hotkey):
    if sys.platform == "win32":
        from .windows_backend import GlobalHotkeys

        return GlobalHotkeys(on_hotkey)
    from .linux_backend import GlobalHotkeys

    return GlobalHotkeys(on_hotkey)
