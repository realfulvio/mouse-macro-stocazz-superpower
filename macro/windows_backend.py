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
from pynput._util.win32 import INPUT, INPUT_union, MOUSEINPUT, KEYBDINPUT, SendInput


def checked_input(packet) -> None:
    if SendInput(1, ctypes.byref(packet), ctypes.sizeof(INPUT)) != 1:
        raise OSError("Windows non ha accettato l'input. Riproduzione fermata.")


class CheckedMouse(mouse.Controller):
    """Use the native input stream for motion too, and check every injection."""
    def _position_set(self, pos):
        x, y = map(int, pos)
        if self._position_get() == (x, y):
            return
        left, top, width, height = screen_geometry()
        if not left <= x < left + width or not top <= y < top + height:
            raise ValueError("Una coordinata è fuori dallo schermo. Registra di nuovo.")
        checked_input(INPUT(type=INPUT.MOUSE, value=INPUT_union(mi=MOUSEINPUT(
            dx=round((x-left)*65535/(width-1)), dy=round((y-top)*65535/(height-1)),
            dwFlags=0x0001 | 0x8000 | 0x4000))))  # MOVE | ABSOLUTE | VIRTUALDESK

    def _press(self, button):
        checked_input(INPUT(type=INPUT.MOUSE, value=INPUT_union(mi=MOUSEINPUT(
            dwFlags=button.value[1], mouseData=button.value[2]))))

    def _release(self, button):
        checked_input(INPUT(type=INPUT.MOUSE, value=INPUT_union(mi=MOUSEINPUT(
            dwFlags=button.value[0], mouseData=button.value[2]))))

    def _scroll(self, dx, dy):
        for amount, flag in ((dy, 0x0800), (dx, 0x1000)):
            if amount:
                checked_input(INPUT(type=INPUT.MOUSE, value=INPUT_union(mi=MOUSEINPUT(
                    dwFlags=flag, mouseData=int(amount*120)))))


class CheckedKeyboard(keyboard.Controller):
    def _handle(self, key, is_press):
        checked_input(INPUT(type=INPUT.KEYBOARD, value=INPUT_union(
            ki=KEYBDINPUT(**key._parameters(is_press)))))

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

_user32.GetForegroundWindow.restype = wintypes.HWND
_user32.GetForegroundWindow.argtypes = []
_user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
_user32.GetWindowTextW.restype = ctypes.c_int
_user32.WindowFromPoint.argtypes = [wintypes.POINT]
_user32.WindowFromPoint.restype = wintypes.HWND
_user32.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]
_user32.GetAncestor.restype = wintypes.HWND


class TargetWindowChanged(RuntimeError):
    pass

_user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
_user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
_user32.IsWindow.argtypes = [wintypes.HWND]
_user32.GetDpiForWindow.argtypes = [wintypes.HWND]
_kernel32 = ctypes.windll.kernel32
_kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
_kernel32.OpenProcess.restype = wintypes.HANDLE
_kernel32.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
_kernel32.CloseHandle.argtypes = [wintypes.HANDLE]


def root_at(x: int, y: int):
    return _user32.GetAncestor(_user32.WindowFromPoint(wintypes.POINT(x, y)), 2)


def window_rect(hwnd) -> list[int]:
    rect = wintypes.RECT()
    if not _user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        raise TargetWindowChanged("La finestra del browser non è disponibile.")
    return [rect.left, rect.top, rect.right, rect.bottom]


def browser_name(hwnd) -> str:
    import ntpath
    pid = wintypes.DWORD()
    _user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    handle = _kernel32.OpenProcess(0x1000, False, pid.value)
    if not handle:
        return ""
    try:
        size = wintypes.DWORD(32768)
        name = ctypes.create_unicode_buffer(size.value)
        if _kernel32.QueryFullProcessImageNameW(handle, 0, name, ctypes.byref(size)):
            return {"chrome.exe": "Chrome", "firefox.exe": "Firefox"}.get(ntpath.basename(name.value).lower(), "")
        return ""
    finally:
        _kernel32.CloseHandle(handle)


