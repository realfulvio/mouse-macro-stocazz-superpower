"""Linux release package: run after `build_release.py` on Linux.

Writes to dist/linux:
- MouseMacroStocazzSuperpower-Linux-v<version>.tar.gz, a single folder with the
  IT/EN binaries, the permission script, license files and build_info.json;
- install.sh (copied from the repository);
- MouseMacroStocazzSuperpower-Linux-v<version>-x86_64.AppImage, the portable
  double-click version, when APPIMAGETOOL points to appimagetool;
- MouseMacroStocazzSuperpower-Linux-v<version>.flatpak, a single-file Flatpak
  bundle, when FLATPAK_BUNDLE=1 (needs flatpak and org.gnome.Platform 51);
- SHA256SUMS-linux-v<version>.txt covering all of the above.
The archive is reproducible: fixed owner, permissions and timestamps.
"""
from __future__ import annotations

import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from macro.panel_model import LINUX_VERSION  # noqa: E402
from macro.linux_updater import APPIMAGE, BINARIES, FLATPAK, PACKAGE, SUMS  # noqa: E402

FILES = {  # name in the package: (source, executable)
    'setup-linux-input.sh': ('scripts/setup-linux-input.sh', True),
    'LICENSE': ('LICENSE', False),
    'THIRD-PARTY-NOTICES.md': ('THIRD-PARTY-NOTICES.md', False),
    'GUIDA-ITALIANA.md': ('GUIDA-ITALIANA.md', False),
    'icon.png': ('assets/icon.png', False),
}
EPOCH = 1760000000  # fixed mtime for reproducible archives
APP_ID = 'mouse-macro-stocazz-superpower'
FLATPAK_ID = 'io.github.realfulvio.MouseMacroStocazzSuperpower'
FLATPAK_RUNTIME = ('org.gnome.Platform', '51')  # GTK3 and libsecret for the Flet client
APPRUN = """#!/bin/sh
# Portable launcher: Italian interface for Italian locales, English otherwise.
HERE="$(dirname "$(readlink -f "$0")")"
case "${MMSS_LANG:-${LC_ALL:-${LC_MESSAGES:-${LANG:-}}}}" in
    it*|IT*) LANGUAGE=IT ;;
    *) LANGUAGE=EN ;;
esac
exec "$HERE/usr/bin/MouseMacroStocazzSuperpower-Linux-$LANGUAGE" "$@"
"""
DESKTOP = """[Desktop Entry]
Type=Application
Name=Mouse Macro Stocazz Superpower
Comment=Registra e riproduce i gesti del mouse
Exec=AppRun
Icon=mouse-macro-stocazz-superpower
Terminal=false
Categories=Utility;
StartupWMClass=com.appveyor.flet
"""


