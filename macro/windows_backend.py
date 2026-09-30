"""Backend Windows: usa pynput, che internamente si appoggia agli hook nativi di basso
livello di Windows (SetWindowsHookEx / SendInput) — permette di registrare e riprodurre
posizioni ASSOLUTE del cursore.

In più, via ctypes:
- DPI awareness del processo, senza la quale con lo scaling di Windows > 100% il
  listener riceve coordinate fisiche e il controller lavora in coordinate scalate
  (i click finiscono spostati);
- cattura di un piccolo ritaglio di schermo attorno a ogni click, usato in riproduzione
  per aspettare che la pagina sia davvero pronta prima di cliccare;
- tasti rapidi globali con RegisterHotKey (nessun hook di tastiera).
"""
from __future__ import annotations

import base64
import ctypes
import threading
import time
import zlib
from ctypes import wintypes
from typing import Callable


def _enable_dpi_awareness() -> None:
    user32 = ctypes.windll.user32
    try:
        # DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 (Windows 10 1703+)
        if user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4)):
            return
    except AttributeError:
        pass
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except (AttributeError, OSError):
        user32.SetProcessDPIAware()


# Va fatto prima che pynput crei listener/controller.
_enable_dpi_awareness()

from pynput import keyboard, mouse  # noqa: E402

from .events import (  # noqa: E402
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

# ================= Cattura schermo (GDI) =================

SNAP_SIZE = 40
# Differenza media per byte (0-255) entro cui il ritaglio è considerato "uguale".
# Riferimento misurato: stesso punto = 0, zone diverse dello schermo ≈ 30+.
TOLERANCE_STRICT = 6.0
TOLERANCE_NORMAL = 15.0
TOLERANCE_LOOSE = 28.0


def screen_geometry() -> list[int]:
    """[x, y, larghezza, altezza] del desktop virtuale (tutti i monitor) in pixel fisici."""
    gsm = ctypes.windll.user32.GetSystemMetrics
    return [gsm(76), gsm(77), gsm(78), gsm(79)]

_user32 = ctypes.windll.user32
_gdi32 = ctypes.windll.gdi32

_user32.GetDC.argtypes = [wintypes.HWND]
_user32.GetDC.restype = wintypes.HDC
_user32.ReleaseDC.argtypes = [wintypes.HWND, wintypes.HDC]
_gdi32.CreateCompatibleDC.argtypes = [wintypes.HDC]
_gdi32.CreateCompatibleDC.restype = wintypes.HDC
_gdi32.CreateCompatibleBitmap.argtypes = [wintypes.HDC, ctypes.c_int, ctypes.c_int]
_gdi32.CreateCompatibleBitmap.restype = wintypes.HBITMAP
_gdi32.SelectObject.argtypes = [wintypes.HDC, wintypes.HGDIOBJ]
_gdi32.SelectObject.restype = wintypes.HGDIOBJ
_gdi32.BitBlt.argtypes = [wintypes.HDC, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                          wintypes.HDC, ctypes.c_int, ctypes.c_int, wintypes.DWORD]
_gdi32.DeleteObject.argtypes = [wintypes.HGDIOBJ]
_gdi32.DeleteDC.argtypes = [wintypes.HDC]
_gdi32.GetDIBits.argtypes = [wintypes.HDC, wintypes.HBITMAP, wintypes.UINT, wintypes.UINT,
                             ctypes.c_void_p, ctypes.c_void_p, wintypes.UINT]

_SRCCOPY = 0x00CC0020


class _BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", wintypes.DWORD), ("biWidth", wintypes.LONG), ("biHeight", wintypes.LONG),
        ("biPlanes", wintypes.WORD), ("biBitCount", wintypes.WORD), ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD), ("biXPelsPerMeter", wintypes.LONG),
        ("biYPelsPerMeter", wintypes.LONG), ("biClrUsed", wintypes.DWORD),
        ("biClrImportant", wintypes.DWORD),
    ]


class _BITMAPINFO(ctypes.Structure):
    _fields_ = [("bmiHeader", _BITMAPINFOHEADER), ("bmiColors", wintypes.DWORD * 3)]


