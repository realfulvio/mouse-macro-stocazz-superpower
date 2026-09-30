"""Avvio della versione portatile per Windows.

La versione portatile usa il Python ufficiale (eseguibili firmati dalla Python
Software Foundation) e le librerie di PyPI così come sono: Smart App Control
non deve valutare nessun eseguibile nuovo, e il codice del programma sono file
.py. Questo file viene copiato come app/start.py e avviato da app/sitecustomize.py
(vedi portable_sitecustomize.py) o con "app\\start.py it|en".
"""
import os
import sys
import traceback

APP_NAME = "Mouse Macro Stocazz Superpower"


def _report_startup_error(here: str) -> None:
    text = traceback.format_exc()
    folder = os.path.join(os.environ.get("LOCALAPPDATA") or here, "MouseMacroStocazzSuperpower")
    log = os.path.join(folder, "errore-avvio.log")
    try:
        os.makedirs(folder, exist_ok=True)
        with open(log, "w", encoding="utf-8") as stream:
            stream.write(text)
    except OSError:
        log = "-"
    import ctypes

    # pythonw non ha una console: senza questo messaggio un errore passerebbe inosservato.
    ctypes.windll.user32.MessageBoxW(
        None,
        f"Il programma non è partito / The app could not start.\n\n{text[-1500:]}\n\n{log}",
        APP_NAME,
        0x10,
    )


def main(language: str | None = None) -> int:
    if language is None:
        language = sys.argv[1] if len(sys.argv) > 1 else "it"
    here = os.path.dirname(os.path.abspath(__file__))
    os.chdir(here)
    if here not in sys.path:
        sys.path.insert(0, here)
    try:
        import main as app
        from app_launcher import run

        if language == "en":
            run(lambda page: app.main(page, language="en"))
        else:
            run(app.main)
    except Exception:
        _report_startup_error(here)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
