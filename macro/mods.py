"""Mod come pacchetti di soli dati (.mmmod = zip): temi e raccolte di macro.

Nessuna mod contiene codice: il pacchetto è accettato solo se ogni file è tra
quelli previsti, con estensione, dimensione e contenuto verificati. Niente
`extractall`: i byte validati vengono scritti da qui, quindi path traversal,
link simbolici e file inattesi non hanno modo di passare. Modulo portabile,
nessuna dipendenza dal desktop.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import tempfile
import zipfile

FORMAT = 1
KINDS = ('theme', 'macros')
RESERVED_IDS = ('bambola', 'unicorno', 'palio', 'unicorn')
STATES = ('pronto', 'registrazione', 'riproduzione', 'errore')
MAX_PACKAGE = 8 * 1024 * 1024
MAX_FILE = 4 * 1024 * 1024
MAX_TOTAL = 16 * 1024 * 1024
MAX_ENTRIES = 80
MAX_MACROS = 50
MAX_IMAGE_SIDE = 2048
ID_RE = re.compile(r'^[a-z0-9][a-z0-9-]{1,31}$')
COLOR_RE = re.compile(r'^#[0-9A-Fa-f]{6}$')
MACRO_NAME_RE = re.compile(r'^macros/[A-Za-z0-9][A-Za-z0-9 ._-]{0,60}\.mmr$')
THEME_FILES = {'mod.json', 'theme.json'} | {f'horses/{state}.png' for state in STATES}

# Chiavi colore accettate in theme.json (stesse della palette Windows di Bambola).
COLOR_KEYS = ('background', 'surface', 'alt', 'border', 'text', 'muted', 'record', 'play', 'ready',
              'warning', 'error', 'disabled', 'faded', 'header_top', 'header_bottom', 'header_text',
              'header_muted', 'header_a', 'header_b', 'chrome', 'chrome_hover', 'surface_bottom',
              'surface_hover', 'input', 'button', 'button_hover', 'on_accent', 'record_hover',
              'record_pressed', 'record_bottom', 'record_edge', 'play_hover', 'play_pressed',
              'play_bottom', 'dot_ok', 'dot_new', 'dot_off')


class ModError(ValueError):
    """Pacchetto non valido o non installabile; il testo è mostrabile all'utente."""


@dataclass
class ModInfo:
    id: str
    kind: str
    name: str
    version: str
    author: str
    description: str
    sha256: str = ''
    size: int = 0
    files: list = field(default_factory=list)
    path: Path | None = None  # cartella di installazione, se installata

    def summary(self):
        """Righe per la conferma di installazione."""
        if self.kind == 'theme':
            lines = ['Colori e 4 immagini PNG (pronto, registrazione, riproduzione, errore)']
        else:
            lines = [f'{sum(f.endswith(".mmr") for f in self.files)} macro (file .mmr)']
        return lines + ['Nessun codice: non può eseguire programmi, usare la rete o leggere i tuoi file']


def _text(value, name, limit, required=True):
    if value is None and not required:
        return ''
    if not isinstance(value, str) or (required and not value.strip()) or len(value) > limit \
            or any(ord(c) < 32 for c in value):
        raise ModError(f'mod.json: «{name}» mancante o non valido.')
    return value.strip()


def parse_manifest(raw: bytes) -> ModInfo:
    try:
        data = json.loads(raw.decode('utf-8'))
    except (UnicodeDecodeError, ValueError) as error:
        raise ModError('mod.json non è un JSON valido.') from error
    if not isinstance(data, dict) or data.get('format') != FORMAT:
        raise ModError(f'Formato mod non supportato (serve format {FORMAT}).')
    mod_id = data.get('id')
    if not isinstance(mod_id, str) or not ID_RE.fullmatch(mod_id):
        raise ModError('mod.json: «id» deve essere 2-32 caratteri tra a-z, 0-9 e trattino.')
    if mod_id in RESERVED_IDS:
        raise ModError(f'«{mod_id}» è un nome riservato ai temi integrati.')
    if data.get('kind') not in KINDS:
        raise ModError('mod.json: «kind» deve essere «theme» o «macros».')
    return ModInfo(mod_id, data['kind'], _text(data.get('name'), 'name', 40),
                   _text(data.get('version'), 'version', 16), _text(data.get('author'), 'author', 40),
                   _text(data.get('description'), 'description', 200, required=False))


