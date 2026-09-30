"""Finestre native Apri/Salva di Windows (comdlg32).

Servono quando l'interfaccia gira nella finestra di Edge: lì il FilePicker di
Flet si comporta come in un sito web e non restituisce il percorso del file.
Le funzioni sono bloccanti: vanno chiamate da un thread (asyncio.to_thread).
"""
from __future__ import annotations

import ctypes
from ctypes import wintypes

_OFN_OVERWRITEPROMPT = 0x00000002
_OFN_NOCHANGEDIR = 0x00000008
_OFN_PATHMUSTEXIST = 0x00000800
_OFN_FILEMUSTEXIST = 0x00001000
_OFN_EXPLORER = 0x00080000
_COINIT_APARTMENTTHREADED = 0x2
_MAX_PATH_BUFFER = 32768


class _OPENFILENAMEW(ctypes.Structure):
    _fields_ = [
        ("lStructSize", wintypes.DWORD),
        ("hwndOwner", wintypes.HWND),
        ("hInstance", wintypes.HINSTANCE),
        ("lpstrFilter", ctypes.c_void_p),
        ("lpstrCustomFilter", wintypes.LPWSTR),
        ("nMaxCustFilter", wintypes.DWORD),
        ("nFilterIndex", wintypes.DWORD),
        ("lpstrFile", ctypes.c_void_p),
        ("nMaxFile", wintypes.DWORD),
        ("lpstrFileTitle", wintypes.LPWSTR),
        ("nMaxFileTitle", wintypes.DWORD),
        ("lpstrInitialDir", wintypes.LPCWSTR),
        ("lpstrTitle", wintypes.LPCWSTR),
        ("Flags", wintypes.DWORD),
        ("nFileOffset", wintypes.WORD),
        ("nFileExtension", wintypes.WORD),
        ("lpstrDefExt", wintypes.LPCWSTR),
        ("lCustData", wintypes.LPARAM),
        ("lpfnHook", ctypes.c_void_p),
        ("lpTemplateName", wintypes.LPCWSTR),
        ("pvReserved", ctypes.c_void_p),
        ("dwReserved", wintypes.DWORD),
        ("FlagsEx", wintypes.DWORD),
    ]


def _file_filter(pairs: list[tuple[str, str]]) -> str:
    # "Descrizione\0*.ext\0...\0" : il terminatore finale lo aggiunge il buffer.
    return "".join(f"{label}\0{pattern}\0" for label, pattern in pairs)


def _run_dialog(save: bool, title: str, file_name: str, pairs: list[tuple[str, str]],
                default_ext: str) -> str | None:
    ctypes.windll.ole32.CoInitializeEx(None, _COINIT_APARTMENTTHREADED)
    file_buf = ctypes.create_unicode_buffer(file_name, _MAX_PATH_BUFFER)
    filter_buf = ctypes.create_unicode_buffer(_file_filter(pairs))

    ofn = _OPENFILENAMEW()
    ofn.lStructSize = ctypes.sizeof(_OPENFILENAMEW)
    # La finestra in primo piano è quella dell'app (l'utente ha appena cliccato
    # il pulsante): il dialogo le resta sopra.
    ofn.hwndOwner = ctypes.windll.user32.GetForegroundWindow()
    ofn.lpstrFilter = ctypes.addressof(filter_buf)
    ofn.nFilterIndex = 1
    ofn.lpstrFile = ctypes.addressof(file_buf)
    ofn.nMaxFile = _MAX_PATH_BUFFER
    ofn.lpstrTitle = title
    ofn.lpstrDefExt = default_ext
    ofn.Flags = _OFN_EXPLORER | _OFN_NOCHANGEDIR | _OFN_PATHMUSTEXIST | (
        _OFN_OVERWRITEPROMPT if save else _OFN_FILEMUSTEXIST)

    comdlg32 = ctypes.windll.comdlg32
    fn = comdlg32.GetSaveFileNameW if save else comdlg32.GetOpenFileNameW
    fn.argtypes = [ctypes.POINTER(_OPENFILENAMEW)]
    fn.restype = wintypes.BOOL
    if fn(ctypes.byref(ofn)):
        return file_buf.value
    error = comdlg32.CommDlgExtendedError()
    if error:
        raise OSError(f"Windows file dialog error {error:#x}")
    return None  # annullato dall'utente


def ask_save_path(title: str, file_name: str = "macro.mmr") -> str | None:
    return _run_dialog(True, title, file_name, [("Mouse macro (*.mmr)", "*.mmr")], "mmr")


def ask_open_path(title: str) -> str | None:
    return _run_dialog(False, title, "", [("Mouse macro (*.mmr; *.json)", "*.mmr;*.json"),
                                          ("*.*", "*.*")], "mmr")