def sha256(path):
    with open(path, 'rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def build(dist=None, version=LINUX_VERSION):
    dist = Path(dist) if dist else ROOT / 'dist' / 'linux'
    package = PACKAGE.format(version)
    content = {name: (dist / name, True) for name in BINARIES}
    content.update({name: (ROOT / source, executable) for name, (source, executable) in FILES.items()})
    missing = [str(path) for path, _ in content.values() if not path.is_file()]
    if missing:
        raise SystemExit('Missing files (run build_release.py first): ' + ', '.join(missing))
    manifest = {'version': version, 'platform': 'linux',
                'sha256': {name: sha256(path) for name, (path, _) in sorted(content.items())}}
    archive = dist / f'{package}.tar.gz'

    def info(name, size, mode):
        item = tarfile.TarInfo(f'{package}/{name}' if name else package)
        item.size, item.mode, item.mtime = size, mode, EPOCH
        item.uid = item.gid = 0
        item.uname = item.gname = 'root'
        return item

    with open(archive, 'wb') as raw, gzip.GzipFile(fileobj=raw, mode='wb', mtime=EPOCH, filename='') as zipped, \
            tarfile.open(fileobj=zipped, mode='w', format=tarfile.PAX_FORMAT) as tar:
        folder = info('', 0, 0o755)
        folder.type = tarfile.DIRTYPE
        tar.addfile(folder)
        for name, (path, executable) in sorted(content.items()):
            with open(path, 'rb') as stream:
                tar.addfile(info(name, path.stat().st_size, 0o755 if executable else 0o644), stream)
        data = (json.dumps(manifest, indent=2) + '\n').encode()
        tar.addfile(info('build_info.json', len(data), 0o644), io.BytesIO(data))
    installer = dist / 'install.sh'
    shutil.copyfile(ROOT / 'install.sh', installer)
    installer.chmod(0o755)
    outputs = [archive, installer]
    tool = os.environ.get('APPIMAGETOOL')
    if tool:
        outputs.append(build_appimage(dist, version, tool))
    if os.environ.get('FLATPAK_BUNDLE') == '1':
        outputs.append(build_flatpak(dist, version))
    sums = dist / SUMS.format(version)
    sums.write_text(''.join(f'{sha256(p)}  {p.name}\n' for p in outputs), encoding='utf-8')
    print(', '.join(p.name for p in outputs) + f' and {sums.name} written to {dist}', flush=True)
    return archive, installer, sums


def make_appdir(dist, target):
    """AppDir for the portable AppImage: both binaries, launcher, desktop entry, icon."""
    target = Path(target)
    shutil.rmtree(target, ignore_errors=True)
    (target / 'usr' / 'bin').mkdir(parents=True)
    for name in BINARIES:
        shutil.copyfile(Path(dist) / name, target / 'usr' / 'bin' / name)
        (target / 'usr' / 'bin' / name).chmod(0o755)
    (target / 'AppRun').write_text(APPRUN, encoding='utf-8')
    (target / 'AppRun').chmod(0o755)
    (target / f'{APP_ID}.desktop').write_text(DESKTOP, encoding='utf-8')
    shutil.copyfile(ROOT / 'assets' / 'icon.png', target / f'{APP_ID}.png')
    shutil.copyfile(ROOT / 'assets' / 'icon.png', target / '.DirIcon')
    return target


def build_appimage(dist, version, tool):
    dist = Path(dist)
    appdir = make_appdir(dist, ROOT / 'build' / 'AppDir')
    output = dist / APPIMAGE.format(version)
    output.unlink(missing_ok=True)
    subprocess.run([tool, '--no-appstream', str(appdir), str(output)], check=True,
                   env=dict(os.environ, ARCH='x86_64'))
    output.chmod(0o755)
    return output


def flatpak_finish_args():
    """Permissions, kept identical to flatpak/<id>.yml (checked by the tests)."""
    import re
    manifest = (ROOT / 'flatpak' / f'{FLATPAK_ID}.yml').read_text(encoding='utf-8')
    return re.findall(r'^  - (--[a-z-]+=[A-Za-z0-9._-]+)', manifest, re.M)


def build_flatpak(dist, version):
    """Single-file bundle from the release binaries, without flatpak-builder or the SDK:
    nothing is compiled, files are only placed and the sandbox is described."""
    dist = Path(dist)
    work = ROOT / 'build' / 'flatpak'
    shutil.rmtree(work, ignore_errors=True)
    build_dir, repo = work / 'build', work / 'repo'
    runtime, branch = FLATPAK_RUNTIME
    def run(*args):
        subprocess.run(['flatpak', *args], check=True)
    run('build-init', str(build_dir), FLATPAK_ID, runtime, runtime, branch)
    files = build_dir / 'files'
    def place(source, target, mode):
        target = files / target
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        target.chmod(mode)
    for name in BINARIES:
        place(dist / name, f'lib/mmss/{name}', 0o755)
    place(ROOT / 'flatpak' / 'launcher.sh', 'bin/mouse-macro-stocazz-superpower', 0o755)
    place(ROOT / 'assets' / 'icon.png', f'share/icons/hicolor/256x256/apps/{FLATPAK_ID}.png', 0o644)
    place(ROOT / 'flatpak' / f'{FLATPAK_ID}.desktop', f'share/applications/{FLATPAK_ID}.desktop', 0o644)
    place(ROOT / 'flatpak' / f'{FLATPAK_ID}.metainfo.xml', f'share/metainfo/{FLATPAK_ID}.metainfo.xml', 0o644)
    run('build-finish', str(build_dir), '--command=mouse-macro-stocazz-superpower', *flatpak_finish_args())
    run('build-export', str(repo), str(build_dir))
    output = dist / FLATPAK.format(version)
    output.unlink(missing_ok=True)
    run('build-bundle', str(repo), str(output), FLATPAK_ID,
        '--runtime-repo=https://dl.flathub.org/repo/flathub.flatpakrepo')
    return output


if __name__ == '__main__':
    build()
