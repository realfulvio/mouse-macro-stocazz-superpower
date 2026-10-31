"""Update check and install from the official GitHub release.

The only network access of the program. Nothing runs automatically except the
anonymous read of the latest release tag; downloading and installing happen only
when the user asks. Every downloaded file is verified against the SHA256SUMS file
published in the same release before it is used.

Two kinds of copies are updated differently:
- portable (ZIP or install.ps1): the new ZIP is extracted next to the old one;
- installed with the setup program (unins000.exe next to runtime/): the new
  setup is downloaded and run silently, so shortcuts and the entry in
  "Installed apps" keep pointing at the same folder.
"""
from __future__ import annotations
import hashlib
import json
import re
import shutil
import tempfile
import urllib.request
import zipfile
from pathlib import Path

REPO = 'realfulvio/mouse-macro-stocazz-superpower'
API_URL = f'https://api.github.com/repos/{REPO}/releases/latest'
TIMEOUT = 8
PACKAGE = 'MouseMacroStocazzSuperpower-Windows-v{}'
SETUP = 'MouseMacroStocazzSuperpower-Setup-v{}.exe'
SETUP_ARGS = ('/SILENT', '/SUPPRESSMSGBOXES', '/NORESTART', '/SP-')
MAX_BYTES = 200 * 1024 * 1024


class UpdateError(Exception):
    """Readable failure for the status line."""


def parse_version(text):
    numbers = re.findall(r'\d+', str(text).split('-')[0])
    if not numbers:
        raise ValueError(f'versione non valida: {text!r}')
    return tuple(int(n) for n in numbers[:3]) + (0,) * (3 - len(numbers[:3]))


def is_newer(candidate, current):
    return parse_version(candidate) > parse_version(current)


def _open(url, opener=None):
    request = urllib.request.Request(url, headers={'User-Agent': 'MouseMacro-update-check',
                                                   'Accept': 'application/vnd.github+json'})
    return (opener or urllib.request.urlopen)(request, timeout=TIMEOUT)


def fetch_latest(opener=None):
    """Return {'version', 'assets': {name: url}} for the latest published release."""
    try:
        with _open(API_URL, opener) as response:
            data = json.loads(response.read(1_000_000).decode('utf-8'))
        version = str(data['tag_name']).lstrip('vV')
        parse_version(version)
        assets = {a['name']: a['browser_download_url'] for a in data.get('assets', [])}
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise UpdateError('Non riesco a controllare gli aggiornamenti.') from error
    return {'version': version, 'assets': assets}


def check(current, opener=None):
    """Return ('current'|'available', release)."""
    release = fetch_latest(opener)
    return ('available' if is_newer(release['version'], current) else 'current'), release


def _download(url, target, opener=None):
    size = 0
    with _open(url, opener) as response, open(target, 'wb') as out:
        while True:
            chunk = response.read(1 << 16)
            if not chunk:
                return
            size += len(chunk)
            if size > MAX_BYTES:
                raise UpdateError('Download troppo grande: annullato.')
            out.write(chunk)


def is_installed(app_root):
    """True when this copy was installed by the setup program (it has an uninstaller)."""
    return any(Path(app_root).glob('unins*.exe'))


def _fetch_verified(release, name, work, opener=None, missing='La release non contiene i file attesi.'):
    """Download asset `name` of `release` into `work`; check it against SHA256SUMS."""
    sums_name = f'SHA256SUMS-v{release["version"]}.txt'
    try:
        url, sums_url = release['assets'][name], release['assets'][sums_name]
    except KeyError as error:
        raise UpdateError(missing) from error
    try:
        _download(sums_url, work / 'sums.txt', opener)
        _download(url, work / name, opener)
    except OSError as error:
        raise UpdateError('Download non riuscito: controlla la connessione.') from error
    expected = None
    for line in (work / 'sums.txt').read_text('utf-8', 'replace').splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[1].lstrip('*') == name:
            expected = parts[0].lower()
    digest = hashlib.sha256((work / name).read_bytes()).hexdigest()
    if expected is None or digest != expected:
        raise UpdateError('SHA-256 diverso dall’atteso: download scartato.')
    return work / name


def download_setup(release, opener=None):
    """Download and verify the setup program of `release`; return its path.

    The file stays in a fresh temporary folder because it is run right after;
    Windows cleans %TEMP% on its own.
    """
    name = SETUP.format(release['version'])
    work = Path(tempfile.mkdtemp(prefix='mmss-setup-'))
    try:
        setup = _fetch_verified(release, name, work, opener,
                                'La release non contiene il programma di installazione.')
        if setup.read_bytes()[:2] != b'MZ':
            raise UpdateError('Il programma di installazione scaricato non è valido.')
    except BaseException:
        shutil.rmtree(work, ignore_errors=True)
        raise
    (work / 'sums.txt').unlink(missing_ok=True)
    return setup


def install(release, root, opener=None, keep=()):
    """Download, verify and extract `release` under `root`; return the package folder."""
    version = release['version']
    package = PACKAGE.format(version)
    zip_name = package + '.zip'
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix='mmss-update-'))
    try:
        _fetch_verified(release, zip_name, work, opener, 'La release non contiene ZIP e SHA256SUMS attesi.')
        staging = work / 'extract'
        with zipfile.ZipFile(work / zip_name) as archive:
            if archive.testzip() is not None:
                raise UpdateError('ZIP danneggiato: download scartato.')
            base = staging.resolve()
            for name in archive.namelist():
                if not (staging / name).resolve().is_relative_to(base):
                    raise UpdateError('ZIP con percorsi non sicuri: scartato.')
            archive.extractall(staging)
        source = staging / package
        if not (source / 'runtime' / 'pythonw.exe').is_file() or not (source / 'app' / 'windows_main.py').is_file():
            raise UpdateError('Il pacchetto scaricato è incompleto.')
        target = root / package
        if target.exists():
            shutil.rmtree(target)
        shutil.move(str(source), str(target))
    finally:
        shutil.rmtree(work, ignore_errors=True)
    prune(root, keep=[target, *keep])
    return target


def prune(root, keep=()):
    """Remove older package folders created by this updater; never touch `keep`."""
    keep = {Path(k).resolve() for k in keep}
    for folder in Path(root).glob(PACKAGE.format('*')):
        if folder.is_dir() and folder.resolve() not in keep:
            shutil.rmtree(folder, ignore_errors=True)
