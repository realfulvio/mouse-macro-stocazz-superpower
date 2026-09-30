"""Avvio automatico della versione portatile (copiato come app/sitecustomize.py).

I file da cliccare sono copie rinominate di pythonw.exe: restano firmati dalla
Python Software Foundation, quindi Smart App Control li accetta, mentre blocca
i file .cmd scaricati da Internet. Lanciati senza argomenti, Python importa
questo modulo durante l'avvio: qui si fa partire il programma e poi si esce.
Con argomenti (es. "app\\main.py --self-test report.json") non fa nulla.
"""
import os
import sys

_exe = os.path.basename(sys.executable).lower()
if _exe.startswith("mouse macro") and len(sys.argv) <= 1 and not (sys.argv and sys.argv[0]):
    import start

    os._exit(start.main("en" if "english" in _exe else "it"))
