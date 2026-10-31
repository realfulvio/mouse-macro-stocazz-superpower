"""Finestra Impostazioni di Windows: opzioni generali e gestione delle mod.

Controlli Win32 nativi (aspetto di sistema), così resta semplice e affidabile;
lo stile viola si può aggiungere dopo senza toccare la logica. La logica delle
mod sta in macro/mods.py.
"""
from __future__ import annotations

import ctypes as C
from ctypes import wintypes as W
import os

from macro import mods

U = C.windll.user32
LRESULT = C.c_ssize_t
WNDPROC = C.WINFUNCTYPE(LRESULT, W.HWND, W.UINT, W.WPARAM, W.LPARAM)
CLASS = 'MouseMacroSettings'
WM_COMMAND, WM_CLOSE, WM_DESTROY = 0x111, 0x10, 2
ID_TRAY, ID_UPDATES, ID_LIST, ID_INSTALL, ID_USE, ID_REMOVE, ID_FOLDER, ID_CLOSE = 301, 302, 303, 310, 311, 312, 313, 314
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
        ('MessageBoxW', C.c_int, [W.HWND, W.LPCWSTR, W.LPCWSTR, W.UINT])]:
    _fn = getattr(U, _name)
    _fn.restype, _fn.argtypes = _res, _args


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

    def show(self):
        if self.hwnd and U.IsWindow(self.hwnd):
            U.ShowWindow(self.hwnd, 9)
            U.SetForegroundWindow(self.hwnd)
            return
        instance = C.windll.kernel32.GetModuleHandleW(None)
        wc = WNDCLASS(0, self.proc, 0, 0, instance, None, U.LoadCursorW(None, C.c_void_p(32512)),
                      W.HBRUSH(16), None, CLASS)  # COLOR_BTNFACE + 1
        U.RegisterClassW(C.byref(wc))  # 0 se già registrata: va bene
        s = _dpi_scale()
        px = lambda n: round(n * s)
        self.hwnd = U.CreateWindowExW(0, CLASS, 'Impostazioni · Mouse Macro Stocazz Superpower',
                                      0x10C80000, px(160), px(120), px(560), px(470), None, None, instance, None)
        if not self.hwnd:
            raise C.WinError()
        make = lambda cls, text, style, x, y, w, h, cid: U.CreateWindowExW(
            0, cls, text, 0x50000000 | style, px(x), px(y), px(w), px(h), self.hwnd, W.HMENU(cid), instance, None)
        font = C.windll.gdi32.GetStockObject(17)  # DEFAULT_GUI_FONT
        self.controls = {}
        spec = [(ID_TRAY, 'BUTTON', 'Chiudi nel tray (la X nasconde il pannello, non chiude)', 0x10003, 20, 16, 500, 24),
                (ID_UPDATES, 'BUTTON', 'Controlla gli aggiornamenti all’avvio', 0x10003, 20, 44, 500, 24),
                (0, 'STATIC', 'Mod installate (pacchetti .mmmod di soli dati: temi e macro, senza codice)', 0, 20, 84, 510, 20),
                (ID_LIST, 'LISTBOX', '', 0x800000 + 0x200000 + 0x10000 + 0x141, 20, 108, 510, 200),
                (ID_INSTALL, 'BUTTON', 'Installa da file…', 0x10000, 20, 322, 150, 30),
                (ID_USE, 'BUTTON', 'Usa tema', 0x10000, 180, 322, 110, 30),
                (ID_REMOVE, 'BUTTON', 'Rimuovi', 0x10000, 300, 322, 110, 30),
                (ID_FOLDER, 'BUTTON', 'Apri cartella mod', 0x10000, 420, 322, 110, 30),
                (0, 'STATIC', 'Le macro delle raccolte stanno in «Apri cartella mod» → nome mod → macros: caricale con Carica.', 0, 20, 366, 510, 36),
                (ID_CLOSE, 'BUTTON', 'Chiudi', 0x10000, 420, 412, 110, 30)]
        for cid, cls, text, style, x, y, w, h in spec:
            handle = make(cls, text, style, x, y, w, h, cid)
            if cid:
                self.controls[cid] = handle
            U.SendMessageW(handle, 0x30, font, 1)  # WM_SETFONT
        self.refresh()
        U.ShowWindow(self.hwnd, 5)
        U.SetForegroundWindow(self.hwnd)

    def refresh(self):
        settings = self.panel.settings
        U.SendMessageW(self.controls[ID_TRAY], 0xF1, 1 if settings.get('close_to_tray', False) else 0, None)
        U.SendMessageW(self.controls[ID_UPDATES], 0xF1, 1 if settings.get('check_updates', True) else 0, None)
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
        if cid in (ID_TRAY, ID_UPDATES) and code == 0:  # BN_CLICKED
            on = bool(U.SendMessageW(self.controls[cid], 0xF0, 0, None))
            settings['close_to_tray' if cid == ID_TRAY else 'check_updates'] = on
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

    def wndproc(self, hwnd, msg, wp, lp):
        try:
            if msg == WM_COMMAND and self.hwnd:
                self.command(wp)
                return 0
            if msg == WM_CLOSE:
                U.DestroyWindow(hwnd)
                return 0
            if msg == WM_DESTROY:
                self.hwnd = None
                return 0
        except Exception as error:  # una finestra secondaria non deve mai far cadere il pannello
            self.panel.session.message = f'Impostazioni: {error}'
        return U.DefWindowProcW(hwnd, msg, wp, lp)
