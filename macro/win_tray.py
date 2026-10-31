"""Icona nell'area di notifica di Windows (Shell_NotifyIconW), solo ctypes.

Nessuna dipendenza esterna. La parte che parla con Windows è in `Tray`; le
scelte (voci del menu, cosa fare a un clic) sono funzioni pure, così si
provano anche senza Windows.
"""
from __future__ import annotations

import ctypes
from ctypes import wintypes

WM_TRAY = 0x8000 + 0x42          # messaggio privato inviato dalla finestra del pannello
WM_LBUTTONDBLCLK = 0x0203
WM_LBUTTONUP = 0x0202
WM_RBUTTONUP = 0x0205
WM_CONTEXTMENU = 0x007B
NIM_ADD, NIM_MODIFY, NIM_DELETE, NIM_SETVERSION = 0, 1, 2, 4
NIF_MESSAGE, NIF_ICON, NIF_TIP = 1, 2, 4
NOTIFYICON_VERSION_4 = 4
ICON_ID = 1

# Identificatori delle voci di menu (restituiti da TrackPopupMenu).
SHOW, RECORD, PLAY, STOP_ALL, CLOSE_TO_TRAY, QUIT = 1, 2, 3, 4, 5, 6
MF_STRING, MF_CHECKED, MF_GRAYED, MF_SEPARATOR = 0, 8, 3, 0x800


def menu_items(visible: bool, close_to_tray: bool, busy: bool = False):
    """Voci (id, testo, flag) del menu del tray; `None` come testo = separatore."""
    return [
        (SHOW, 'Nascondi pannello' if visible else 'Mostra pannello', MF_STRING),
        (None, None, MF_SEPARATOR),
        (RECORD, 'Registra · F9', MF_STRING),
        (PLAY, 'Riproduci · F10', MF_STRING),
        (STOP_ALL, 'Ferma tutto · Ctrl+Alt+F11', MF_STRING),
        (None, None, MF_SEPARATOR),
        (CLOSE_TO_TRAY, 'Chiudi nel tray', MF_CHECKED if close_to_tray else MF_STRING),
        (None, None, MF_SEPARATOR),
        (QUIT, 'Esci', MF_STRING),
    ]


def click_action(lparam: int):
    """Che cosa fare per il messaggio del tray: 'toggle', 'menu' o None."""
    event = lparam & 0xFFFF
    if event in (WM_LBUTTONDBLCLK,):
        return 'toggle'
    if event in (WM_RBUTTONUP, WM_CONTEXTMENU):
        return 'menu'
    return None


def should_hide_on_close(close_to_tray: bool, quitting: bool, tray_ok: bool) -> bool:
    """La X nasconde solo se l'opzione è attiva, l'icona c'è davvero e non si sta uscendo."""
    return close_to_tray and tray_ok and not quitting


class _NOTIFYICONDATA(ctypes.Structure):
    _fields_ = [('cbSize', wintypes.DWORD), ('hWnd', wintypes.HWND), ('uID', wintypes.UINT),
                ('uFlags', wintypes.UINT), ('uCallbackMessage', wintypes.UINT),
                ('hIcon', wintypes.HICON), ('szTip', wintypes.WCHAR * 128),
                ('dwState', wintypes.DWORD), ('dwStateMask', wintypes.DWORD),
                ('szInfo', wintypes.WCHAR * 256), ('uVersion', wintypes.UINT),
                ('szInfoTitle', wintypes.WCHAR * 64), ('dwInfoFlags', wintypes.DWORD)]


class Tray:
    """Aggiunge, ripristina e toglie l'icona. Ogni errore diventa `ok = False`:
    senza tray il pannello deve continuare a funzionare come prima."""

    def __init__(self, hwnd, icon_path, tooltip):
        self.hwnd, self.tooltip, self.icon, self.ok = hwnd, tooltip[:127], None, False
        shell = ctypes.windll.shell32
        self._notify = shell.Shell_NotifyIconW
        self._notify.restype, self._notify.argtypes = wintypes.BOOL, [wintypes.DWORD, ctypes.POINTER(_NOTIFYICONDATA)]
        user = ctypes.windll.user32
        user.RegisterWindowMessageW.restype = wintypes.UINT
        # Windows invia questo messaggio quando Explorer riparte: l'icona va rimessa.
        self.created_message = user.RegisterWindowMessageW('TaskbarCreated')
        user.LoadImageW.restype = wintypes.HANDLE
        user.LoadImageW.argtypes = [wintypes.HINSTANCE, wintypes.LPCWSTR, wintypes.UINT,
                                    ctypes.c_int, ctypes.c_int, wintypes.UINT]
        self.icon = user.LoadImageW(None, str(icon_path), 1, 16, 16, 0x10)  # IMAGE_ICON, LR_LOADFROMFILE
        self.add()

    def _data(self):
        data = _NOTIFYICONDATA()
        data.cbSize = ctypes.sizeof(_NOTIFYICONDATA)
        data.hWnd, data.uID = self.hwnd, ICON_ID
        data.uFlags = NIF_MESSAGE | NIF_ICON | NIF_TIP
        data.uCallbackMessage, data.hIcon, data.szTip = WM_TRAY, self.icon, self.tooltip
        return data

    def add(self):
        try:
            data = self._data()
            self.ok = bool(self._notify(NIM_ADD, ctypes.byref(data)))
        except Exception:
            self.ok = False
        return self.ok

    def set_tooltip(self, text):
        self.tooltip = text[:127]
        if self.ok:
            self._notify(NIM_MODIFY, ctypes.byref(self._data()))

    def remove(self):
        if self.ok:
            self._notify(NIM_DELETE, ctypes.byref(self._data()))
            self.ok = False

