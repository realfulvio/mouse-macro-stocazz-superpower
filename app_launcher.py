"""Avvio dell'interfaccia.

Su Windows l'interfaccia Flet viene servita solo in locale (127.0.0.1, percorso
casuale) e mostrata in una finestra di Microsoft Edge in modalità app, invece
che nel client desktop di Flet (flet.exe). flet.exe non è firmato e Smart App
Control di Windows 11 ne blocca l'avvio; Edge è firmato da Microsoft ed è
presente su ogni Windows 10/11. Su Linux resta la finestra desktop di Flet.
"""
from __future__ import annotations

import os
import secrets
import subprocess
import sys
import threading
import time
import webbrowser

import flet as ft

# Dimensione esterna della finestra: contenuto ~560x720 più la barra del titolo.
WINDOW_SIZE = (576, 770)
# Senza finestra aperta per così tanti secondi, il programma si chiude.
IDLE_EXIT_SECONDS = 8
# Se nessuna finestra si collega entro questo tempo, apre il browser predefinito.
FIRST_CONNECT_TIMEOUT = 45


def uses_browser_window() -> bool:
    return sys.platform == "win32"


def _fix_std_streams() -> None:
    # Con PyInstaller --windowed stdout/stderr sono None e la configurazione di
    # logging di uvicorn (server web di Flet) fallirebbe.
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w")


def find_app_browser() -> str | None:
    """Percorso di Edge (o in mancanza di Chrome), entrambi supportano --app."""
    import winreg

    for exe in ("msedge.exe", "chrome.exe"):
        for root in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
            try:
                with winreg.OpenKey(root, rf"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\{exe}") as key:
                    path = winreg.QueryValue(key, None).strip('"')
            except OSError:
                continue
            if path and os.path.isfile(path):
                return path
    for base in (os.environ.get("ProgramFiles(x86)"), os.environ.get("ProgramFiles")):
        if base:
            path = os.path.join(base, "Microsoft", "Edge", "Application", "msedge.exe")
            if os.path.isfile(path):
                return path
    return None


class _Lifetime:
    """Tiene il conto delle finestre collegate e chiude il programma quando
    l'ultima viene chiusa."""

    def __init__(self):
        self._lock = threading.Lock()
        self._sessions = 0
        self._seen = False
        self._changed = time.monotonic()

    def opened(self) -> None:
        with self._lock:
            self._sessions += 1
            self._seen = True
            self._changed = time.monotonic()

    def closed(self) -> None:
        with self._lock:
            self._sessions = max(0, self._sessions - 1)
            self._changed = time.monotonic()

    def seen(self) -> bool:
        with self._lock:
            return self._seen

    def idle_for(self) -> float:
        with self._lock:
            if not self._seen or self._sessions:
                return 0.0
            return time.monotonic() - self._changed


def _open_window(url: str, lifetime: _Lifetime) -> None:
    browser = find_app_browser()
    proc = None
    if browser:
        profile = os.path.join(os.environ.get("LOCALAPPDATA") or os.path.expanduser("~"),
                               "MouseMacroStocazzSuperpower", "window")
        args = [browser, f"--app={url}", f"--window-size={WINDOW_SIZE[0]},{WINDOW_SIZE[1]}",
                f"--user-data-dir={profile}", "--no-first-run", "--no-default-browser-check",
                "--disable-sync", "--disable-extensions"]
        try:
            proc = subprocess.Popen(args, close_fds=True)
        except OSError:
            proc = None
    if proc is None:
        webbrowser.open(url)

    started = time.monotonic()
    fallback_done = proc is None
    while True:
        time.sleep(1)
        if proc is not None and proc.poll() is not None:
            # La finestra ha un profilo dedicato: se il processo di Edge termina
            # dopo essere rimasto aperto, l'utente l'ha chiusa.
            if time.monotonic() - started > 5 and lifetime.seen():
                os._exit(0)
            proc = None
        if not fallback_done and not lifetime.seen() and time.monotonic() - started > FIRST_CONNECT_TIMEOUT:
            webbrowser.open(url)
            fallback_done = True
        if lifetime.idle_for() > IDLE_EXIT_SECONDS:
            os._exit(0)


def _track(target, lifetime: _Lifetime):
    def session(page: ft.Page):
        lifetime.opened()
        try:
            target(page)
        finally:
            app_handler = page.on_disconnect

            def on_disconnect(e):
                try:
                    if app_handler is not None:
                        app_handler(e)
                finally:
                    lifetime.closed()

            page.on_disconnect = on_disconnect

    return session


def run(target) -> None:
    """Avvia l'app: finestra Edge su Windows, finestra desktop Flet altrove."""
    _fix_std_streams()
    if not uses_browser_window():
        ft.run(target)
        return

    import importlib

    # import_module restituisce il modulo flet.app anche se il pacchetto espone
    # una funzione con lo stesso nome.
    flet_app = importlib.import_module("flet.app")
    lifetime = _Lifetime()

    def open_in_app_window(url: str) -> None:
        threading.Thread(target=_open_window, args=(url, lifetime), daemon=True).start()

    # Flet chiama open_in_browser(url) appena il server locale è pronto.
    flet_app.open_in_browser = open_in_app_window
    ft.run(
        _track(target, lifetime),
        view=ft.AppView.WEB_BROWSER,
        host="127.0.0.1",
        name=secrets.token_urlsafe(16),
        no_cdn=True,
    )
