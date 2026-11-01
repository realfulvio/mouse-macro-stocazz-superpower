"""Finestra Impostazioni di Windows: opzioni generali e gestione delle mod.

Controlli Win32 con i colori della skin in uso (viola per Bambola/Unicorno): sfondo,
testi e elenco colorati con i messaggi WM_CTLCOLOR*, pulsanti e interruttori
disegnati a mano (owner-draw GDI). La logica delle mod sta in macro/mods.py.
"""
from __future__ import annotations

import ctypes as C
from ctypes import wintypes as W
import os

from macro import mods

U = C.windll.user32
G = C.windll.gdi32
LRESULT = C.c_ssize_t
WNDPROC = C.WINFUNCTYPE(LRESULT, W.HWND, W.UINT, W.WPARAM, W.LPARAM)
CLASS = 'MouseMacroSettings'
WM_COMMAND, WM_CLOSE, WM_DESTROY = 0x111, 0x10, 2
ID_TITLE, ID_TRAY, ID_UPDATES, ID_LIST, ID_INSTALL, ID_USE, ID_REMOVE, ID_FOLDER, ID_CLOSE = 300, 301, 302, 303, 310, 311, 312, 313, 314
TOGGLES = (ID_TRAY, ID_UPDATES)
KIND = {'theme': 'tema', 'macros': 'macro'}


class WNDCLASS(C.Structure):
    _fields_ = [('style', W.UINT), ('lpfnWndProc', WNDPROC), ('cbClsExtra', C.c_int),
                ('cbWndExtra', C.c_int), ('hInstance', W.HINSTANCE), ('hIcon', W.HICON),
                ('hCursor', W.HANDLE), ('hbrBackground', W.HBRUSH),
                ('lpszMenuName', W.LPCWSTR), ('lpszClassName', W.LPCWSTR)]


for _name, _res, _args in [
        ('DefWindowProcW', LRESULT, [W.HWND, W.UINT, W.WPARAM, W.LPARAM]),
        ('SendMessageW', LRESULT, [W.HWND, W.UINT, W.WPARAM, C.c_void_p]),
        ('CreateWindowExW', W.HWND, [W.DWORD, W.LPCWSTR, W.LPCWSTR, W.DWORD, C.c_int, C.c_int, C.c_int, C.c_int,
                                     W.HWND, W.HMENU, W.HINSTANCE, C.c_void_p]),
        ('IsWindow', W.BOOL, [W.HWND]), ('ShowWindow', W.BOOL, [W.HWND, C.c_int]),
        ('SetForegroundWindow', W.BOOL, [W.HWND]), ('DestroyWindow', W.BOOL, [W.HWND]),
        ('MessageBoxW', C.c_int, [W.HWND, W.LPCWSTR, W.LPCWSTR, W.UINT]),
        ('GetWindowTextW', C.c_int, [W.HWND, W.LPWSTR, C.c_int]), ('GetDlgCtrlID', C.c_int, [W.HWND]),
        ('LoadCursorW', W.HANDLE, [W.HINSTANCE, C.c_void_p]), ('RegisterClassW', W.ATOM, [C.POINTER(WNDCLASS)]), ('InvalidateRect', W.BOOL, [W.HWND, C.c_void_p, W.BOOL]),
        ('FillRect', C.c_int, [W.HDC, C.POINTER(W.RECT), C.c_void_p]),
        ('GetClientRect', W.BOOL, [W.HWND, C.POINTER(W.RECT)]),
        ('DrawTextW', C.c_int, [W.HDC, W.LPCWSTR, C.c_int, C.POINTER(W.RECT), W.UINT])]:
    _fn = getattr(U, _name)
    _fn.restype, _fn.argtypes = _res, _args
