"""UIPI preflight only: never called from the timed playback loop.

Inspects windows currently under recorded clicks/scrolls, plus the foreground
window for keyboard input. Windows opened or moved later cannot be predicted.
An inaccessible token is unknown, not evidence of higher integrity.
"""
from __future__ import annotations

import ctypes as C
from ctypes import wintypes as W
import os

from .events import BUTTON_OF_DOWN, KEY_DOWN, WHEEL


class _SidAndAttributes(C.Structure):
    _fields_ = [('sid', C.c_void_p), ('attributes', W.DWORD)]


class _WindowsAPI:
    def __init__(self):
        self.u = C.WinDLL('user32', use_last_error=True)
        self.k = C.WinDLL('kernel32', use_last_error=True)
        self.a = C.WinDLL('advapi32', use_last_error=True)
        signatures = (
            (self.u.WindowFromPoint, W.HWND, [W.POINT]),
            (self.u.GetForegroundWindow, W.HWND, []),
            (self.u.GetWindowThreadProcessId, W.DWORD, [W.HWND, C.POINTER(W.DWORD)]),
            (self.k.OpenProcess, W.HANDLE, [W.DWORD, W.BOOL, W.DWORD]),
            (self.k.CloseHandle, W.BOOL, [W.HANDLE]),
            (self.a.OpenProcessToken, W.BOOL, [W.HANDLE, W.DWORD, C.POINTER(W.HANDLE)]),
            (self.a.GetTokenInformation, W.BOOL, [W.HANDLE, C.c_int, C.c_void_p, W.DWORD, C.POINTER(W.DWORD)]),
            (self.a.IsValidSid, W.BOOL, [C.c_void_p]),
            (self.a.GetSidSubAuthorityCount, C.POINTER(W.BYTE), [C.c_void_p]),
            (self.a.GetSidSubAuthority, C.POINTER(W.DWORD), [C.c_void_p, W.DWORD]),
        )
        for fn, result, arguments in signatures:
            fn.restype, fn.argtypes = result, arguments

    def pid(self, hwnd):
        pid = W.DWORD()
        if hwnd:
            self.u.GetWindowThreadProcessId(hwnd, C.byref(pid))
        return pid.value

    def at(self, x, y):
        return self.pid(self.u.WindowFromPoint(W.POINT(x, y)))

    def foreground(self):
        return self.pid(self.u.GetForegroundWindow())

    def integrity(self, pid):
        process = self.k.OpenProcess(0x1000, False, pid)  # QUERY_LIMITED_INFORMATION
        if not process:
            return None
        token = W.HANDLE()
        try:
            if not self.a.OpenProcessToken(process, 0x0008, C.byref(token)):  # TOKEN_QUERY
                return None
            size = W.DWORD()
            self.a.GetTokenInformation(token, 25, None, 0, C.byref(size))  # TokenIntegrityLevel
            if not size.value:
                return None
            buf = C.create_string_buffer(size.value)
            if not self.a.GetTokenInformation(token, 25, buf, size, C.byref(size)):
                return None
            sid = C.cast(buf, C.POINTER(_SidAndAttributes)).contents.sid
            if not sid or not self.a.IsValidSid(sid):
                return None
            count = self.a.GetSidSubAuthorityCount(sid)
            if not count or not count[0]:
                return None
            rid = self.a.GetSidSubAuthority(sid, count[0] - 1)
            return rid[0] if rid else None
        finally:
            if token.value:
                self.k.CloseHandle(token)
            self.k.CloseHandle(process)


def ensure_input_integrity(events):
    """Reject known higher-integrity targets before any playback input is sent."""
    api = _WindowsAPI()
    own_pid = os.getpid()
    own_level = api.integrity(own_pid)
    if own_level is None:
        return
    checked_pids = {0, own_pid}
    checked_points = set()
    keyboard_checked = False
    for event in events:
        if event.kind in BUTTON_OF_DOWN or event.kind == WHEEL:
            point = (event.x, event.y)
            if point in checked_points:
                continue
            checked_points.add(point)
            pid = api.at(*point)
        elif event.kind == KEY_DOWN and not keyboard_checked:
            keyboard_checked = True
            pid = api.foreground()
        else:
            continue
        if pid in checked_pids:
            continue
        checked_pids.add(pid)
        level = api.integrity(pid)
        if level is not None and level > own_level:
            raise ValueError(
                'Bersaglio elevato.\nRiapri con «Esegui come amministratore».')
