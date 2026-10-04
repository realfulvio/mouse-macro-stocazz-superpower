"""Compact native Windows panel. No browser UI, no Flet helper, no network."""
from __future__ import annotations

import ctypes as C
from ctypes import wintypes as W
import json
import os
from pathlib import Path
import queue
import threading
import traceback

from macro.windows_backend import (WindowsRecorder, WindowsPlayer, GlobalHotkeys,
    HOTKEY_RECORD, HOTKEY_PLAY, HOTKEY_EMERGENCY, screen_geometry, window_rect, browser_layout)
from macro.session import Session, State, VERSION
from macro.engine import PlaybackOptions
from macro.events import BUTTON_OF_DOWN, BUTTON_OF_UP, WHEEL

U = C.windll.user32
G = C.windll.gdi32
K = C.windll.kernel32
LRESULT = C.c_ssize_t
WNDPROC = C.WINFUNCTYPE(LRESULT, W.HWND, W.UINT, W.WPARAM, W.LPARAM)


class WNDCLASS(C.Structure):
    _fields_ = [('style', W.UINT), ('lpfnWndProc', WNDPROC), ('cbClsExtra', C.c_int),
                ('cbWndExtra', C.c_int), ('hInstance', W.HINSTANCE), ('hIcon', W.HICON),
                ('hCursor', W.HANDLE), ('hbrBackground', W.HBRUSH),
                ('lpszMenuName', W.LPCWSTR), ('lpszClassName', W.LPCWSTR)]


class MONITORINFO(C.Structure):
    _fields_ = [('cbSize', W.DWORD), ('rcMonitor', W.RECT), ('rcWork', W.RECT), ('dwFlags', W.DWORD)]


def api(lib, name, result, args):
    fn = getattr(lib, name)
    fn.restype, fn.argtypes = result, args
    return fn


api(K, 'GetModuleHandleW', W.HMODULE, [W.LPCWSTR])
api(K, 'CreateMutexW', W.HANDLE, [C.c_void_p, W.BOOL, W.LPCWSTR])
api(U, 'DefWindowProcW', LRESULT, [W.HWND, W.UINT, W.WPARAM, W.LPARAM])
api(U, 'CreateWindowExW', W.HWND, [W.DWORD, W.LPCWSTR, W.LPCWSTR, W.DWORD,
    C.c_int, C.c_int, C.c_int, C.c_int, W.HWND, W.HMENU, W.HINSTANCE, C.c_void_p])
api(U, 'SetWindowPos', W.BOOL, [W.HWND, W.HWND, C.c_int, C.c_int, C.c_int, C.c_int, W.UINT])
api(U, 'SendMessageW', LRESULT, [W.HWND, W.UINT, W.WPARAM, W.LPARAM])
api(U, 'PostMessageW', W.BOOL, [W.HWND, W.UINT, W.WPARAM, W.LPARAM])
api(U, 'SetWindowTextW', W.BOOL, [W.HWND, W.LPCWSTR])
api(U, 'EnableWindow', W.BOOL, [W.HWND, W.BOOL])
api(U, 'ShowWindow', W.BOOL, [W.HWND, C.c_int])
api(U, 'DestroyWindow', W.BOOL, [W.HWND])
api(U, 'LoadCursorW', W.HANDLE, [W.HINSTANCE, C.c_void_p])
api(U, 'MonitorFromPoint', W.HANDLE, [W.POINT, W.DWORD])
api(U, 'GetMonitorInfoW', W.BOOL, [W.HANDLE, C.POINTER(MONITORINFO)])
api(U, 'CreatePopupMenu', W.HMENU, [])
api(U, 'AppendMenuW', W.BOOL, [W.HMENU, W.UINT, C.c_size_t, W.LPCWSTR])
api(U, 'TrackPopupMenu', W.UINT, [W.HMENU, W.UINT, C.c_int, C.c_int, C.c_int, W.HWND, C.c_void_p])
api(U, 'DestroyMenu', W.BOOL, [W.HMENU])
api(U, 'MessageBoxW', C.c_int, [W.HWND, W.LPCWSTR, W.LPCWSTR, W.UINT])
api(G, 'CreateFontW', W.HFONT, [C.c_int]*5 + [W.DWORD]*8 + [W.LPCWSTR])
api(G, 'DeleteObject', W.BOOL, [W.HGDIOBJ])
api(U, 'SetTimer', C.c_size_t, [W.HWND, C.c_size_t, W.UINT, C.c_void_p])
api(U, 'KillTimer', W.BOOL, [W.HWND, C.c_size_t])
api(U, 'GetMessageW', C.c_int, [C.POINTER(W.MSG), W.HWND, W.UINT, W.UINT])
api(U, 'TranslateMessage', W.BOOL, [C.POINTER(W.MSG)])
api(U, 'DispatchMessageW', LRESULT, [C.POINTER(W.MSG)])