for _name, _res, _args in [
        ('CreateSolidBrush', C.c_void_p, [W.DWORD]), ('CreatePen', C.c_void_p, [C.c_int, C.c_int, W.DWORD]),
        ('SelectObject', C.c_void_p, [W.HDC, C.c_void_p]), ('DeleteObject', W.BOOL, [C.c_void_p]),
        ('RoundRect', W.BOOL, [W.HDC, C.c_int, C.c_int, C.c_int, C.c_int, C.c_int, C.c_int]),
        ('SetTextColor', W.DWORD, [W.HDC, W.DWORD]), ('SetBkColor', W.DWORD, [W.HDC, W.DWORD]),
        ('SetBkMode', C.c_int, [W.HDC, C.c_int]),
        ('CreateFontW', C.c_void_p, [C.c_int, C.c_int, C.c_int, C.c_int, C.c_int, W.DWORD, W.DWORD, W.DWORD, W.DWORD,
                                      W.DWORD, W.DWORD, W.DWORD, W.DWORD, W.LPCWSTR])]:
    _fn = getattr(G, _name)
    _fn.restype, _fn.argtypes = _res, _args


_gmh = C.windll.kernel32.GetModuleHandleW
_gmh.restype, _gmh.argtypes = W.HMODULE, [W.LPCWSTR]


class DRAWITEM(C.Structure):
    _fields_ = [('CtlType', W.UINT), ('CtlID', W.UINT), ('itemID', W.UINT), ('itemAction', W.UINT),
                ('itemState', W.UINT), ('hwndItem', W.HWND), ('hDC', W.HDC), ('rcItem', W.RECT),
                ('itemData', C.c_size_t)]


def colorref(hex_color):
    """'#RRGGBB' -> COLORREF (0x00BBGGRR)."""
    h = hex_color.lstrip('#')
    return int(h[0:2], 16) | int(h[2:4], 16) << 8 | int(h[4:6], 16) << 16


def is_dark(hex_color):
    h = hex_color.lstrip('#')
    return (0.299 * int(h[0:2], 16) + 0.587 * int(h[2:4], 16) + 0.114 * int(h[4:6], 16)) < 128


def _dpi_scale():
    try:
        return U.GetDpiForSystem() / 96
    except AttributeError:
        return 1.0


def list_label(info, current_skin):
    """Riga dell'elenco: «Nome · tema · v1.0 · in uso»."""
    used = ' · in uso' if current_skin == 'mod:' + info.id else ''
    return f'{info.name} · {KIND[info.kind]} · v{info.version} · di {info.author}{used}'


def confirm_text(info):
    lines = '\n'.join('• ' + line for line in info.summary())
    return (f'Installare «{info.name}» {info.version} di {info.author}?\n\n{lines}\n\n'
            f'SHA-256: {info.sha256[:16]}…\n\nInstalla solo mod di cui ti fidi.')


