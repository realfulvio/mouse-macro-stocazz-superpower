"""Build native IT/EN desktop binaries, including the matching Flet client."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import subprocess
import sys
import urllib.request


def main():
    if sys.platform not in ('win32', 'linux'):
        raise SystemExit('Build on Windows or Linux using its native Python environment.')
    root = Path(__file__).resolve().parent
    os.chdir(root)
    import flet_desktop
    from flet_desktop.version import version

    system = 'Windows' if sys.platform == 'win32' else 'Linux'
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
    output = root / 'dist' / system.lower()
    for language, entrypoint in [('IT', 'main.py'), ('EN', 'main_en.py')]:
        name = f'MouseMacroStocazzSuperpower-{system}-{language}'
        args = [sys.executable, '-m', 'PyInstaller', '--noconfirm', '--onefile', '--windowed',
                '--noupx', '--name', name, '--distpath', str(output),
                '--workpath', str(root / 'build' / system.lower() / language),
                '--specpath', str(root / 'build'), '--paths', str(root),
                '--add-data', f'{root / "assets"}{os.pathsep}assets',
                '--add-data', f'{archive}{os.pathsep}flet_desktop/app',
                '--collect-data', 'flet', '--hidden-import', 'flet_desktop']
        if system == 'Windows':
            args += ['--icon', str(root / 'assets' / 'icon.ico'), '--version-file', str(root / 'version_info.txt'),
                     '--hidden-import', 'flet_desktop.win_taskbar', '--hidden-import', 'flet_desktop.version']
        else:
            args += ['--strip', '--hidden-import', 'evdev', '--hidden-import', 'flet_desktop.version']
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
