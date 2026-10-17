"""Update check and install for the Linux package.

Linux releases are published with `linux-v*` tags and are never marked as the
repository's latest release, which stays reserved to the Windows updater in
`macro/updater.py`. This module therefore scans the /releases list. As on
Windows, only the anonymous tag read runs automatically; downloading and
installing happen only when the user asks, and the archive is verified against
the SHA256SUMS file of the same release before anything is extracted.
"""
from __future__ import annotations

import functools
import hashlib
import json
import os
from pathlib import Path
import shutil
import ssl
import tarfile
import tempfile
import urllib.request

from .updater import REPO, UpdateError, _download, _open, is_newer, parse_version

API_URL = f'https://api.github.com/repos/{REPO}/releases?per_page=50'
TAG_PREFIX = 'linux-v'
PACKAGE = 'MouseMacroStocazzSuperpower-Linux-v{}'
SUMS = 'SHA256SUMS-linux-v{}.txt'
BINARIES = ('MouseMacroStocazzSuperpower-Linux-IT', 'MouseMacroStocazzSuperpower-Linux-EN')


# The packaged binary is built on Ubuntu, whose OpenSSL looks for CA certificates
# in /usr/lib/ssl; other distributions keep them elsewhere. Use the system bundle
# where it is, falling back to the certifi bundle shipped with the binary.
CA_BUNDLES = ('/etc/ssl/certs/ca-certificates.crt', '/etc/pki/tls/certs/ca-bundle.crt',
              '/etc/ssl/ca-bundle.pem', '/etc/ssl/cert.pem')


def ssl_context(candidates=CA_BUNDLES):
    for path in candidates:
        if os.path.isfile(path):
            return ssl.create_default_context(cafile=path)
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except (ImportError, OSError):
        return ssl.create_default_context()


def default_opener():
    return functools.partial(urllib.request.urlopen, context=ssl_context())


def data_root():
    """Install folder of the packages, shared with install.sh."""
    base = Path(os.environ.get('XDG_DATA_HOME') or Path.home() / '.local' / 'share')
    return base / 'MouseMacroStocazzSuperpower'


def pick_latest(releases):
    """Return the newest published, non-draft, non-prerelease `linux-v*` release."""
    best = None
    for data in releases if isinstance(releases, list) else []:
        try:
            tag = str(data['tag_name'])
            if not tag.startswith(TAG_PREFIX) or data.get('draft') or data.get('prerelease'):
                continue
            version = tag[len(TAG_PREFIX):]
            parse_version(version)
            assets = {a['name']: a['browser_download_url'] for a in data.get('assets', [])}
        except (KeyError, TypeError, ValueError):
            continue
        if best is None or is_newer(version, best['version']):
            best = {'version': version, 'tag': tag, 'assets': assets}
    return best


def fetch_latest(opener=None):
    """Return {'version', 'tag', 'assets': {name: url}} for the newest Linux release."""
    try:
        with _open(API_URL, opener or default_opener()) as response:
            releases = json.loads(response.read(5_000_000).decode('utf-8'))
    except (OSError, ValueError) as error:
        raise UpdateError('Non riesco a controllare gli aggiornamenti.') from error
    release = pick_latest(releases)
    if release is None:
        raise UpdateError('Nessuna release Linux pubblicata su GitHub.')
    return release


def check(current, opener=None):
    """Return ('current'|'available', release)."""
    release = fetch_latest(opener)
    return ('available' if is_newer(release['version'], current) else 'current'), release


def expected_digest(sums_file, name):
    for line in Path(sums_file).read_text('utf-8', 'replace').splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[1].lstrip('*') == name:
            return parts[0].lower()
    return None


def install(release, root=None, opener=None, keep=()):
    """Download, verify and extract `release` under `root`; return the package folder.

    `root/current` is pointed at the new package so launchers created by
    install.sh start the updated version."""
    version = release['version']
    package = PACKAGE.format(version)
    archive_name = package + '.tar.gz'
    sums_name = SUMS.format(version)
    try:
        archive_url, sums_url = release['assets'][archive_name], release['assets'][sums_name]
    except KeyError as error:
        raise UpdateError('La release non contiene il pacchetto Linux e SHA256SUMS attesi.') from error
    opener = opener or default_opener()
    root = Path(root) if root else data_root()
    root.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix='mmss-update-', dir=root))
    try:
        try:
            _download(sums_url, work / 'sums.txt', opener)
            _download(archive_url, work / archive_name, opener)
        except OSError as error:
            raise UpdateError('Download non riuscito: controlla la connessione.') from error
        expected = expected_digest(work / 'sums.txt', archive_name)
        with open(work / archive_name, 'rb') as stream:
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        if expected is None or digest != expected:
            raise UpdateError('SHA-256 diverso dall’atteso: download scartato.')
        staging = work / 'extract'
        try:
            with tarfile.open(work / archive_name, 'r:gz') as archive:
                base = staging.resolve()
                for member in archive.getmembers():
                    if not (staging / member.name).resolve().is_relative_to(base):
                        raise UpdateError('Archivio con percorsi non sicuri: scartato.')
                    if not (member.isfile() or member.isdir()):
                        raise UpdateError('Archivio con collegamenti o file speciali: scartato.')
                archive.extractall(staging, filter='data')
        except (tarfile.TarError, EOFError, OSError) as error:
            raise UpdateError('Archivio danneggiato: download scartato.') from error
        source = staging / package
        if not all((source / name).is_file() for name in BINARIES):
            raise UpdateError('Il pacchetto scaricato è incompleto.')
        for name in BINARIES:
            (source / name).chmod(0o755)
        target = root / package
        if target.exists():
            shutil.rmtree(target)
        shutil.move(str(source), str(target))
        link = root / 'current'
        temporary = root / '.current.tmp'
        temporary.unlink(missing_ok=True)
        temporary.symlink_to(target.name)
        os.replace(temporary, link)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    prune(root, keep=[target, *keep])
    return target


def prune(root, keep=()):
    """Remove older package folders created by this updater; never touch `keep`."""
    keep = {Path(k).resolve() for k in keep}
    for folder in Path(root).glob(PACKAGE.format('*')):
        if folder.is_dir() and not folder.is_symlink() and folder.resolve() not in keep:
            shutil.rmtree(folder, ignore_errors=True)


def running_package():
    """Folder of the running packaged binary, or None when started from source."""
    import sys
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).resolve().parent
    return None