class SettingsWindow:
    """Una sola finestra alla volta; `panel` è il Panel di windows_main."""

    def __init__(self, panel, mods_dir):
        self.panel, self.mods_dir, self.hwnd, self.items = panel, mods_dir, None, []
        self.proc = WNDPROC(self.wndproc)  # va tenuto vivo finché la finestra esiste
        self.toggles, self.gdi = {}, {}

    def make_gdi(self, s):
        """Colori della skin in uso, pennelli e font; rifatti a ogni apertura."""
        from windows_visual import COLORS
        self.drop_gdi()
        c = {k: colorref(COLORS[k]) for k in ('background', 'surface', 'border', 'text', 'muted', 'play',
                                              'button', 'button_hover', 'on_accent')}
        self.gdi = {'c': c, 'bg': G.CreateSolidBrush(c['background']), 'surface': G.CreateSolidBrush(c['surface']),
                    'font': G.CreateFontW(-round(15 * s), 0, 0, 0, 400, 0, 0, 0, 1, 0, 0, 5, 0, 'Segoe UI'),
                    'bold': G.CreateFontW(-round(15 * s), 0, 0, 0, 700, 0, 0, 0, 1, 0, 0, 5, 0, 'Segoe UI'),
                    'title': G.CreateFontW(-round(26 * s), 0, 0, 0, 700, 0, 0, 0, 1, 0, 0, 5, 0, 'Segoe UI'),
                    'dark': is_dark(COLORS['background'])}

    def drop_gdi(self):
        for key in ('bg', 'surface', 'font', 'bold', 'title'):
            if self.gdi.get(key):
                G.DeleteObject(self.gdi[key])
        self.gdi = {}

    def show(self):
        if self.hwnd and U.IsWindow(self.hwnd):
            U.ShowWindow(self.hwnd, 9)
            U.SetForegroundWindow(self.hwnd)
            return
        instance = _gmh(None)
        wc = WNDCLASS(0, self.proc, 0, 0, instance, None, U.LoadCursorW(None, C.c_void_p(32512)),
                      None, None, CLASS)  # lo sfondo lo disegna WM_ERASEBKGND
        U.RegisterClassW(C.byref(wc))  # 0 se già registrata: va bene
        s = _dpi_scale()
        px = lambda n: round(n * s)
        self.make_gdi(s)
        # WS_EX_TOPMOST: the panel is always on top, so without it this window opens behind it.
        # Height 604 leaves the Chiudi button (bottom at 528) fully inside the client area.
        self.hwnd = U.CreateWindowExW(0x8, CLASS, 'Impostazioni · Mouse Macro Stocazz Superpower',
                                      0x10C80000, px(160), px(120), px(580), px(604), None, None, instance, None)
        if not self.hwnd:
            raise C.WinError()
        if self.gdi['dark']:  # barra del titolo scura (Windows 10 20H1+ / 11); ignorato altrove
            try:
                C.windll.dwmapi.DwmSetWindowAttribute(self.hwnd, 20, C.byref(C.c_int(1)), 4)
            except (OSError, AttributeError):
                pass
        make = lambda cls, text, style, x, y, w, h, cid: U.CreateWindowExW(
            0, cls, text, 0x50000000 | style, px(x), px(y), px(w), px(h), self.hwnd, W.HMENU(cid), instance, None)
        owner = 0x10000 | 0xB  # TABSTOP | BS_OWNERDRAW
        spec = [(ID_TITLE, 'STATIC', 'Impostazioni', 0, 24, 16, 520, 40),
                (ID_TRAY, 'BUTTON', 'Chiudi nel tray (la X nasconde il pannello)', owner, 24, 66, 520, 36),
                (ID_UPDATES, 'BUTTON', 'Controlla gli aggiornamenti all’avvio', owner, 24, 106, 520, 36),
                (0, 'STATIC', 'Mod installate: pacchetti .mmmod di soli dati (temi e macro), senza codice', 0, 24, 156, 520, 22),
                (ID_LIST, 'LISTBOX', '', 0x800000 + 0x200000 + 0x10000 + 0x141, 24, 184, 520, 190),
                (ID_INSTALL, 'BUTTON', 'Installa da file…', owner, 24, 388, 170, 40),
                (ID_USE, 'BUTTON', 'Usa tema', owner, 204, 388, 100, 40),
                (ID_REMOVE, 'BUTTON', 'Rimuovi', owner, 314, 388, 100, 40),
                (ID_FOLDER, 'BUTTON', 'Cartella mod', owner, 424, 388, 120, 40),
                (0, 'STATIC', 'Le macro delle raccolte sono in «Cartella mod» → nome mod → macros: caricale con Carica.', 0, 24, 440, 520, 40),
                (ID_CLOSE, 'BUTTON', 'Chiudi', owner, 424, 488, 120, 40)]
        self.controls = {}
        for cid, cls, text, style, x, y, w, h in spec:
            handle = make(cls, text, style, x, y, w, h, cid)
            if cid:
                self.controls[cid] = handle
            font = self.gdi['title'] if cid == ID_TITLE else self.gdi['font']
            U.SendMessageW(handle, 0x30, font, 1)  # WM_SETFONT
        self.refresh()
        U.ShowWindow(self.hwnd, 5)
        U.SetForegroundWindow(self.hwnd)

    def refresh(self):
        settings = self.panel.settings
        self.toggles = {ID_TRAY: bool(settings.get('close_to_tray', False)),
                        ID_UPDATES: bool(settings.get('check_updates', True))}
        for cid in TOGGLES:
            U.InvalidateRect(self.controls[cid], None, True)
        self.items = mods.installed(self.mods_dir)
        U.SendMessageW(self.controls[ID_LIST], 0x184, 0, None)  # LB_RESETCONTENT
        from windows_visual import CURRENT
        for info in self.items:
            U.SendMessageW(self.controls[ID_LIST], 0x180, 0, C.c_wchar_p(list_label(info, CURRENT['skin'])))

    def selected(self):
        index = U.SendMessageW(self.controls[ID_LIST], 0x188, 0, None)  # LB_GETCURSEL
        return self.items[index] if 0 <= index < len(self.items) else None

    def say(self, text, flags=0x40):
        return U.MessageBoxW(self.hwnd, text, 'Mouse Macro · Mod', flags)

    def install(self):
        from macro.win_dialogs import ask_open_mod
        self.panel.dialog_open = True
        try:
            path = ask_open_mod('Installa mod', owner=self.hwnd)
            if not path:
                return
            info = mods.inspect(path)
            if self.say(confirm_text(info), 0x24) != 6:  # MB_YESNO | MB_ICONQUESTION, IDYES
                return
            self.panel.release_mod_skin(info.id)  # i PNG in uso non si possono sostituire
            mods.install(path, self.mods_dir)
            self.panel.reload_mod_skins()
            self.refresh()
            self.say('Mod installata.' + (' Scegli «Usa tema» per attivarla.' if info.kind == 'theme' else ''))
        except (mods.ModError, OSError) as error:
            self.say(f'Mod non installata.\n\n{error}', 0x10)
        finally:
            self.panel.dialog_open = False

    def use_theme(self):
        info = self.selected()
        if not info or info.kind != 'theme':
            return self.say('Seleziona un tema nell’elenco.')
        self.panel.set_skin('mod:' + info.id)
        self.panel.render()
        self.refresh()

    def remove(self):
        info = self.selected()
        if not info:
            return self.say('Seleziona una mod nell’elenco.')
        if self.say(f'Rimuovere «{info.name}»?', 0x24) != 6:
            return
        try:
            self.panel.release_mod_skin(info.id)
            mods.remove(self.mods_dir, info.id)
        except mods.ModError as error:
            return self.say(str(error), 0x10)
        self.panel.reload_mod_skins()
        self.refresh()

    def command(self, wp):
        cid, code = wp & 0xFFFF, wp >> 16
        settings = self.panel.settings
        if cid in TOGGLES and code == 0:  # BN_CLICKED
            self.toggles[cid] = not self.toggles.get(cid, False)
            U.InvalidateRect(self.controls[cid], None, True)
            settings['close_to_tray' if cid == ID_TRAY else 'check_updates'] = self.toggles[cid]
            self.panel.write_settings()
        elif cid == ID_INSTALL:
            self.install()
        elif cid == ID_USE or (cid == ID_LIST and code == 2):  # doppio clic nell'elenco
            self.use_theme()
        elif cid == ID_REMOVE:
            self.remove()
        elif cid == ID_FOLDER:
            self.mods_dir.mkdir(parents=True, exist_ok=True)
            os.startfile(str(self.mods_dir))
        elif cid == ID_CLOSE:
            U.DestroyWindow(self.hwnd)

    def draw_item(self, lp):
        """Pulsanti e interruttori disegnati con i colori della skin (WM_DRAWITEM)."""
        di = C.cast(lp, C.POINTER(DRAWITEM)).contents
        c, dc, rect = self.gdi['c'], di.hDC, di.rcItem
        cid, pressed = di.CtlID, bool(di.itemState & 1)
        U.FillRect(dc, C.byref(rect), self.gdi['bg'])
        G.SetBkMode(dc, 1)  # TRANSPARENT
        s = _dpi_scale()
        if cid in TOGGLES:
            label = C.create_unicode_buffer(128)
            U.GetWindowTextW(di.hwndItem, label, 128)
            text_rect = W.RECT(rect.left + round(4 * s), rect.top, rect.right - round(70 * s), rect.bottom)
            G.SelectObject(dc, self.gdi['font'])
            G.SetTextColor(dc, c['text'])
            U.DrawTextW(dc, label.value, -1, C.byref(text_rect), 0x24)  # VCENTER | SINGLELINE
            on = self.toggles.get(cid, False)
            w, h = round(46 * s), round(24 * s)
            left, top = rect.right - w - round(4 * s), rect.top + (rect.bottom - rect.top - h) // 2
            self.pill(dc, left, top, w, h, c['play'] if on else c['border'], c['border'])
            knob = h - round(6 * s)
            x = left + w - knob - round(3 * s) if on else left + round(3 * s)
            self.pill(dc, x, top + round(3 * s), knob, knob, c['text'], c['text'])
            return
        primary = cid == ID_INSTALL
        fill = c['play'] if primary else (c['button_hover'] if pressed else c['button'])
        self.pill(dc, rect.left, rect.top, rect.right - rect.left, rect.bottom - rect.top, fill, c['border'],
                  radius=round(12 * s))
        label = C.create_unicode_buffer(128)
        U.GetWindowTextW(di.hwndItem, label, 128)
        G.SelectObject(dc, self.gdi['bold'])
        G.SetTextColor(dc, c['on_accent'] if primary else c['text'])
        text_rect = W.RECT(rect.left, rect.top, rect.right, rect.bottom)
        U.DrawTextW(dc, label.value, -1, C.byref(text_rect), 0x25)  # CENTER | VCENTER | SINGLELINE

    def pill(self, dc, x, y, w, h, fill, edge, radius=None):
        brush, pen = G.CreateSolidBrush(fill), G.CreatePen(0, 1, edge)
        old_brush, old_pen = G.SelectObject(dc, brush), G.SelectObject(dc, pen)
        r = radius if radius is not None else h
        G.RoundRect(dc, x, y, x + w, y + h, r, r)
        G.SelectObject(dc, old_brush)
        G.SelectObject(dc, old_pen)
        G.DeleteObject(brush)
        G.DeleteObject(pen)

    def wndproc(self, hwnd, msg, wp, lp):
        try:
            if msg == WM_COMMAND and self.hwnd:
                self.command(wp)
                return 0
            if msg == 0x14 and self.gdi:  # WM_ERASEBKGND
                rect = W.RECT()
                U.GetClientRect(hwnd, C.byref(rect))
                U.FillRect(wp, C.byref(rect), self.gdi['bg'])
                return 1
            if msg == 0x2B and self.gdi:  # WM_DRAWITEM
                self.draw_item(lp)
                return 1
            if msg in (0x138, 0x134) and self.gdi:  # WM_CTLCOLORSTATIC / WM_CTLCOLORLISTBOX
                c = self.gdi['c']
                G.SetTextColor(wp, c['text'] if msg == 0x134 or U.GetDlgCtrlID(lp) == ID_TITLE else c['muted'])
                if msg == 0x134:
                    G.SetBkColor(wp, c['surface'])
                    return self.gdi['surface']
                G.SetBkMode(wp, 1)
                return self.gdi['bg']
            if msg == WM_CLOSE:
                U.DestroyWindow(hwnd)
                return 0
            if msg == WM_DESTROY:
                self.hwnd = None
                self.drop_gdi()
                return 0
        except Exception as error:  # una finestra secondaria non deve mai far cadere il pannello
            self.panel.session.message = f'Impostazioni: {error}'
        return U.DefWindowProcW(hwnd, msg, wp, lp)