def png_size(data: bytes):
    """(larghezza, altezza) di un PNG valido, altrimenti ModError."""
    if len(data) < 33 or data[:8] != b'\x89PNG\r\n\x1a\n' or data[12:16] != b'IHDR':
        raise ModError('Un\'immagine non è un PNG valido.')
    width, height = struct.unpack('>II', data[16:24])
    if not (1 <= width <= MAX_IMAGE_SIDE and 1 <= height <= MAX_IMAGE_SIDE):
        raise ModError(f'Immagine troppo grande o vuota (massimo {MAX_IMAGE_SIDE}×{MAX_IMAGE_SIDE}).')
    return width, height


def _check_theme(files: dict):
    try:
        theme = json.loads(files['theme.json'].decode('utf-8'))
    except (UnicodeDecodeError, ValueError) as error:
        raise ModError('theme.json non è un JSON valido.') from error
    colors = theme.get('colors') if isinstance(theme, dict) else None
    if not isinstance(colors, dict) or not colors:
        raise ModError('theme.json: manca «colors».')
    for key, value in colors.items():
        if key not in COLOR_KEYS or not isinstance(value, str) or not COLOR_RE.fullmatch(value):
            raise ModError(f'theme.json: colore «{key}» non valido (serve #RRGGBB e una chiave nota).')
    regions = theme.get('regions')
    if regions is not None:
        if not isinstance(regions, dict) or set(regions) != set(STATES):
            raise ModError('theme.json: «regions» deve avere i 4 stati.')
        for state, box in regions.items():
            width, height = png_size(files[f'horses/{state}.png'])
            if not (isinstance(box, list) and len(box) == 4 and all(type(n) is int for n in box)
                    and box[0] >= 0 and box[1] >= 0 and box[2] > 0 and box[3] > 0
                    and box[0] + box[2] <= width and box[1] + box[3] <= height):
                raise ModError(f'theme.json: regione «{state}» fuori dall\'immagine.')
    for state in STATES:
        png_size(files[f'horses/{state}.png'])
    return theme


def _check_macros(files: dict):
    from .events import Macro
    from .session import validate_gestures
    names = [n for n in files if n != 'mod.json']
    if not names or len(names) > MAX_MACROS:
        raise ModError(f'Servono da 1 a {MAX_MACROS} macro.')
    with tempfile.TemporaryDirectory() as folder:
        for index, name in enumerate(sorted(names)):
            path = Path(folder) / f'{index}.mmr'
            path.write_bytes(files[name])
            try:
                macro = Macro.load(str(path))
                validate_gestures(macro.events)
            except Exception as error:
                raise ModError(f'La macro «{name[7:]}» non è valida: {error}') from error


