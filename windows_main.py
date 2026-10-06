"""Approved compact/expanded Windows UI, native controls and offline runtime."""
from __future__ import annotations

import ctypes as C
from ctypes import wintypes as W
import json
import os
from pathlib import Path
import queue
import subprocess
import sys
import threading
import traceback
import time
from windows_visual import Theme, Canvas, COLORS, Paint, DrawItem, SKINS, CURRENT, apply_skin

from macro.windows_backend import (WindowsRecorder, WindowsPlayer, GlobalHotkeys,
    HOTKEY_RECORD, HOTKEY_PLAY, HOTKEY_EMERGENCY, screen_geometry, window_rect)
from macro.session import Session, State, VERSION, validate_gestures
from macro.engine import PlaybackOptions
from macro import updater
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
api(U, 'GetWindowLongPtrW', C.c_ssize_t, [W.HWND, C.c_int])
api(U, 'SetWindowLongPtrW', C.c_ssize_t, [W.HWND, C.c_int, C.c_ssize_t])
api(U, 'SetLayeredWindowAttributes', W.BOOL, [W.HWND, W.DWORD, W.BYTE, W.DWORD])
api(U, 'SendMessageW', LRESULT, [W.HWND, W.UINT, W.WPARAM, W.LPARAM])
api(U, 'PostMessageW', W.BOOL, [W.HWND, W.UINT, W.WPARAM, W.LPARAM])
api(U, 'SetWindowTextW', W.BOOL, [W.HWND, W.LPCWSTR])
api(U, 'GetWindowTextW', C.c_int, [W.HWND, W.LPWSTR, C.c_int])
api(U, 'GetFocus', W.HWND, [])
api(U, 'WindowFromPoint', W.HWND, [W.POINT])
api(U, 'EnableWindow', W.BOOL, [W.HWND, W.BOOL])
api(U, 'ShowWindow', W.BOOL, [W.HWND, C.c_int])
api(U, 'CreatePopupMenu', W.HMENU, [])
api(U, 'AppendMenuW', W.BOOL, [W.HMENU, W.UINT, C.c_size_t, W.LPCWSTR])
api(U, 'TrackPopupMenu', C.c_int, [W.HMENU, W.UINT, C.c_int, C.c_int, C.c_int, W.HWND, C.c_void_p])
api(U, 'DestroyMenu', W.BOOL, [W.HMENU])
api(U, 'SetForegroundWindow', W.BOOL, [W.HWND])
api(G, 'SetTextColor', W.DWORD, [W.HDC, W.DWORD])
api(G, 'SetBkColor', W.DWORD, [W.HDC, W.DWORD])
api(G, 'CreateSolidBrush', W.HBRUSH, [W.DWORD])
api(U, 'DestroyWindow', W.BOOL, [W.HWND])
api(C.windll.uxtheme,'SetWindowTheme',C.c_long,[W.HWND,W.LPCWSTR,W.LPCWSTR])
api(U, 'LoadImageW', W.HANDLE, [W.HINSTANCE,W.LPCWSTR,W.UINT,C.c_int,C.c_int,W.UINT])
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
api(U, 'IsDialogMessageW', W.BOOL, [W.HWND, C.POINTER(W.MSG)])
api(U, 'SetWindowRgn', C.c_int, [W.HWND, W.HRGN, W.BOOL])
api(G, 'CreateRoundRectRgn', W.HRGN, [C.c_int]*6)
api(U, 'GetCursorPos', W.BOOL, [C.POINTER(W.POINT)])
api(U, 'GetMessageW', C.c_int, [C.POINTER(W.MSG), W.HWND, W.UINT, W.UINT])
api(U, 'TranslateMessage', W.BOOL, [C.POINTER(W.MSG)])
api(U, 'DispatchMessageW', LRESULT, [C.POINTER(W.MSG)])

WM_COMMAND, WM_CLOSE, WM_DESTROY = 0x111, 0x10, 2
WM_APP = 0x8001
ACTIVE_SIZE = (288, 64)  # logical pixels; the normal panel remains available at rest
ACTIVE_ALPHA = 242  # 95% opaque: a slight transparency, including the controls
FOLDER = Path(os.environ.get('LOCALAPPDATA', Path.home())) / 'MouseMacroStocazzSuperpower'


def parse_repeats(text):
    text = text.strip()
    if not text or not text.isascii() or not text.isdecimal() or not 1 <= int(text) <= 999:
        raise ValueError('Imposta da 1 a 999 ripetizioni.')
    return int(text)


