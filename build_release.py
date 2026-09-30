"""Build native IT/EN binaries for the current OS.

Windows: the Flet interface is served locally and shown in an Edge app window
(see app_launcher.py), so the unsigned Flet desktop client is NOT bundled; the
Flet web client files are embedded instead, without the unused Pyodide runtime.
Linux: the matching official Flet desktop client is embedded.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import urllib.request


def linux_flet_client(root: Path) -> Path:
    import flet_desktop
    from flet_desktop.version import version

    artifact = flet_desktop.get_artifact_filename()
    vendor = root / 'vendor'
    vendor.mkdir(exist_ok=True)
    archive = vendor / artifact
    if not archive.is_file():
        url = f'https://github.com/flet-dev/flet/releases/download/v{version}/{artifact}'
        temporary = archive.with_suffix(archive.suffix + '.tmp')
        try:
            print(f'Downloading official Flet client: {url}', flush=True)
            urllib.request.urlretrieve(url, temporary)
            temporary.replace(archive)
        finally:
            temporary.unlink(missing_ok=True)
    return archive


def windows_web_client(root: Path) -> Path:
    import flet_web

    source = Path(flet_web.__file__).resolve().parent / 'web'
    stage = root / 'build' / 'flet_web_client'
    shutil.rmtree(stage, ignore_errors=True)
    shutil.copytree(source, stage, ignore=shutil.ignore_patterns('pyodide', '*.symbols', '*.map'))
    return stage


def main():
    if sys.platform not in ('win32', 'linux'):
        raise SystemExit('Build on Windows or Linux using its native Python environment.')
    root = Path(__file__).resolve().parent
    os.chdir(root)

    system = 'Windows' if sys.platform == 'win32' else 'Linux'
    output = root / 'dist' / system.lower()
    if system == 'Windows':
        client = windows_web_client(root)
        client_args = ['--add-data', f'{client}{os.pathsep}flet_web/web',
                       '--collect-submodules', 'flet_web', '--collect-submodules', 'uvicorn',
                       '--hidden-import', 'macro.win_dialogs']
    else:
        client = linux_flet_client(root)
        client_args = ['--add-data', f'{client}{os.pathsep}flet_desktop/app',
                       '--hidden-import', 'flet_desktop', '--hidden-import', 'flet_desktop.version']

    for language, entrypoint in [('IT', 'main.py'), ('EN', 'main_en.py')]:
        name = f'MouseMacroStocazzSuperpower-{system}-{language}'
        args = [sys.executable, '-m', 'PyInstaller', '--noconfirm', '--onefile', '--windowed',
                '--noupx', '--name', name, '--distpath', str(output),
                '--workpath', str(root / 'build' / system.lower() / language),
                '--specpath', str(root / 'build'), '--paths', str(root),
                '--add-data', f'{root / "assets"}{os.pathsep}assets',
                '--collect-data', 'flet'] + client_args
        if system == 'Windows':
            args += ['--icon', str(root / 'assets' / 'icon.ico'), '--version-file', str(root / 'version_info.txt')]
        else:
            args += ['--strip', '--hidden-import', 'evdev']
        args.append(str(root / entrypoint))
        subprocess.run(args, check=True)

    checksums = []
    for binary in sorted(output.glob('MouseMacroStocazzSuperpower-*')):
        if binary.is_file():
            with binary.open('rb') as stream:
                checksums.append(f'{hashlib.file_digest(stream, "sha256").hexdigest()}  {binary.name}')
    (output / 'SHA256SUMS.txt').write_text('\n'.join(checksums) + '\n', encoding='utf-8')
    print(f'IT/EN binaries and SHA256SUMS.txt written to dist/{system.lower()}', flush=True)


if __name__ == '__main__':
    main()