def grab_region(cx: int, cy: int, size: int = SNAP_SIZE) -> bytes:
    """Pixel BGRA di un quadrato size×size centrato in (cx, cy), cursore escluso."""
    left, top = cx - size // 2, cy - size // 2
    hdc_screen = _user32.GetDC(None)
    hdc_mem = _gdi32.CreateCompatibleDC(hdc_screen)
    hbmp = _gdi32.CreateCompatibleBitmap(hdc_screen, size, size)
    old = _gdi32.SelectObject(hdc_mem, hbmp)
    try:
        _gdi32.BitBlt(hdc_mem, 0, 0, size, size, hdc_screen, left, top, _SRCCOPY)
        bmi = _BITMAPINFO()
        bmi.bmiHeader.biSize = ctypes.sizeof(_BITMAPINFOHEADER)
        bmi.bmiHeader.biWidth = size
        bmi.bmiHeader.biHeight = -size
        bmi.bmiHeader.biPlanes = 1
        bmi.bmiHeader.biBitCount = 32
        buf = ctypes.create_string_buffer(size * size * 4)
        _gdi32.GetDIBits(hdc_mem, hbmp, 0, size, buf, ctypes.byref(bmi), 0)
        return buf.raw
    finally:
        _gdi32.SelectObject(hdc_mem, old)
        _gdi32.DeleteObject(hbmp)
        _gdi32.DeleteDC(hdc_mem)
        _user32.ReleaseDC(None, hdc_screen)


# L'attesa pagina confronta solo la parte centrale del ritaglio, cioè il pulsante
# cliccato: attorno possono cambiare foto, nome e icone da una scheda all'altra.
COMPARE_SIZE = 24


def center_crop(raw: bytes, size: int = SNAP_SIZE, inner: int = COMPARE_SIZE) -> bytes:
    """Quadrato inner×inner al centro di un ritaglio BGRA size×size."""
    if len(raw) != size * size * 4 or inner >= size:
        return raw
    start = (size - inner) // 2
    stride = size * 4
    return b"".join(raw[(start + y) * stride + start * 4:(start + y) * stride + (start + inner) * 4]
                    for y in range(inner))


def region_diff(a: bytes, b: bytes) -> float:
    if len(a) != len(b) or not a:
        return 255.0
    return sum(abs(x - y) for x, y in zip(a, b)) / len(a)


def encode_snap(raw: bytes) -> str:
    return base64.b64encode(zlib.compress(raw, 6)).decode("ascii")


def decode_snap(snap: str) -> bytes:
    return zlib.decompress(base64.b64decode(snap))


# ================= Registrazione =================

class WindowsRecorder:
    def __init__(self):
        self._events: list[MacroEvent] = []
        self._raw_snaps: dict[int, bytes] = {}
        self._lock = threading.Lock()
        self._listener: mouse.Listener | None = None
        self._base_t: float | None = None

    def start(self) -> None:
        self._events = []
        self._raw_snaps = {}
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

    def _append(self, evt: MacroEvent, snap: bytes | None = None) -> None:
        with self._lock:
            if snap is not None:
                self._raw_snaps[len(self._events)] = snap
            self._events.append(evt)

    def _on_move(self, x, y) -> None:
        self._append(MacroEvent(t=self._now(), kind=MOVE_ABS, x=int(x), y=int(y)))

    def _on_click(self, x, y, button, pressed) -> None:
        kind = _CLICK_KIND.get((button, pressed))
        if not kind:
            return
        snap = None
        if pressed:
            # L'hook scatta prima che l'applicazione riceva il click: lo schermo è
            # ancora nello stato "pronto a essere cliccato" (hover compreso).
            try:
                snap = grab_region(int(x), int(y))
            except OSError:
                snap = None
        self._append(MacroEvent(t=self._now(), kind=kind, x=int(x), y=int(y)), snap)

    def _on_scroll(self, x, y, dx, dy) -> None:
        self._append(MacroEvent(t=self._now(), kind=WHEEL, x=int(x), y=int(y), wheel=float(dy)))

    def stop(self) -> list[MacroEvent]:
        if self._listener:
            self._listener.stop()
            self._listener = None
        with self._lock:
            for idx, raw in self._raw_snaps.items():
                self._events[idx].snap = encode_snap(raw)
            return list(self._events)

    @property
    def current_event_count(self) -> int:
        with self._lock:
            return len(self._events)