WM_COMMAND, WM_CLOSE, WM_DESTROY = 0x111, 0x10, 2
WM_APP = 0x8001
FOLDER = Path(os.environ.get('LOCALAPPDATA', Path.home())) / 'MouseMacroStocazzSuperpower'


class Panel:
    def __init__(self):
        self.hwnd = None
        self.controls = {}
        self.queue = queue.SimpleQueue()
        self.repeats = 1
        self.speed = 1.0
        self.next_tab = True
        self.slow = False
        self.fonts = []
        self.closing = False
        self.dialog_open = False
        self.trace_saved = None
        self.settings = {}
        FOLDER.mkdir(parents=True, exist_ok=True)
        try:
            self.settings = json.loads((FOLDER / 'panel-v016.json').read_text('utf-8'))
        except (OSError, ValueError):
            pass
        self.proc = WNDPROC(self.wndproc)
        self.instance = K.GetModuleHandleW(None)
        wc = WNDCLASS(0, self.proc, 0, 0, self.instance, None,
                      U.LoadCursorW(None, C.c_void_p(32512)), W.HBRUSH(16), None, 'MouseMacroCompact016')
        if not U.RegisterClassW(C.byref(wc)):
            raise C.WinError()
        dpi = U.GetDpiForSystem()
        scale = dpi / 96
        width, height = round(356 * scale), round(254 * scale)
        rect = W.RECT(0, 0, width, height)
        self.style = 0x00C80000  # WS_CAPTION | WS_SYSMENU; fixed compact size
        self.exstyle = 0x08040008  # NOACTIVATE | APPWINDOW | TOPMOST
        U.AdjustWindowRectExForDpi(C.byref(rect), self.style, False, self.exstyle, dpi)
        w, h = rect.right - rect.left, rect.bottom - rect.top
        point = self.settings.get('position', [U.GetSystemMetrics(0)-w-20, 20])
        if not isinstance(point, list) or len(point) != 2 or any(type(n) is not int for n in point):
            point = [20, 20]
        x, y = self.clamp(point[0], point[1], w, h)
        self.hwnd = U.CreateWindowExW(self.exstyle, wc.lpszClassName,
            f'Mouse Macro {VERSION} • hcok', self.style, x, y, w, h, None, None, self.instance, None)
        if not self.hwnd:
            raise C.WinError()
        self.session = Session(lambda: WindowsRecorder(self.hwnd, capture_snapshots=False, browser_only=True),
                               WindowsPlayer, lambda: self.post('render'), screen_geometry)
        for cid, cls, text, style in [
            (1, 'STATIC', 'PRONTO', 0), (2, 'STATIC', '', 0),
            (10, 'BUTTON', 'Registra  F9', 0), (11, 'BUTTON', 'Riproduci  F10', 0),
            (20, 'STATIC', 'Ripetizioni', 0), (21, 'BUTTON', '−', 0),
            (22, 'STATIC', '1', 1), (23, 'BUTTON', '+', 0), (24, 'BUTTON', 'Menu', 0),
            (30, 'STATIC', 'Velocità', 0), (31, 'BUTTON', 'Normale', 0),
            (32, 'BUTTON', 'Rapida 2×', 0), (40, 'BUTTON', 'Scheda successiva tra i giri', 3),
            (50, 'STATIC', 'F9 / F10 · Emergenza Ctrl+Alt+F11', 0)]:
            self.controls[cid] = U.CreateWindowExW(0, cls, text, 0x50000000 | style,
                0, 0, 1, 1, self.hwnd, W.HMENU(cid), self.instance, None)
        self.layout(U.GetDpiForWindow(self.hwnd))
        self.hotkeys = GlobalHotkeys(self.hotkey)
        self.hotkeys.start()
        if self.hotkeys.failed:
            self.session.error('Tasti occupati: '+ ', '.join(self.hotkeys.failed)+ '. Chiudi l’altra app.')
        U.SetTimer(self.hwnd, 1, 100, None)  # drains queue, never changes focus/Z order
        self.render()
        U.ShowWindow(self.hwnd, 4)  # SW_SHOWNOACTIVATE
        U.SetWindowPos(self.hwnd, W.HWND(-1), 0, 0, 0, 0, 0x13)  # no move/size/activate

    def clamp(self, x, y, w, h):
        monitor = U.MonitorFromPoint(W.POINT(x, y), 2)
        mi = MONITORINFO(C.sizeof(MONITORINFO))
        U.GetMonitorInfoW(monitor, C.byref(mi))
        work = mi.rcWork
        return max(work.left, min(x, work.right-w)), max(work.top, min(y, work.bottom-h))

    def layout(self, dpi):
        self.dpi = dpi
        s = dpi / 96
        font = G.CreateFontW(-round(14*s), 0, 0, 0, 400, 0, 0, 0, 1, 0, 0, 5, 0, 'Segoe UI')
        self.fonts.append(font)
        boxes = {1:(12,10,332,24), 2:(12,38,332,38), 10:(12,82,158,38), 11:(182,82,162,38),
            20:(12,134,84,24), 21:(104,128,32,32), 22:(141,134,56,24), 23:(202,128,32,32),
            24:(270,128,74,32), 30:(12,175,72,24), 31:(90,170,118,32), 32:(220,170,124,32),
            40:(12,207,332,24), 50:(12,234,332,18)}
        for cid, (x,y,w,h) in boxes.items():
            U.SetWindowPos(self.controls[cid], None, round(x*s),round(y*s),round(w*s),round(h*s),0x14)
            U.SendMessageW(self.controls[cid],0x30,font,1)

    def post(self, action):
        if not self.closing:
            self.queue.put(action)
            if self.hwnd:
                U.PostMessageW(self.hwnd, WM_APP, 0, 0)

    def hotkey(self, code):
        if self.dialog_open and code != HOTKEY_EMERGENCY:
            return
        if code == HOTKEY_EMERGENCY:
            self.session.request_stop()
            self.post('emergency')
        elif code == HOTKEY_PLAY:
            if self.session.state in (State.PLAYING, State.STOPPING):
                self.session.request_stop()
            else:
                self.post('play')
        elif code == HOTKEY_RECORD:
            self.post('record')

    def options(self):
        return PlaybackOptions(repeat_count=self.repeats, speed=self.speed,
            max_pause_speedup=1.0, min_click_hold_seconds=.12,
            min_action_gap_seconds=1.2 if self.slow else .65,
            double_click_seconds=U.GetDoubleClickTime()/1000,
            double_click_gap_seconds=.08, protect_wheel_actions=True)

    def preflight(self, macro):
        if macro.screen and macro.screen != screen_geometry():
            raise ValueError('Schermo o monitor diversi. Ripristinali o registra di nuovo.')
        if not macro.layout and U.GetDpiForWindow(self.hwnd) != 96:
            raise ValueError('Macro precedente senza scala DPI. Registra di nuovo a questa scala.')
        r = window_rect(self.hwnd)
        held = set()
        for event in macro.events:
            if event.kind in BUTTON_OF_DOWN:
                held.add(BUTTON_OF_DOWN[event.kind])
            if (event.kind in BUTTON_OF_DOWN or event.kind == WHEEL or held) and r[0] <= event.x < r[2] and r[1] <= event.y < r[3]:
                raise ValueError('Il pannello copre un gesto della macro. Spostalo e premi F10.')
            if event.kind in BUTTON_OF_UP:
                held.discard(BUTTON_OF_UP[event.kind])

    def render(self):
        state = self.session.state
        active = state in (State.RECORDING, State.PLAYING, State.STOPPING)
        U.SetWindowTextW(self.controls[1], state.value.upper())
        U.SetWindowTextW(self.controls[2], self.session.message)
        U.SetWindowTextW(self.controls[10], 'FERMA  F9' if state == State.RECORDING else 'Registra  F9')
        U.SetWindowTextW(self.controls[11], 'FERMA  F10' if state in (State.PLAYING, State.STOPPING) else 'Riproduci  F10')
        U.EnableWindow(self.controls[10], state not in (State.PLAYING, State.STOPPING))
        U.EnableWindow(self.controls[11], state != State.RECORDING and bool(self.session.macro.events))
        for cid in (21,23,24,31,32,40):
            U.EnableWindow(self.controls[cid], not active)
        U.SetWindowTextW(self.controls[22], str(self.repeats))
        U.SetWindowTextW(self.controls[31], ('✓ ' if self.speed == 1 else '')+'Normale')
        U.SetWindowTextW(self.controls[32], ('✓ ' if self.speed == 2 else '')+'Rapida 2×')
        U.SendMessageW(self.controls[40], 0xF1, int(self.next_tab), 0)
        if self.session.last_trace and state in (State.READY, State.ERROR) and self.trace_saved is not self.session.last_trace:
            self.trace_saved = self.session.last_trace
            try:
                (FOLDER/'ultimo-replay.json').write_text(json.dumps({'version':VERSION,
                    'options':self.options().__dict__ | {'mode':'repeat_count'},
                    'outcome':state.value,'records':self.session.last_trace}, indent=2), 'utf-8')
            except OSError:
                pass

    def drain(self):
        while not self.queue.empty():
            action = self.queue.get()
            if action == 'record':
                self.session.toggle_record()
            elif action == 'play':
                self.session.toggle_play(self.options(), self.next_tab, self.preflight)
            elif action == 'emergency' and self.session.state == State.RECORDING:
                self.session.toggle_record()
        self.render()

    def menu(self):
        menu = U.CreatePopupMenu()
        entries = [(101,'Salva macro…'),(102,'Carica macro…'),(0,''),
            (103, ('✓ ' if self.slow else '')+'Pagine lente: pausa più prudente'),
            (104,'Guida e limiti'),(0,''),(105,'Ripetizioni: 1'),(106,'Ripetizioni: 20')]
        for cid, label in entries:
            U.AppendMenuW(menu, 0 if cid else 0x800, cid, label)
        r = window_rect(self.controls[24])
        try:
            choice = U.TrackPopupMenu(menu, 0x100 | 0x2, r[0], r[3], 0, self.hwnd, None)
        finally:
            U.DestroyMenu(menu)
        if choice in (101,102):
            from macro.win_dialogs import ask_save_path, ask_open_path
            self.dialog_open = True
            try:
                path = ask_save_path('Salva macro', owner=self.hwnd) if choice == 101 else ask_open_path('Carica macro', owner=self.hwnd)
            finally:
                self.dialog_open = False
            if path:
                self.session.save(path) if choice == 101 else self.session.load(path)
        elif choice == 103:
            self.slow = not self.slow
            self.session.message = 'Pagine lente attive: nessun rilevamento automatico del caricamento.' if self.slow else 'Pausa standard fra le azioni.'
        elif choice == 104:
            self.dialog_open = True
            try:
                U.MessageBoxW(self.hwnd, '1. Attiva Chrome o Firefox; registra un solo cavallo con F9.\n'
                    '2. Ferma con F9 senza cambiare scheda durante la registrazione.\n'
                    '3. Scegli le ripetizioni e premi F10 dalla prima scheda.\n'
                    'Scheda successiva invia Ctrl+Tab soltanto TRA i giri.\n'
                    'Non registra i tasti della tastiera. Non chiude schede.\n\n'
                    'F10 ferma; Ctrl+Alt+F11 è lo stop di emergenza.\n'
                    'Sposta il pannello fuori dai gesti PRIMA di iniziare.\n'
                    'Mantieni posizione, scala e zoom del browser.\n'
                    'Rapida 2× accelera i movimenti, conserva le pause lunghe.\n'
                    'Per pagine lente registra attese sufficienti e abilita Pagine lente.\n'
                    'Le pause non dimostrano che il sito abbia accettato un clic.\n'
                    'Non è stato verificato su account Howrse o con SentinelOne/SAC.',
                    f'Mouse Macro {VERSION} · hcok', 0x40)
            finally:
                self.dialog_open = False
        elif choice in (105,106):
            self.repeats = 1 if choice == 105 else 20
        self.render()

    def save_position(self):
        if self.hwnd:
            r = window_rect(self.hwnd)
            (FOLDER/'panel-v016.json').write_text(json.dumps({'position':r[:2]}), 'utf-8')

    def wndproc(self, hwnd, msg, wp, lp):
        try:
            if msg == 0x21:  # WM_MOUSEACTIVATE: don't steal Chrome's focus
                return 3  # MA_NOACTIVATE
            if msg in (WM_APP, 0x113) and self.hwnd and hasattr(self, 'session'):
                self.drain()
                return 0
            if msg == WM_COMMAND and hasattr(self, 'session'):
                cid = wp & 0xffff
                if cid == 10:
                    self.post('record')
                elif cid == 11:
                    if self.session.state in (State.PLAYING, State.STOPPING):
                        self.session.request_stop()
                    else:
                        self.post('play')
                elif self.session.state in (State.READY, State.ERROR):
                    if cid == 21: self.repeats = max(1, self.repeats-1)
                    if cid == 23: self.repeats = min(999, self.repeats+1)
                    if cid == 31: self.speed = 1
                    if cid == 32: self.speed = 2
                    if cid == 40: self.next_tab = not self.next_tab
                    if cid == 24: self.menu()
                    self.render()
                return 0
            if msg == 0x2E0 and self.hwnd:  # WM_DPICHANGED
                rect = C.cast(lp, C.POINTER(W.RECT)).contents
                U.SetWindowPos(hwnd,None,rect.left,rect.top,rect.right-rect.left,rect.bottom-rect.top,0x14)
                self.layout(wp & 0xffff)
                self.save_position()
                return 0
            if msg == 0x232 and self.hwnd:  # WM_EXITSIZEMOVE
                self.save_position()
            if msg == WM_CLOSE and self.hwnd:
                self.closing = True
                self.save_position()
                U.KillTimer(hwnd,1)
                self.session.close()
                self.hotkeys.stop()
                U.DestroyWindow(hwnd)
                return 0
            if msg == WM_DESTROY:
                for font in self.fonts:
                    G.DeleteObject(font)
                U.PostQuitMessage(0)
                return 0
        except Exception as error:
            (FOLDER/'errore.log').write_text(traceback.format_exc(), 'utf-8')
            if hasattr(self,'session'):
                self.session.request_stop()
                self.session.error(error)
        return U.DefWindowProcW(hwnd,msg,wp,lp)

    def run(self):
        msg = W.MSG()
        while U.GetMessageW(C.byref(msg), None, 0, 0) > 0:
            U.TranslateMessage(C.byref(msg))
            U.DispatchMessageW(C.byref(msg))


def main():
    mutex = K.CreateMutexW(None, False, 'Local\\MouseMacroCompact016')
    if K.GetLastError() == 183:
        # Second launch leaves the original session and its global hotkeys alone.
        K.CloseHandle(mutex)
        return
    try:
        Panel().run()
    except Exception:
        FOLDER.mkdir(parents=True,exist_ok=True)
        (FOLDER/'errore-avvio.log').write_text(traceback.format_exc(),'utf-8')
        U.MessageBoxW(None,'Avvio non riuscito. Dettagli in '+str(FOLDER/'errore-avvio.log'), 'Mouse Macro',0x10)
        raise
    finally:
        K.CloseHandle(mutex)


if __name__ == '__main__':
    main()