class Panel:
    def __init__(self):
        self.hwnd = None
        self.controls = {}
        self.queue = queue.SimpleQueue()
        self.repeats = 1
        self.speed = 1.0
        self.next_tab = False
        self.slow = False
        self.human = False
        self.closing = False
        self.dialog_open = False
        self.trace_saved = None
        self.settings = {}
        self.expanded = False
        self.active_view = False
        self.normal_position = None
        self.active_position = None
        self.play_started = None
        self.repeat_font = None
        self.record_started = None
        self.hover = None
        self.last_view = None
        self.update = {'state': 'unknown', 'latest': None, 'release': None}
        self.edit_brush = None
        FOLDER.mkdir(parents=True, exist_ok=True)
        try:
            self.settings = json.loads((FOLDER / 'panel-v016.json').read_text('utf-8'))
        except (OSError, ValueError):
            pass
        if not isinstance(self.settings, dict):
            self.settings = {}
        apply_skin(self.settings.get('skin'))
        self.theme = Theme()
        self.proc = WNDPROC(self.wndproc)
        self.instance = K.GetModuleHandleW(None)
        icon = U.LoadImageW(None,str(Path(__file__).resolve().parent/'assets'/'icon.ico'),1,0,0,0x10|0x40)
        wc = WNDCLASS(0, self.proc, 0, 0, self.instance, icon,
                      U.LoadCursorW(None, C.c_void_p(32512)), W.HBRUSH(16), None, 'MouseMacroSuperpower017')
        if not U.RegisterClassW(C.byref(wc)):
            raise C.WinError()
        dpi = U.GetDpiForSystem()
        scale = dpi / 96
        self.dpi = dpi
        width, height = round(340 * scale), round(600 * scale)
        rect = W.RECT(0, 0, width, height)
        self.style = 0x82000000  # WS_POPUP | WS_CLIPCHILDREN; custom drawn chrome
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
        self.session = Session(lambda: WindowsRecorder(self.hwnd, capture_snapshots=False),
                               WindowsPlayer, lambda: self.post('render'), screen_geometry)
        # Status text children remain available to accessibility/QA without
        # overlaying the vector card. All actions are actual Win32 buttons.
        for cid, label in [(1,'PRONTO'),(2,self.session.message),(3,'0'),(4,'00:00.000')]:
            self.controls[cid] = U.CreateWindowExW(0,'STATIC',label,0x40000000,
                0,0,1,1,self.hwnd,W.HMENU(cid),self.instance,None)
        self.controls[22] = U.CreateWindowExW(0x200,'EDIT','1',0x50012081,
            0,0,1,1,self.hwnd,W.HMENU(22),self.instance,None)  # tabstop, number, centered
        U.SendMessageW(self.controls[22],0xC5,3,0)  # EM_LIMITTEXT
        labels = {10:'Registra · F9',11:'Riproduci · F10',21:'−',23:'+',24:'Opzioni',
                  25:'Preset 20',31:'Normale',32:'Rapida 2×',40:'Scheda successiva tra i giri',
                  41:'Pagine lente',42:'Movimento umano',101:'Salva macro',102:'Carica macro',104:'Guida',
                  110:'Emergenza: Ctrl+Alt+F11',201:'Riduci a icona',202:'Espandi opzioni',203:'Chiudi',
                  204:'Cambia skin',205:'Aggiornamenti'}
        labels[12] = 'Ferma'
        for cid, label in labels.items():
            self.controls[cid] = U.CreateWindowExW(0,'BUTTON',label,0x5001000B,
                0,0,1,1,self.hwnd,W.HMENU(cid),self.instance,None)
        for control in self.controls.values():C.windll.uxtheme.SetWindowTheme(control,'','')
        self.layout(U.GetDpiForWindow(self.hwnd))
        self.hotkeys = GlobalHotkeys(self.hotkey)
        self.hotkeys.start()
        if self.hotkeys.failed:
            self.session.error('Tasti occupati: '+ ', '.join(self.hotkeys.failed)+ '. Chiudi l’altra app.')
        U.SetTimer(self.hwnd, 1, 100, None)  # drains queue, never changes focus/Z order
        self.render()
        U.ShowWindow(self.hwnd, 4)  # SW_SHOWNOACTIVATE
        U.SetWindowPos(self.hwnd, W.HWND(-1), 0, 0, 0, 0, 0x13)  # no move/size/activate
        if self.settings.get('check_updates', True):
            self.check_updates()

    def clamp(self, x, y, w, h):
        monitor = U.MonitorFromPoint(W.POINT(x, y), 2)
        mi = MONITORINFO(C.sizeof(MONITORINFO))
        U.GetMonitorInfoW(monitor, C.byref(mi))
        work = mi.rcWork
        return max(work.left, min(x, work.right-w)), max(work.top, min(y, work.bottom-h))

    def layout(self, dpi):
        self.dpi = dpi
        scale = dpi / 96
        width,height = ACTIVE_SIZE if self.active_view else (640,608) if self.expanded else (340,600)
        self.width,self.height = width,height
        r = window_rect(self.hwnd)
        x,y = self.clamp(r[0],r[1],round(width*scale),round(height*scale))
        U.SetWindowPos(self.hwnd,None,x,y,round(width*scale),round(height*scale),0x14)
        # Windows owns this region after SetWindowRgn succeeds.
        region = G.CreateRoundRectRgn(0,0,round(width*scale)+1,round(height*scale)+1,round(36*scale),round(36*scale))
        if not U.SetWindowRgn(self.hwnd,region,True): G.DeleteObject(region)
        boxes = {12:(208,12,72,40)} if self.active_view else {201:(width-98,7,28,28),202:(width-66,7,28,28),203:(width-34,7,28,28),
                                                  204:(width-130,7,28,28),205:(width-162,7,28,28)}
        if self.active_view:
            pass
        elif self.expanded:
            boxes.update({10:(16,244,298,64),11:(326,244,298,64),24:(16,324,608,44),
                21:(32,410,34,38),22:(66,410,46,38),23:(112,410,34,38),25:(32,457,114,30),
                31:(192,402,162,38),32:(192,442,162,38),
                40:(386,373,220,38),41:(386,413,220,38),42:(386,453,220,38),
                101:(192,495,162,38),102:(366,495,240,38),
                104:(20,558,104,34),110:(346,562,266,30)})
            boxes[104]=(20,558,104,34);boxes[110]=(346,562,266,30)
        else:
            boxes.update({10:(16,322,308,64),11:(16,398,308,64),24:(16,478,308,44),
                          104:(20,538,98,34),110:(146,535,178,46)})
        self.boxes = boxes
        font = G.CreateFontW(-round(18*scale),0,0,0,600,0,0,0,1,0,0,5,0,'Segoe UI')
        U.SendMessageW(self.controls[22],0x30,font,1)  # WM_SETFONT
        if self.repeat_font:
            G.DeleteObject(self.repeat_font)
        self.repeat_font = font
        for cid,hwnd in self.controls.items():
            if cid in boxes:
                x1,y1,w,h=boxes[cid]
                U.SetWindowPos(hwnd,None,round(x1*scale),round(y1*scale),round(w*scale),round(h*scale),0x14)
                U.ShowWindow(hwnd,4)
            else:U.ShowWindow(hwnd,0)
        U.SetWindowTextW(self.controls[202], 'Riduci opzioni' if self.expanded else 'Espandi opzioni')
        U.InvalidateRect(self.hwnd,None,False)

    def active_work_area(self):
        r = window_rect(self.hwnd)
        monitor = U.MonitorFromPoint(W.POINT((r[0]+r[2])//2, (r[1]+r[3])//2), 2)
        mi = MONITORINFO(C.sizeof(MONITORINFO))
        if not U.GetMonitorInfoW(monitor, C.byref(mi)):
            raise C.WinError()
        return mi.rcWork

    def set_active_view(self, active):
        if self.active_view == active:
            return
        if active:
            self.normal_position = window_rect(self.hwnd)[:2]
            work = self.active_work_area()
            self.active_view = True
            self.layout(self.dpi)
            w,h = (round(n*self.dpi/96) for n in ACTIVE_SIZE)
            x,y = self.active_position or ((work.left+work.right-w)//2, (work.top+work.bottom-h)//2)
            x,y = self.clamp(x,y,w,h)
            U.SetWindowPos(self.hwnd,None,x,y,w,h,0x14)
            U.SetWindowLongPtrW(self.hwnd,-20,self.exstyle | 0x80000)  # WS_EX_LAYERED
            if not U.SetLayeredWindowAttributes(self.hwnd,0,ACTIVE_ALPHA,2):
                error = C.WinError()
                self.set_active_view(False)
                raise error
            U.ShowWindow(self.hwnd,4)  # also restore a minimized panel without taking focus
        else:
            self.active_position = window_rect(self.hwnd)[:2]
            U.SetLayeredWindowAttributes(self.hwnd,0,255,2)
            U.SetWindowLongPtrW(self.hwnd,-20,self.exstyle)
            self.active_view = False
            self.layout(self.dpi)
            x,y = self.clamp(*(self.normal_position or [20,20]),
                             round(self.width*self.dpi/96),round(self.height*self.dpi/96))
            U.SetWindowPos(self.hwnd,None,x,y,0,0,0x15)
        self.last_view = None

    def paint_active(self, c):
        state = self.session.state
        recording = state == State.RECORDING
        color = COLORS['record'] if recording else COLORS['play']
        c.horse('registrazione' if recording else 'riproduzione',6,12,36,40)
        label = 'Registrazione' if recording else 'Arresto…' if state == State.STOPPING else 'Riproduzione'
        c.text(label,48,4,154,24,16,color,True)
        if recording:
            count,duration = self.metrics()
            detail = f'{count} eventi · {duration.split(".")[0]}'
        else:
            seconds = max(0,int(time.monotonic()-(self.play_started or time.monotonic())))
            detail = f'{self.session.completed}/{self.repeats} giri · {seconds//60:02d}:{seconds%60:02d}'
        c.text(detail,48,28,154,19,14,COLORS['text'])
        c.text('F9 stop' if recording else 'F10 stop · Ctrl+Alt+F11',48,46,154,16,11,COLORS['muted'])

    def paint(self, hwnd):
        ps=Paint();hdc=U.BeginPaint(hwnd,C.byref(ps))
        rect=W.RECT();U.GetClientRect(hwnd,C.byref(rect))
        c=Canvas(self.theme,hdc,rect.right,rect.bottom,self.dpi/96,text_hint=4 if self.active_view else 5)
        try:
            w,h=self.width,self.height
            c.clear(COLORS['background'])
            c.rounded(1,1,w-2,h-2,18,COLORS['background'],COLORS['border'])
            if self.active_view:
                self.paint_active(c)
                return
            c.rounded(3,3,w-6,86,16,COLORS['header_top'],bottom=COLORS['header_bottom'])
            c.horse('pronto',10,30,58,54)
            tx=76
            c.text('Mouse Macro',tx,32,w-tx-12,26,22,COLORS['header_text'],bold=True,display=True)
            c.text('Stocazz',tx,57,85,24,20,COLORS['header_a'],True,display=True)
            c.text('Superpower',tx+86,57,w-tx-98,24,20,COLORS['header_b'],True,display=True)
            state=self.session.state
            horse={State.RECORDING:'registrazione',State.PLAYING:'riproduzione',State.STOPPING:'riproduzione',State.ERROR:'errore'}.get(state,'pronto')
            color={'pronto':COLORS['ready'],'registrazione':COLORS['record'],'riproduzione':COLORS['play'],'errore':COLORS['error']}[horse]
            c.rounded(16,102,w-32,126,14,COLORS['surface'],COLORS['border'],bottom=COLORS['surface_bottom'])
            c.ellipse(32,125,16,16,color)
            c.text(state.value.capitalize(),58,115,226 if self.expanded else 156,34,22,color if state==State.ERROR else COLORS['text'],True)
            c.text(self.session.message,32,152,268 if self.expanded else 172,64,14,
                   COLORS['error'] if state==State.ERROR else COLORS['muted'],wrap=True)
            count,duration=self.metrics()
            if self.expanded:
                for x in (314,386):c.line(x,127,x,207,COLORS['border'])
                c.text('Eventi',328,127,66,24,13,COLORS['muted'])
                c.text(count,328,154,60,34,22,bold=True)
                c.text('Durata',402,127,110,24,13,COLORS['muted'])
                c.text(duration,402,154,113,34,18,bold=True)
                c.horse(horse,508,105,114,120)
                c.rounded(16,324,w-32,220,14,COLORS['surface'],COLORS['border'])
                c.text('Ripetizioni',32,376,140,26,14,bold=True)
                c.text('Velocità',192,376,158,26,14,bold=True)
                for x in (172,368):c.line(x,384,x,484,COLORS['border'])
                c.rounded(66,410,46,38,1,COLORS['input'],COLORS['border'])
                c.line(16,550,w-16,550,COLORS['border'])
            else:
                c.horse(horse,207,118,112,104)
                for x,cw,label,value in [(16,148,'Eventi',count),(176,148,'Durata',duration)]:
                    c.rounded(x,240,cw,66,14,COLORS['surface'],COLORS['border'])
                    c.text(label,x+16,247,cw-28,22,14,COLORS['muted'])
                    c.text(value,x+16,267,cw-24,30,22 if label=='Eventi' else 19,bold=True)
            c.text('hcok',w-57,h-19,44,14,11,COLORS['muted'],align=2)
        finally:c.close();U.EndPaint(hwnd,C.byref(ps))

    def metrics(self):
        if self.session.state==State.RECORDING and self.session.recorder:
            count=self.session.recorder.current_event_count
            duration=time.monotonic()-(self.record_started or time.monotonic())
        else:
            count=len(self.session.macro.events)
            duration=self.session.macro.events[-1].t if count else 0
        millis=max(0,round(duration*1000))
        return str(count),f'{millis//60000:02d}:{(millis//1000)%60:02d}.{millis%1000:03d}'

    def draw_control(self,item):
        cid=item.id
        if cid not in self.boxes:return
        scale=self.dpi/96
        w=(item.rect.right-item.rect.left)/scale;h=(item.rect.bottom-item.rect.top)/scale
        c=Canvas(self.theme,item.hdc,item.rect.right-item.rect.left,item.rect.bottom-item.rect.top,scale,text_hint=4 if self.active_view else 5)
        enabled=bool(U.IsWindowEnabled(item.hwnd));hover=cid==self.hover and enabled
        pressed=bool(item.state&1);fg=COLORS['text'] if enabled else COLORS['faded']
        fg_accent=COLORS['on_accent'] if enabled else COLORS['faded']
        try:
            c.clear(COLORS['chrome'] if cid in (201,202,203,204,205) else COLORS['surface'] if cid in (21,23,25,31,32,40,41,101,102) else COLORS['background'])
            if cid == 12:
                c.rounded(1,1,w-2,h-2,12,COLORS['record'] if self.session.state==State.RECORDING else COLORS['play'],COLORS['border'])
                c.icon('stop',6,12,16,fg_accent)
                c.text('Stop',24,0,w-26,h,13,fg_accent,True)
            elif cid in (10,11):
                key='record' if cid==10 else 'play'
                bg=COLORS[key] if enabled else COLORS['disabled']
                if hover:bg=COLORS['record_hover'] if cid==10 else COLORS['play_hover']
                if pressed and enabled:bg=COLORS['record_pressed'] if cid==10 else COLORS['play_pressed']
                c.rounded(1,1,w-2,h-2,16,bg,COLORS['record_edge'] if cid==10 and enabled else COLORS['border'],bottom=bg if not enabled else (COLORS['record_bottom'] if cid==10 else COLORS['play_bottom']))
                stopping=self.session.state==State.RECORDING if cid==10 else self.session.state in (State.PLAYING,State.STOPPING)
                icon='stop' if stopping else key if cid==10 else 'play'
                label=('Ferma' if stopping else 'Registra' if cid==10 else 'Riproduci')+(' · F9' if cid==10 else ' · F10')
                c.icon(icon,41 if cid==10 else 30,14,36,fg_accent)
                c.text(label,80 if cid==10 else 66,0,w-90 if cid==10 else w-76,h,18,fg_accent,True)
            elif cid==24:
                c.rounded(1,1,w-2,h-2,12,COLORS['surface_hover'] if hover else COLORS['surface'],COLORS['border'])
                c.icon('gear',16,10,24,fg)
                c.text('Opzioni',50,0,w-85,h,16,fg,True)
                cx=w-24;cy=h/2
                d=-1 if self.expanded else 1
                c.line(cx-6,cy-3*d,cx,cy+3*d,fg,2);c.line(cx,cy+3*d,cx+6,cy-3*d,fg,2)
            elif cid in (31,32):
                selected=self.speed==(1 if cid==31 else 2)
                if hover:c.rounded(1,1,w-2,h-2,10,COLORS['alt'])
                c.ellipse(6,11,16,16,COLORS['record'] if selected and enabled else fg,not selected)
                if selected:c.ellipse(11,16,6,6,COLORS['text'])
                c.text('Normale' if cid==31 else 'Rapida 2×',32,0,w-38,h,14,fg)
            elif cid in (40,41,42):
                on={40:self.next_tab,41:self.slow,42:self.human}[cid]
                title,hint={40:('Cambia scheda','Ctrl+Tab tra i giri'),41:('Pagine lente','Pause più lunghe'),
                            42:('Movimento umano','Percorsi e pause variabili')}[cid]
                c.text(title,0,1,w-55,20,14,fg,True)
                c.text(hint,0,21,w-52,16,11,COLORS['muted'] if enabled else fg)
                c.rounded(w-48,9,44,22,11,COLORS['record'] if on and enabled else COLORS['disabled'])
                c.ellipse(w-24 if on else w-44,12,16,16,fg)
            elif cid==104:
                c.icon('help',4,7,22,COLORS['record']);c.text('Guida',34,0,w-38,h,14,COLORS['record'],True)
            elif cid==110:
                c.icon('warning',2,(h-24)/2,24,COLORS['warning'])
                c.text('Emergenza: Ctrl+Alt+F11' if self.expanded else 'Emergenza:\nCtrl+Alt+F11',31,0,w-33,h,13,COLORS['warning'],wrap=True)
            elif cid==204:
                color=COLORS['header_text'] if hover else COLORS['header_muted']
                if hover:c.rounded(0,0,w,h,7,COLORS['chrome_hover'])
                c.ellipse(6,6,16,16,color,True)
                for dx,dy in ((10,10),(15,10),(12.5,16)):c.ellipse(dx-1.5,dy-1.5,3,3,color)
            elif cid==205:
                if hover:c.rounded(0,0,w,h,7,COLORS['chrome_hover'])
                dot={'current':COLORS['dot_ok'],'available':COLORS['dot_new']}.get(self.update['state'],COLORS['dot_off'])
                c.ellipse(8,8,12,12,dot)
                if self.update['state']=='available':c.ellipse(5,5,18,18,dot,True)
            elif cid in (201,202,203):
                color=COLORS['header_text'] if hover else COLORS['header_muted']
                if hover:c.rounded(0,0,w,h,7,COLORS['error'] if cid==203 else COLORS['chrome_hover'])
                if cid==201:c.line(8,15,20,15,color,1.5)
                elif cid==202:
                    for a,b,d,e in [(8,8,20,8),(20,8,20,20),(20,20,8,20),(8,20,8,8)]:c.line(a,b,d,e,color,1.5)
                else:c.line(8,8,20,20,color,1.5);c.line(20,8,8,20,color,1.5)
            else:
                c.rounded(1,1,w-2,h-2,9,COLORS['button_hover'] if hover else COLORS['button'],COLORS['border'])
                label={21:'−',23:'+',25:'Preset 20',101:'Salva macro',102:'Carica macro'}[cid]
                if cid in (101,102):
                    c.icon('save' if cid==101 else 'load',12,(h-20)/2,20,fg)
                    c.text(label,40,0,w-44,h,14,fg,bold=True)
                else:c.text(label,0,0,w,h,20 if cid in (21,23) else 13,fg,align=1)
            if item.state&16 and enabled:self.focus_ring(c,w,h)
        finally:c.close()

    def focus_ring(self,c,w,h):
        p=c.path(3,3,w-6,h-6,10)
        from windows_visual import D, ptrcall, argb
        pen=ptrcall(D.GdipCreatePen1,argb(COLORS['warning']),2,2)
        D.GdipDrawPath(c.g,pen,p);D.GdipDeletePen(pen);D.GdipDeletePath(p)

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
            # Ordinary interaction scales at 2x; only genuine long waits stay at 1x.
            # Slow pages retain the previous conservative timing policy.
            pause_threshold_seconds=.35 if self.slow else 2.0,
            max_pause_speedup=1.0, min_click_hold_seconds=.12,
            min_action_gap_seconds=1.2 if self.slow else .65/self.speed,
            double_click_seconds=U.GetDoubleClickTime()/1000,
            double_click_gap_seconds=.08, protect_wheel_actions=True, humanize=self.human)

    def preflight(self, macro):
        if macro.screen and macro.screen != screen_geometry():
            raise ValueError('Schermo o monitor diversi. Ripristinali o registra di nuovo.')
        r = window_rect(self.hwnd)
        # The bar starts at the center. If that covers a recorded gesture, find
        # the closest free position rather than putting the overlay over a click.
        blocked = []
        held = set()
        previous = None
        for event in macro.events:
            if event.kind in BUTTON_OF_DOWN:
                held.add(BUTTON_OF_DOWN[event.kind])
            if event.kind in BUTTON_OF_DOWN or event.kind == WHEEL or held:
                x,y = (previous.x,previous.y) if previous is not None and held and event.kind not in BUTTON_OF_DOWN else (event.x,event.y)
                blocked.append((min(x,event.x),min(y,event.y),max(x,event.x)+1,max(y,event.y)+1))
            if event.kind in BUTTON_OF_UP:
                held.discard(BUTTON_OF_UP[event.kind])
            previous = event
        def clear(rect):
            return not any(rect[0]<b[2] and b[0]<rect[2] and rect[1]<b[3] and b[1]<rect[3] for b in blocked)
        if clear(r):
            return
        if self.active_view:
            work = self.active_work_area()
            w,h = r[2]-r[0],r[3]-r[1]
            xs = {work.left,work.right-w,r[0]}
            ys = {work.top,work.bottom-h,r[1]}
            for b in blocked:
                xs.update((b[0]-w-8,b[2]+8))
                ys.update((b[1]-h-8,b[3]+8))
            # Candidate count is bounded even with long recordings; existing
            # placement is preferred, then nearby rows and screen edges.
            xs = set(sorted({max(work.left,min(x,work.right-w)) for x in xs},key=lambda x:abs(x-r[0]))[:32]) | {work.left,work.right-w}
            ys = set(sorted({max(work.top,min(y,work.bottom-h)) for y in ys},key=lambda y:abs(y-r[1]))[:32]) | {work.top,work.bottom-h}
            positions = sorted(((x,y) for x in xs for y in ys),key=lambda p:(p[0]-r[0])**2+(p[1]-r[1])**2)
            for x,y in positions:
                if clear((x,y,x+w,y+h)):
                    if not U.SetWindowPos(self.hwnd,None,x,y,0,0,0x15):
                        raise C.WinError()
                    if clear(window_rect(self.hwnd)):
                        return
        raise ValueError('Non c’è spazio libero per il pannello. Sposta i bersagli e registra di nuovo.')

    def render(self):
        state = self.session.state
        if state == State.RECORDING and self.record_started is None: self.record_started = time.monotonic()
        elif state != State.RECORDING: self.record_started = None
        count,duration=self.metrics()
        U.SetWindowTextW(self.controls[3],count)
        U.SetWindowTextW(self.controls[4],duration)
        U.SetWindowTextW(self.hwnd,f'Mouse Macro {VERSION} · hcok · {state.value} · {count} eventi · {duration}')
        active = state in (State.RECORDING, State.PLAYING, State.STOPPING)
        if not active and self.active_view:
            self.set_active_view(False)
        if state == State.PLAYING and self.play_started is None:
            self.play_started = time.monotonic()
        elif not active:
            self.play_started = None
        U.SetWindowTextW(self.controls[12], 'Stop · F9' if state == State.RECORDING else 'Stop · F10')
        U.EnableWindow(self.controls[12], active and state != State.STOPPING)
        U.SetWindowTextW(self.controls[1], state.value.upper())
        U.SetWindowTextW(self.controls[2], self.session.message)
        U.SetWindowTextW(self.controls[10], 'FERMA  F9' if state == State.RECORDING else 'Registra  F9')
        U.SetWindowTextW(self.controls[11], 'FERMA  F10' if state in (State.PLAYING, State.STOPPING) else 'Riproduci  F10')
        U.EnableWindow(self.controls[10], state not in (State.PLAYING, State.STOPPING))
        try:
            validate_gestures(self.session.macro.events)
            valid = True
        except ValueError: valid = False
        U.EnableWindow(self.controls[11], state != State.RECORDING and valid)
        for cid in (21,22,23,24,25,31,32,40,41,42,101,102,104,202,204,205):
            U.EnableWindow(self.controls[cid], not active)
        if U.GetFocus() != self.controls[22]:
            self.sync_repeats()
        U.SetWindowTextW(self.controls[31], ('✓ ' if self.speed == 1 else '')+'Normale')
        U.SetWindowTextW(self.controls[32], ('✓ ' if self.speed == 2 else '')+'Rapida 2×')
        U.SetWindowTextW(self.controls[40], 'Scheda successiva tra i giri: '+('attivo' if self.next_tab else 'disattivato'))
        U.SetWindowTextW(self.controls[41], 'Pagine lente: '+('attivo' if self.slow else 'disattivato'))
        U.SetWindowTextW(self.controls[42], 'Movimento umano: '+('attivo' if self.human else 'disattivato'))
        U.EnableWindow(self.controls[101], not active and valid)
        view=(state,self.session.message,self.metrics(),self.repeats,self.speed,self.next_tab,self.slow,self.human,
              int(time.monotonic()-(self.play_started or time.monotonic())),CURRENT['skin'],self.update['state'])
        if view != self.last_view:
            self.last_view=view
            U.InvalidateRect(self.hwnd,None,False)
            for hwnd in self.controls.values():U.InvalidateRect(hwnd,None,False)
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
            if isinstance(action, tuple):
                self.worker_result(*action)
            elif action == 'record':
                if self.session.state in (State.READY,State.ERROR):
                    self.set_active_view(True)
                self.session.toggle_record()
            elif action == 'play':
                if self.session.state in (State.READY,State.ERROR):
                    try:
                        self.repeats = self.read_repeats()
                    except ValueError as error:
                        self.session.error(error)
                        continue
                    self.set_active_view(True)
                self.session.toggle_play(self.options(), self.next_tab, self.preflight)
            elif action == 'emergency' and self.session.state == State.RECORDING:
                self.session.toggle_record()
        self.render()

    def set_skin(self, name):
        name = apply_skin(name)
        self.theme.load_images()
        if self.edit_brush:
            G.DeleteObject(self.edit_brush)
        self.edit_brush = None
        self.settings['skin'] = name
        self.write_settings()
        self.last_view = None
        U.InvalidateRect(self.hwnd,None,True)
        for hwnd in self.controls.values():U.InvalidateRect(hwnd,None,True)

    def write_settings(self):
        try:
            (FOLDER/'panel-v016.json').write_text(json.dumps(self.settings), 'utf-8')
        except OSError:
            pass  # an unwritable settings folder must never block the panel

    def popup(self, cid, items):
        """Show a menu under control `cid`; items are (id, label, flags). Returns the chosen id or 0."""
        menu = U.CreatePopupMenu()
        try:
            for item_id, label, flags in items:
                U.AppendMenuW(menu, flags | (0x800 if label is None else 0), item_id, label)
            r = window_rect(self.controls[cid])
            U.SetForegroundWindow(self.hwnd)
            choice = U.TrackPopupMenu(menu, 0x182, r[0], r[3], 0, self.hwnd, None)  # RETURNCMD|RIGHTBUTTON|NONOTIFY
            U.PostMessageW(self.hwnd, 0, 0, 0)
            return choice
        finally:
            U.DestroyMenu(menu)

    def skin_menu(self):
        items = [(100+i, info['label'], 8 if name == CURRENT['skin'] else 0)
                 for i, (name, info) in enumerate(SKINS.items())]
        choice = self.popup(204, items)
        if choice:
            self.set_skin(list(SKINS)[choice-100])
            self.render()

    def update_menu(self):
        state, latest = self.update['state'], self.update['latest']
        status = {'current': f'Aggiornato · versione {VERSION}',
                  'available': f'Disponibile la versione {latest} (hai la {VERSION})',
                  'checking': 'Controllo in corso…'}.get(state, 'Stato aggiornamenti sconosciuto')
        items = [(1, status, 3), (2, None, 0), (3, 'Controlla ora', 0),
                 (4, f'Scarica e installa la versione {latest}' if state == 'available' else 'Nessun aggiornamento da installare',
                  0 if state == 'available' else 3),
                 (5, 'Controlla all’avvio', 8 if self.settings.get('check_updates', True) else 0)]
        choice = self.popup(205, items)
        if choice == 3:
            self.check_updates(manual=True)
        elif choice == 4:
            self.install_update()
        elif choice == 5:
            self.settings['check_updates'] = not self.settings.get('check_updates', True)
            self.write_settings()
            self.session.message = ('Controllo aggiornamenti all’avvio attivo.' if self.settings['check_updates']
                                    else 'Controllo aggiornamenti all’avvio disattivato: nessun accesso alla rete.')
        self.render()

    def check_updates(self, manual=False):
        """Anonymous read of the latest GitHub release, off the UI thread."""
        if self.update['state'] == 'checking':
            return
        previous = self.update['state']
        self.update['state'] = 'checking'
        if manual:
            self.session.message = 'Controllo aggiornamenti…'
        def work():
            try:
                state, release = updater.check(VERSION)
                self.post(('update_checked', state, release, manual))
            except updater.UpdateError as error:
                self.post(('update_failed', previous, str(error), manual))
            except Exception as error:  # never let a worker thread die silently
                self.post(('update_failed', previous, f'Controllo non riuscito: {error}', manual))
        threading.Thread(target=work, name='update-check', daemon=True).start()

    def install_update(self):
        release = self.update.get('release')
        if self.update['state'] != 'available' or not release:
            return
        self.dialog_open = True
        try:
            answer = U.MessageBoxW(self.hwnd, f'Scaricare la versione {release["version"]} da GitHub, verificarla e riavviare il programma?\n\n'
                'Le macro salvate non vengono toccate.', f'Mouse Macro {VERSION} · hcok', 0x24)
        finally:
            self.dialog_open = False
        if answer != 6:
            return
        self.session.message = f'Scarico la versione {release["version"]}…'
        current = Path(__file__).resolve().parent.parent
        def work():
            try:
                target = updater.install(release, FOLDER/'Portable', keep=[current])
                self.post(('update_installed', str(target)))
            except updater.UpdateError as error:
                self.post(('update_failed', 'available', str(error), True))
            except Exception as error:
                self.post(('update_failed', 'available', f'Aggiornamento non riuscito: {error}', True))
        threading.Thread(target=work, name='update-install', daemon=True).start()

    def worker_result(self, kind, *args):
        if kind == 'update_checked':
            state, release, manual = args
            self.update = {'state': state, 'latest': release['version'], 'release': release}
            if manual or state == 'available':
                self.session.message = (f'Disponibile la versione {release["version"]}: clicca il pallino in alto.'
                                        if state == 'available' else f'Sei aggiornato: versione {VERSION}.')
        elif kind == 'update_failed':
            previous, message, manual = args
            self.update['state'] = previous if previous != 'checking' else 'unknown'
            if manual:
                self.session.message = message
        elif kind == 'update_installed':
            target = Path(args[0])
            subprocess.Popen([str(target/'runtime'/'pythonw.exe'), '-B', str(target/'app'/'windows_main.py'), '--wait-for-exit'],
                             cwd=str(target), creationflags=0x00000008|0x00000200, close_fds=True)
            U.PostMessageW(self.hwnd, WM_CLOSE, 0, 0)

    def read_repeats(self):
        text = C.create_unicode_buffer(16)
        U.GetWindowTextW(self.controls[22],text,len(text))
        return parse_repeats(text.value)

    def sync_repeats(self):
        text = C.create_unicode_buffer(16)
        U.GetWindowTextW(self.controls[22],text,len(text))
        if text.value != str(self.repeats):
            U.SetWindowTextW(self.controls[22],str(self.repeats))

    def action(self, choice):
        if choice in (101,102):
            from macro.win_dialogs import ask_save_path, ask_open_path
            self.dialog_open = True
            try:
                path = ask_save_path('Salva macro', owner=self.hwnd) if choice == 101 else ask_open_path('Carica macro', owner=self.hwnd)
            finally:
                self.dialog_open = False
            if path:
                self.session.save(path) if choice == 101 else self.session.load(path)
        elif choice == 42:
            self.human = not self.human
            self.session.message = ('Movimento umano attivo: percorsi e pause cambiano a ogni giro, i clic restano sugli stessi punti.'
                                    if self.human else 'Movimento umano disattivato: replay identico alla registrazione.')
        elif choice == 41:
            self.slow = not self.slow
            self.session.message = 'Pagine lente attive: nessun rilevamento automatico del caricamento.' if self.slow else 'Pausa standard fra le azioni.'
        elif choice == 104:
            self.dialog_open = True
            try:
                U.MessageBoxW(self.hwnd, '1. Registra i gesti del mouse in qualsiasi programma con F9.\n'
                    '2. Ferma la registrazione con F9.\n'
                    '3. Ripristina lo stato iniziale, scegli i giri e premi F10.\n'
                    'Non registra i tasti della tastiera. Non chiude schede.\n\n'
                    'CAMBIA SCHEDA: tra un giro e l’altro invia Ctrl+Tab al programma attivo\n'
                    '(es. per passare alla scheda successiva del browser). Mai dopo l’ultimo giro.\n'
                    'Spento: la sequenza si ripete sempre nella stessa scheda.\n\n'
                    'PAGINE LENTE: aspetta di più tra un click e l’altro (almeno 1,2 s) e\n'
                    'non accorcia le tue pause oltre 0,35 s. Serve se il sito carica piano.\n'
                    'Non rileva il caricamento: aggiunge solo tempo.\n\n'
                    'MOVIMENTO UMANO (spento all’avvio): a ogni giro il cursore segue una curva\n'
                    'leggermente diversa, con velocità non uniforme, e le pause variano un poco.\n'
                    'I clic cadono sempre negli stessi punti della registrazione. Non rende\n'
                    'invisibile l’automazione: controlla i termini del sito che usi.\n\n'
                    'F10 ferma; Ctrl+Alt+F11 è lo stop di emergenza.\n'
                    'Sposta il pannello fuori dai gesti PRIMA di iniziare.\n'
                    'Mantieni posizione delle finestre e scala dello schermo.\n'
                    'Rapida 2× accelera movimenti e pause operative; conserva attese oltre 2 s.\n'
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
            if self.active_view:
                self.active_position = r[:2]
            position = self.normal_position if self.active_view else r[:2]
            if position:
                try:
                    self.settings['position'] = list(position)
                    self.write_settings()
                except OSError:
                    pass  # an unwritable settings folder must never block closing

    def wndproc(self, hwnd, msg, wp, lp):
        try:
            if msg == 0xF and hasattr(self,'width') and hasattr(self,'session'):
                self.paint(hwnd);return 0
            if msg == 0x14:return 1  # fully buffered painting
            if msg == 0x133 and hasattr(self,'session') and lp == self.controls.get(22):  # WM_CTLCOLOREDIT
                rgb=lambda color:int(color[5:7],16)<<16|int(color[3:5],16)<<8|int(color[1:3],16)
                G.SetTextColor(wp,rgb(COLORS['text']));G.SetBkColor(wp,rgb(COLORS['input']))
                if not self.edit_brush:self.edit_brush=G.CreateSolidBrush(rgb(COLORS['input']))
                return self.edit_brush
            if msg == 0x2B and hasattr(self,'boxes'):
                self.draw_control(C.cast(lp,C.POINTER(DrawItem)).contents);return 1
            if msg == 0x84 and hasattr(self,'hwnd') and self.hwnd:
                r=window_rect(hwnd);y=C.c_short((lp >> 16)&0xffff).value-r[1]
                if 0 <= y < round((self.height if self.active_view else 30)*self.dpi/96):return 2  # drag outside buttons
            if msg == 0x21:  # WM_MOUSEACTIVATE: don't steal Chrome's focus
                if hasattr(self,'session') and self.session.state in (State.READY,State.ERROR):
                    point=W.POINT();U.GetCursorPos(C.byref(point))
                    if U.WindowFromPoint(point) == self.controls.get(22):
                        return 1  # explicit click in the numeric input activates editing
                return 3  # MA_NOACTIVATE
            if msg == 0x113 and hasattr(self,'boxes'):
                point=W.POINT();U.GetCursorPos(C.byref(point))
                hovered=next((cid for cid in self.boxes if (lambda r:r[0]<=point.x<r[2] and r[1]<=point.y<r[3])(window_rect(self.controls[cid]))),None)
                if hovered != self.hover:
                    for cid in (self.hover,hovered):
                        if cid:U.InvalidateRect(self.controls[cid],None,False)
                    self.hover=hovered
            if msg in (WM_APP, 0x113) and self.hwnd and hasattr(self, 'session'):
                self.drain()
                return 0
            if msg == WM_COMMAND and hasattr(self, 'session'):
                cid = wp & 0xffff
                if cid == 22:
                    # EDIT sends synchronous notifications during creation,
                    # before its HWND has been assigned to controls[22].
                    if 22 not in self.controls or (wp >> 16) not in (0x300,0x200):
                        return 0
                    if self.session.state in (State.READY,State.ERROR):
                        try:
                            self.repeats = self.read_repeats()
                        except ValueError:
                            if (wp >> 16) == 0x200:  # EN_KILLFOCUS: restore last valid value
                                self.sync_repeats()
                    return 0
                if cid == 203: U.PostMessageW(hwnd,WM_CLOSE,0,0)
                elif cid == 201: U.ShowWindow(hwnd,6)
                elif cid in (24,202) and self.session.state in (State.READY,State.ERROR):
                    self.expanded=not self.expanded;self.layout(self.dpi)
                elif cid == 204 and self.session.state in (State.READY,State.ERROR):self.skin_menu()
                elif cid == 205 and self.session.state in (State.READY,State.ERROR):self.update_menu()
                elif cid == 104:self.action(104)
                elif cid == 110:self.hotkey(HOTKEY_EMERGENCY)
                elif cid == 12:
                    if self.session.state == State.RECORDING:
                        self.post('record')
                    elif self.session.state in (State.PLAYING,State.STOPPING):
                        self.session.request_stop()
                elif cid == 10:
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
                    if cid == 25: self.repeats = 20
                    if cid in (21,23,25): self.sync_repeats()
                    if cid in (41,42,101,102): self.action(cid)
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
                try:
                    self.session.close()
                finally:  # hotkeys and window must go away even if the player is slow to stop
                    self.hotkeys.stop()
                    U.DestroyWindow(hwnd)
                return 0
            if msg == WM_DESTROY:
                if self.repeat_font:
                    G.DeleteObject(self.repeat_font)
                if self.edit_brush:
                    G.DeleteObject(self.edit_brush)
                self.theme.close()
                U.PostQuitMessage(0)
                return 0
        except Exception as error:
            try:
                (FOLDER/'errore.log').write_text(traceback.format_exc(), 'utf-8')
            except OSError:
                pass
            if hasattr(self,'session'):
                self.session.request_stop()
                self.session.error(error)
        return U.DefWindowProcW(hwnd,msg,wp,lp)

    def run(self):
        msg = W.MSG()
        while U.GetMessageW(C.byref(msg), None, 0, 0) > 0:
            if not U.IsDialogMessageW(self.hwnd,C.byref(msg)):
                U.TranslateMessage(C.byref(msg))
                U.DispatchMessageW(C.byref(msg))


def main():
    wait = '--wait-for-exit' in sys.argv  # relaunch after an update: let the old instance close first
    deadline = time.monotonic() + 20
    while True:
        mutex = K.CreateMutexW(None, False, 'Local\\MouseMacroSuperpower017')
        if K.GetLastError() != 183:
            break
        # Second launch leaves the original session and its global hotkeys alone.
        K.CloseHandle(mutex)
        if not wait or time.monotonic() > deadline:
            return
        time.sleep(0.3)
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