# ================= Riproduzione =================

class WindowsPlayer:
    def __init__(self):
        self._ctrl = mouse.Controller()
        self._kbd = keyboard.Controller()

    def close_tab(self) -> None:
        """Ctrl+W alla finestra in primo piano (il browser): chiude la scheda corrente e
        il browser passa alla successiva. Solo invio di tasti, nessun hook di tastiera."""
        with self._kbd.pressed(keyboard.Key.ctrl):
            self._kbd.press("w")
            time.sleep(0.03)
            self._kbd.release("w")

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

    def wait_until_ready(
        self,
        evt: MacroEvent,
        timeout_seconds: float,
        stop_event: threading.Event,
        tolerance: float = TOLERANCE_NORMAL,
        on_waiting: Callable[[], None] | None = None,
    ) -> bool:
        """Prima di un click, aspetta che il punto sullo schermo torni uguale a com'era in
        registrazione (pagina caricata, pulsante comparso). False se scade il timeout o
        se la riproduzione viene fermata."""
        if not evt.snap:
            return True
        ref = center_crop(decode_snap(evt.snap))
        self._ctrl.position = (evt.x, evt.y)
        deadline = time.perf_counter() + timeout_seconds
        notified = False
        while True:
            if region_diff(ref, center_crop(grab_region(evt.x, evt.y))) <= tolerance:
                return True
            if stop_event.is_set() or time.perf_counter() >= deadline:
                return False
            if not notified and on_waiting is not None:
                on_waiting()
                notified = True
            time.sleep(0.05)

    def release_held(self, held: set[str]) -> None:
        mapping = {"left": mouse.Button.left, "right": mouse.Button.right, "middle": mouse.Button.middle}
        for name in held:
            btn = mapping.get(name)
            if btn:
                self._ctrl.release(btn)

    def close(self) -> None:
        pass


# ================= Tasti rapidi globali =================

_MOD_ALT = 0x0001
_MOD_CONTROL = 0x0002
_MOD_NOREPEAT = 0x4000
_VK_F9, _VK_F10, _VK_F11 = 0x78, 0x79, 0x7A
_WM_HOTKEY = 0x0312
_WM_QUIT = 0x0012

HOTKEY_RECORD = 1
HOTKEY_PLAY = 2
HOTKEY_EMERGENCY = 3


class GlobalHotkeys:
    """F9 / F10 / Ctrl+Alt+F11 funzionanti anche con il focus su un'altra finestra
    (es. il browser), tramite RegisterHotKey: nessun hook di tastiera."""

    def __init__(self, on_hotkey: Callable[[int], None]):
        self._on_hotkey = on_hotkey
        self._thread: threading.Thread | None = None
        self._thread_id: int | None = None
        self._ready = threading.Event()
        self.failed: list[str] = []

    def start(self) -> None:
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        self._ready.wait(2)

    def _run(self) -> None:
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        self._thread_id = kernel32.GetCurrentThreadId()
        wanted = [
            (HOTKEY_RECORD, _MOD_NOREPEAT, _VK_F9, "F9"),
            (HOTKEY_PLAY, _MOD_NOREPEAT, _VK_F10, "F10"),
            (HOTKEY_EMERGENCY, _MOD_CONTROL | _MOD_ALT | _MOD_NOREPEAT, _VK_F11, "Ctrl+Alt+F11"),
        ]
        registered = []
        for hk_id, mods, vk, label in wanted:
            if user32.RegisterHotKey(None, hk_id, mods, vk):
                registered.append(hk_id)
            else:
                self.failed.append(label)
        self._ready.set()

        msg = wintypes.MSG()
        try:
            while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
                if msg.message == _WM_HOTKEY:
                    try:
                        self._on_hotkey(int(msg.wParam))
                    except Exception:
                        pass
        finally:
            for hk_id in registered:
                user32.UnregisterHotKey(None, hk_id)

    def stop(self) -> None:
        if self._thread_id is not None:
            ctypes.windll.user32.PostThreadMessageW(self._thread_id, _WM_QUIT, 0, 0)
