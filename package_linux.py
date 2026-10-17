"""Linux release package: run after `build_release.py` on Linux.

Writes to dist/linux:
- MouseMacroStocazzSuperpower-Linux-v<version>.tar.gz, a single folder with the
  IT/EN binaries, the permission script, license files and build_info.json;
- install.sh (copied from the repository);
- SHA256SUMS-linux-v<version>.txt covering the archive and install.sh.
The archive is reproducible: fixed owner, permissions and timestamps.
"""
from __future__ import annotations

import gzip
import hashlib
import io
import json
from pathlib import Path
import shutil
import sys
import tarfile

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from macro.panel_model import LINUX_VERSION  # noqa: E402
from macro.linux_updater import BINARIES, PACKAGE, SUMS  # noqa: E402

FILES = {  # name in the package: (source, executable)
    'setup-linux-input.sh': ('scripts/setup-linux-input.sh', True),
    'LICENSE': ('LICENSE', False),
    'THIRD-PARTY-NOTICES.md': ('THIRD-PARTY-NOTICES.md', False),
    'GUIDA-ITALIANA.md': ('GUIDA-ITALIANA.md', False),
    'icon.png': ('assets/icon.png', False),
}
EPOCH = 1760000000  # fixed mtime for reproducible archives


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
    sums = dist / SUMS.format(version)
    sums.write_text(''.join(f'{sha256(p)}  {p.name}\n' for p in (archive, installer)), encoding='utf-8')
    print(f'{archive.name}, install.sh and {sums.name} written to {dist}', flush=True)
    return archive, installer, sums


if __name__ == '__main__':
    build()
