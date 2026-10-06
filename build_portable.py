"""Build the portable Windows package.

Why: Smart App Control (Windows 11) checks every executable it does not know.
A PyInstaller exe is a brand-new unsigned file at every build, so Microsoft's
cloud may block it; .cmd/.bat launchers downloaded from the web are blocked
outright. The portable package contains no new executable code:

- the two files to double-click are copies of the official pythonw.exe,
  renamed: the Python Software Foundation signature does not depend on the
  file name, so they stay signed. Started without arguments, Python imports
  app/sitecustomize.py, which starts the program (portable_sitecustomize.py);
- python/: the rest of the official Python "embeddable" package from
  python.org (all .exe/.dll/.pyd signed by the PSF) and, in python/lib, the
  dependencies installed from PyPI wheels, byte-identical to what everybody
  else downloads (unused optional native modules removed);
- app/: the program's .py sources and assets.

Short internal paths: Explorer cannot extract zip entries longer than 260
characters. Run with the same Python version you want to ship.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import shutil
import subprocess
import sys
import urllib.request
import zipfile

PACKAGE = "MouseMacroStocazzSuperpower"
LAUNCHERS = {"Mouse Macro Stocazz Superpower.exe": "it",
             "Mouse Macro Stocazz Superpower (English).exe": "en"}
# Accanto ai file da cliccare servono solo le DLL che il loader di Windows cerca
# nella cartella dell'eseguibile; tutto il resto di Python sta in python/.
TOP_LEVEL = ("python3.dll", "vcruntime140.dll", "vcruntime140_1.dll")
# Moduli nativi opzionali (uvicorn[standard]) che il programma non usa: meno
# file binari da far valutare a Smart App Control.
UNUSED = ("httptools", "watchfiles", "yaml", "_yaml", "PyYAML", "bin")
SOURCES = ("main.py", "main_en.py", "app_launcher.py", "localization.py", "macro", "assets", "LICENSE")

README = """Mouse Macro Stocazz Superpower - versione portatile / portable version
=======================================================================

ITALIANO
Fai doppio clic su "Mouse Macro Stocazz Superpower.exe".
Non serve installare niente: tieni insieme tutti i file di questa cartella.
L'icona e' quella di Python perche' il runtime e' il Python ufficiale, firmato.
La firma del runtime non garantisce l'accettazione dell'app da parte di
Smart App Control, antivirus o protezioni aziendali. Se compare una
segnalazione, interrompi l'uso e conserva i dettagli per l'analisi.

ENGLISH
Double-click "Mouse Macro Stocazz Superpower (English).exe".
Nothing to install: keep all the files in this folder together.
It shows the Python icon because the runtime is the official, signed Python.
The runtime signature does not guarantee that Smart App Control, antivirus
or corporate security policies will accept the app. If an alert appears,
stop using the app and preserve the detection details for investigation.

powered by hcok - PolyForm Noncommercial licence (app/LICENSE)
"""


def download_embeddable(root: Path) -> Path:
    version = "{}.{}.{}".format(*sys.version_info[:3])
    name = f"python-{version}-embed-amd64.zip"
    cache = root / "vendor" / name
    if not cache.is_file():
        cache.parent.mkdir(exist_ok=True)
        url = f"https://www.python.org/ftp/python/{version}/{name}"
        print(f"Downloading official Python: {url}", flush=True)
        temporary = cache.with_suffix(".tmp")
        try:
            urllib.request.urlretrieve(url, temporary)
            temporary.replace(cache)
        finally:
            temporary.unlink(missing_ok=True)
    return cache


def main():
    if sys.platform != "win32":
        raise SystemExit("Build the portable package on Windows.")
    root = Path(__file__).resolve().parent
    stage = root / "build" / "portable" / PACKAGE
    shutil.rmtree(stage.parent, ignore_errors=True)
    python = stage / "python"
    app = stage / "app"
    python.mkdir(parents=True)

    with zipfile.ZipFile(download_embeddable(root)) as archive:
        archive.extractall(python)
    dll = next(python.glob("python3?*.dll"))            # es. python313.dll
    stdlib = next(python.glob("python3?*.zip")).name    # es. python313.zip
    for name in (dll.name,) + TOP_LEVEL:
        shutil.move(python / name, stage / name)
    pythonw = python / "pythonw.exe"
    for launcher in LAUNCHERS:
        shutil.copy2(pythonw, stage / launcher)
    for name in ("python.exe", "pythonw.exe") + tuple(p.name for p in python.glob("*._pth")):
        (python / name).unlink()
    # Il ._pth accanto alla DLL decide sys.path: libreria standard, librerie,
    # programma e "import site" (che importa app/sitecustomize.py).
    (stage / dll.with_suffix("._pth").name).write_text(
        f"python\\{stdlib}\npython\npython\\lib\napp\nimport site\n", encoding="utf-8")

    site_packages = python / "lib"
    subprocess.run([sys.executable, "-m", "pip", "install", "--quiet", "--disable-pip-version-check",
                    "--no-compile", "--only-binary=:all:", "--target", str(site_packages),
                    "-r", str(root / "requirements.txt")], check=True)
    for entry in list(site_packages.iterdir()):
        if entry.name.split("-")[0] in UNUSED:
            shutil.rmtree(entry) if entry.is_dir() else entry.unlink()
    web = site_packages / "flet_web" / "web"
    shutil.rmtree(web / "pyodide", ignore_errors=True)  # contiene un python.exe non firmato
    for pattern in ("*.symbols", "*.map"):
        for file in web.rglob(pattern):
            file.unlink()

    app.mkdir()
    for name in SOURCES:
        source = root / name
        if source.is_dir():
            shutil.copytree(source, app / name, ignore=shutil.ignore_patterns("__pycache__"))
        else:
            shutil.copy2(source, app / name)
    shutil.copy2(root / "portable_start.py", app / "start.py")
    shutil.copy2(root / "portable_sitecustomize.py", app / "sitecustomize.py")
    (stage / "LEGGIMI - README.txt").write_text(README.replace("\n", "\r\n"), encoding="utf-8")

    output = root / "dist" / "windows"
    output.mkdir(parents=True, exist_ok=True)
    target = output / f"{PACKAGE}-Windows-Portable.zip"
    target.unlink(missing_ok=True)
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for file in sorted(stage.rglob("*")):
            if file.is_file():
                archive.write(file, file.relative_to(stage.parent))
    with target.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    print(f"{digest}  {target.name}")
    print(f"Portable package written to {target.relative_to(root)} ({target.stat().st_size / 2**20:.1f} MB)", flush=True)


if __name__ == "__main__":
    main()