def read_package(package) -> tuple[ModInfo, dict]:
    """Legge e valida un .mmmod senza scrivere nulla. Restituisce (info, {nome: byte})."""
    package = Path(package)
    try:
        size = package.stat().st_size
        if size > MAX_PACKAGE:
            raise ModError('Il pacchetto supera 8 MB.')
        raw = package.read_bytes()
        archive = zipfile.ZipFile(package)
    except (OSError, zipfile.BadZipFile) as error:
        raise ModError('Non è un pacchetto .mmmod valido.') from error
    with archive:
        entries = [i for i in archive.infolist() if not i.is_dir()]
        if not entries or len(entries) > MAX_ENTRIES or len({i.filename for i in entries}) != len(entries):
            raise ModError('Pacchetto vuoto, con troppi file o con nomi duplicati.')
        if sum(i.file_size for i in entries) > MAX_TOTAL or any(i.file_size > MAX_FILE for i in entries):
            raise ModError('File troppo grandi nel pacchetto.')
        files = {}
        for item in entries:
            if item.flag_bits & 1:
                raise ModError('Pacchetti cifrati non supportati.')
            if (item.external_attr >> 16) & 0o170000 == 0o120000:
                raise ModError('Collegamenti simbolici non ammessi.')
            with archive.open(item) as handle:
                data = handle.read(MAX_FILE + 1)
            if len(data) > MAX_FILE or len(data) != item.file_size:
                raise ModError('File troppo grande nel pacchetto.')
            files[item.filename] = data
    if 'mod.json' not in files:
        raise ModError('Manca mod.json.')
    info = parse_manifest(files['mod.json'])
    if info.kind == 'theme':
        if set(files) != THEME_FILES:
            extra, missing = sorted(set(files) - THEME_FILES), sorted(THEME_FILES - set(files))
            raise ModError('File non ammessi: ' + ', '.join(extra[:3]) if extra else 'File mancanti: ' + ', '.join(missing[:3]))
        _check_theme(files)
    else:
        bad = [n for n in files if n != 'mod.json' and not MACRO_NAME_RE.fullmatch(n)]
        if bad:
            raise ModError(f'File non ammesso: {bad[0]}')
        _check_macros(files)
    info.sha256, info.size, info.files = hashlib.sha256(raw).hexdigest(), len(raw), sorted(files)
    return info, files


def inspect(package) -> ModInfo:
    """Per la finestra di conferma: cosa contiene, senza installare."""
    return read_package(package)[0]


def install(package, mods_dir) -> ModInfo:
    """Valida e installa in `mods_dir/<id>/`, sostituendo la stessa mod già presente."""
    info, files = read_package(package)
    mods_dir = Path(mods_dir)
    mods_dir.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix='.nuova-', dir=mods_dir))
    try:
        for name, data in files.items():
            target = staging / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        (staging / 'sha256.txt').write_text(info.sha256, 'utf-8')
        final, backup = mods_dir / info.id, mods_dir / f'.vecchia-{info.id}'
        shutil.rmtree(backup, ignore_errors=True)
        if final.exists():
            os.replace(final, backup)  # se un file è in uso fallisce qui e la mod vecchia resta intatta
        try:
            os.replace(staging, final)
        except OSError:
            if backup.exists():
                os.replace(backup, final)
            raise
        shutil.rmtree(backup, ignore_errors=True)
    except OSError as error:
        shutil.rmtree(staging, ignore_errors=True)
        raise ModError(f'Installazione non riuscita: {error.strerror or error}') from error
    info.path = final
    return info


def installed(mods_dir) -> list[ModInfo]:
    """Mod presenti, riconvalidate da disco; quelle rovinate vengono ignorate."""
    found = []
    mods_dir = Path(mods_dir)
    if not mods_dir.is_dir():
        return found
    for folder in sorted(p for p in mods_dir.iterdir() if p.is_dir() and not p.name.startswith('.')):
        try:
            info = parse_manifest((folder / 'mod.json').read_bytes())
            if info.id != folder.name:
                continue
            info.path = folder
            info.files = sorted(str(p.relative_to(folder)).replace(os.sep, '/')
                                for p in folder.rglob('*') if p.is_file())
            digest = folder / 'sha256.txt'
            info.sha256 = digest.read_text('utf-8').strip() if digest.is_file() else ''
            found.append(info)
        except (OSError, ModError):
            continue
    return found


def remove(mods_dir, mod_id):
    if not ID_RE.fullmatch(mod_id or ''):
        raise ModError('Nome mod non valido.')
    shutil.rmtree(Path(mods_dir) / mod_id, ignore_errors=True)


def load_theme(info: ModInfo):
    """(colori, regioni o None, cartella immagini) di un tema installato."""
    theme = json.loads((info.path / 'theme.json').read_text('utf-8'))
    regions = theme.get('regions')
    return (theme['colors'],
            {s: tuple(b) for s, b in regions.items()} if regions else None,
            info.path / 'horses')