def browser_layout(hwnd) -> dict:
    return {"window_rect": window_rect(hwnd), "dpi": _user32.GetDpiForWindow(hwnd)}


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
    def __init__(self, excluded_window=None, capture_snapshots=True, browser_only=False):
        self._events: list[MacroEvent] = []
        self._raw_snaps: dict[int, bytes] = {}
        self._lock = threading.Lock()
        self._listener: mouse.Listener | None = None
        self._base_t: float | None = None
        self.excluded_window = excluded_window
        self.capture_snapshots = capture_snapshots
        self.browser_only = browser_only
        self.target_window = None
        self.layout = {}
        self.error = ""
        self._ignored_buttons = set()
        self._held_buttons = set()
        self._keyboard_listener = None
        self._control_keys = set()

    def _exclude(self, x, y) -> bool:
        if self.excluded_window is None:
            return False
        try:
            r = window_rect(self.excluded_window)
        except TargetWindowChanged:
            return False  # panel already destroyed: never raise inside the mouse hook
        return r[0] <= x < r[2] and r[1] <= y < r[3]

    def start(self) -> None:
        self._events = []
        self._raw_snaps = {}
        self._base_t = None
        self.target_window = None
        self.layout = {}
        self.error = ""
        self._ignored_buttons.clear()
        self._held_buttons.clear()
        self._listener = mouse.Listener(
            on_move=self._on_move, on_click=self._on_click, on_scroll=self._on_scroll
        )
        self._listener.start()
        if self.browser_only:
            self._control_keys.clear()
            self._keyboard_listener = keyboard.Listener(on_press=self._key_press, on_release=self._key_release)
            self._keyboard_listener.start()

    def _key_press(self, key):
        if key in (keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
            self._control_keys.add(key)
        if self._control_keys and (key in (keyboard.Key.tab, keyboard.Key.page_down, keyboard.Key.page_up)
                or getattr(key, 'char', None) == 'w'):
            self.error = "Non cambiare scheda mentre registri. Registra i task di un solo cavallo."

    def _key_release(self, key):
        self._control_keys.discard(key)

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

    def _on_move(self, x, y, injected=False) -> None:
        if not self._held_buttons and self._exclude(x, y):
            return
        self._append(MacroEvent(t=self._now(), kind=MOVE_ABS, x=int(x), y=int(y)))

    def _on_click(self, x, y, button, pressed, injected=False) -> None:
        if pressed and self._exclude(x, y):
            self._ignored_buttons.add(button)
            return
        if not pressed and button in self._ignored_buttons:
            self._ignored_buttons.discard(button)
            return
        if not pressed and button not in self._held_buttons:
            return  # release of the panel's start click is not a recorded gesture
        if pressed and self.browser_only and not self._check_record_target(x, y):
            return
        kind = _CLICK_KIND.get((button, pressed))
        if not kind:
            return
        snap = None
        if pressed and self.capture_snapshots:
            # L'hook scatta prima che l'applicazione riceva il click: lo schermo è
            # ancora nello stato "pronto a essere cliccato" (hover compreso).
            try:
                snap = grab_region(int(x), int(y))
            except OSError:
                snap = None
        self._append(MacroEvent(t=self._now(), kind=kind, x=int(x), y=int(y)), snap)
        if pressed:
            self._held_buttons.add(button)
        else:
            self._held_buttons.discard(button)

    def _on_scroll(self, x, y, dx, dy, injected=False) -> None:
        if self._exclude(x, y):
            return
        if self.browser_only and not self._check_record_target(x, y):
            return
        self._append(MacroEvent(t=self._now(), kind=WHEEL, x=int(x), y=int(y), wheel=float(dy)))

    def _check_record_target(self, x, y) -> bool:
        root = root_at(int(x), int(y))
        if root != _user32.GetForegroundWindow() or not browser_name(root):
            self.error = "Registra soltanto nella pagina di Chrome o Firefox."
            return False
        r = window_rect(root)
        if y < r[1] + round(64 * _user32.GetDpiForWindow(root) / 96):
            self.error = "Non registrare il cambio scheda. Ferma con F9 dopo i task di un solo cavallo."
            return False
        if self.target_window is None:
            self.target_window = root
            self.layout = browser_layout(root)
        elif root != self.target_window or browser_layout(root) != self.layout:
            self.error = "La finestra è cambiata durante la registrazione. Registra di nuovo un solo cavallo."
            return False
        return True

    def stop(self) -> list[MacroEvent]:
        if self._keyboard_listener:
            self._keyboard_listener.stop()
            self._keyboard_listener.join(timeout=1)
            if self._keyboard_listener.is_alive():
                raise RuntimeError("L'ascolto tastiera non si è arrestato.")
            self._keyboard_listener = None
        if self._listener:
            self._listener.stop()
            self._listener.join(timeout=1)
            if self._listener.is_alive():
                raise RuntimeError("Il registratore non si è arrestato.")
            self._listener = None
        with self._lock:
            for idx, raw in self._raw_snaps.items():
                self._events[idx].snap = encode_snap(raw)
            events = list(self._events)
        # An incomplete physical drag stopped with F9/close must not leave the
        # Windows button state latched; validation still rejects the incomplete
        # macro rather than silently inventing its missing release event.
        if self._held_buttons:
            ctrl = CheckedMouse()
            for button in self._held_buttons:
                ctrl.release(button)
            self._held_buttons.clear()
        return events

    @property
    def current_event_count(self) -> int:
        with self._lock:
            return len(self._events)


# ================= Riproduzione =================

class WindowsPlayer:
    def __init__(self):
        self._ctrl = CheckedMouse()
        self._kbd = CheckedKeyboard()
        self._target_window = None
        self._held = set()
        self._layout = None

    def select_browser(self, evt: MacroEvent, layout: dict | None = None) -> str:
        target = _user32.GetForegroundWindow()
        name = browser_name(target)
        if not name:
            raise TargetWindowChanged("Attiva Chrome o Firefox, poi premi F10.")
        current = browser_layout(target)
        if layout and current != layout:
            raise TargetWindowChanged("Posizione, dimensione o scala del browser diversa: ripristinala o registra di nuovo.")
        self._target_window = target
        self._layout = current
        self._check_target(evt)
        return name

    def lock_target_window(self, evt: MacroEvent) -> None:
        """Fissa la finestra sotto il primo click; non porta finestre in primo piano."""
        target = _user32.GetForegroundWindow()
        title = ctypes.create_unicode_buffer(512)
        _user32.GetWindowTextW(target, title, len(title))
        if not target or "mouse macro" in title.value.lower():
            raise TargetWindowChanged("Torna sulla finestra del browser e avvia con F10.")
        self._target_window = target
        self._check_target(evt)

    def _check_target(self, evt: MacroEvent | None = None) -> None:
        if self._target_window is None:
            return
        if _user32.GetForegroundWindow() != self._target_window:
            raise TargetWindowChanged("La finestra destinataria non è più in primo piano. Riproduzione fermata.")
        if self._layout is not None and browser_layout(self._target_window) != self._layout:
            raise TargetWindowChanged("La finestra del browser è stata spostata o ridimensionata. Riproduzione fermata.")
        if evt is not None and evt.kind in (LEFT_DOWN, RIGHT_DOWN, MIDDLE_DOWN, WHEEL):
            window = _user32.WindowFromPoint(wintypes.POINT(evt.x, evt.y))
            if _user32.GetAncestor(window, 2) != self._target_window:  # GA_ROOT
                raise TargetWindowChanged("Il punto del click non appartiene alla finestra destinataria. Riproduzione fermata.")

    def next_tab(self, stop_event: threading.Event) -> None:
        """Exactly one Ctrl+Tab between completed cycles. Never closes a tab."""
        self._check_target()
        try:
            self._kbd.press(keyboard.Key.ctrl)
            self._kbd.press(keyboard.Key.tab)
            stop_event.wait(0.04)
        finally:
            try:
                self._kbd.release(keyboard.Key.tab)
            finally:
                self._kbd.release(keyboard.Key.ctrl)
        # Guard time, NOT a detection of loading completion.
        stop_event.wait(0.8)
        if not stop_event.is_set():
            self._check_target()

    def close_tab(self) -> None:
        """Ctrl+W alla finestra in primo piano (il browser): chiude la scheda corrente e
        il browser passa alla successiva. Solo invio di tasti, nessun hook di tastiera."""
        self._check_target()
        with self._kbd.pressed(keyboard.Key.ctrl):
            self._kbd.press("w")
            time.sleep(0.03)
            self._kbd.release("w")

    def apply_event(self, evt: MacroEvent) -> None:
        self._check_target(evt)
        if evt.kind == MOVE_ABS:
            self._ctrl.position = (evt.x, evt.y)
        elif evt.kind == LEFT_DOWN:
            self._ctrl.position = (evt.x, evt.y)
            self._held.add("left")
            self._ctrl.press(mouse.Button.left)
        elif evt.kind == LEFT_UP:
            self._ctrl.position = (evt.x, evt.y)
            self._ctrl.release(mouse.Button.left)
            self._held.discard("left")
        elif evt.kind == RIGHT_DOWN:
            self._ctrl.position = (evt.x, evt.y)
            self._held.add("right")
            self._ctrl.press(mouse.Button.right)
        elif evt.kind == RIGHT_UP:
            self._ctrl.position = (evt.x, evt.y)
            self._ctrl.release(mouse.Button.right)
            self._held.discard("right")
        elif evt.kind == MIDDLE_DOWN:
            self._ctrl.position = (evt.x, evt.y)
            self._held.add("middle")
            self._ctrl.press(mouse.Button.middle)
        elif evt.kind == MIDDLE_UP:
            self._ctrl.position = (evt.x, evt.y)
            self._ctrl.release(mouse.Button.middle)
            self._held.discard("middle")
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
        if stop_event.is_set():
            return False
        self._check_target(evt)
        if not evt.snap:
            return True
        ref = center_crop(decode_snap(evt.snap))
        self._ctrl.position = (evt.x, evt.y)
        deadline = time.perf_counter() + timeout_seconds
        notified = False
        while True:
            if stop_event.is_set():
                return False
            self._check_target(evt)
            if region_diff(ref, center_crop(grab_region(evt.x, evt.y))) <= tolerance:
                return True
            if stop_event.is_set() or time.perf_counter() >= deadline:
                return False
            if not notified and on_waiting is not None:
                on_waiting()
                notified = True
            if stop_event.wait(0.05):
                return False

    def release_held(self, held: set[str]) -> None:
        mapping = {"left": mouse.Button.left, "right": mouse.Button.right, "middle": mouse.Button.middle}
        error = None
        for name in held:
            btn = mapping.get(name)
            if btn:
                try:
                    self._ctrl.release(btn)
                    self._held.discard(name)
                except Exception as caught:
                    error = error or caught
        if error:
            raise error

    def close(self) -> None:
        self.release_held(set(self._held))


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
        if self._thread and threading.current_thread() is not self._thread:
            self._thread.join(timeout=2)
