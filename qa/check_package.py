"""Static package integrity checks; deliberately does not claim GUI acceptance."""
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import zipfile
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from macro.session import VERSION

ROOT = Path(__file__).resolve().parents[1]
archive = ROOT/'dist/windows'/f'MouseMacroStocazzSuperpower-Windows-v{VERSION}.zip'
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    prefix = z.namelist()[0].split('/')[0]+'/'
    assert all(name.startswith(prefix) and '..' not in Path(name).parts for name in z.namelist())
    manifest = json.loads(z.read(prefix+'build_info.json'))
    assert manifest['version'] == VERSION
    for name, expected in manifest['sha256'].items():
        assert hashlib.sha256(z.read(prefix+name)).hexdigest() == expected, name
    listed = set(manifest['sha256'])|{'build_info.json'}
    assert {name[len(prefix):] for name in z.namelist()} == listed
    for name in ('windows_main.py','windows_panel.py','windows_visual.py','macro/__init__.py','macro/events.py','macro/engine.py',
                 'macro/session.py','macro/windows_backend.py','macro/windows_integrity.py','macro/win_dialogs.py','macro/updater.py','macro/mouse_devices.py','macro/keys.py','macro/export.py','macro/runner.py',
                 'macro/win_tray.py','macro/mods.py','windows_settings.py'):
        assert z.read(prefix+'app/'+name) == (ROOT/name).read_bytes(), name
    for folder in ('horses','icons','fonts','skins'):
        for asset in (ROOT/'assets'/folder).iterdir():
            if asset.suffix.lower() == '.webp':  # Linux panel only
                assert prefix+'app/assets/'+folder+'/'+asset.name not in z.namelist(), asset.name
            elif folder != 'fonts' or asset.name in ('Outfit-Regular.ttf','Outfit-Bold.ttf','Outfit-OFL.txt'):
                assert z.read(prefix+'app/assets/'+folder+'/'+asset.name)==asset.read_bytes(),asset.name
    # Every module of the app and of runtime/Lib ships its checked-hash .pyc (PEP 552),
    # valid for the exact source next to it; no other bytecode is in the package.
    names = set(z.namelist())
    sources = [n for n in names if n.endswith('.py') and (n.startswith(prefix+'app/') or n.startswith(prefix+'runtime/Lib/'))]
    pycs = {n for n in names if n.endswith('.pyc')}
    expected_pycs = {importlib.util.cache_from_source(n).replace('\\', '/') for n in sources}
    assert pycs == expected_pycs, sorted(pycs ^ expected_pycs)[:5]
    for source in sources:
        data = z.read(importlib.util.cache_from_source(source).replace('\\', '/'))
        assert data[:4] == importlib.util.MAGIC_NUMBER and int.from_bytes(data[4:8], 'little') == 0b11, source
        assert data[8:16] == importlib.util.source_hash(z.read(source)), source
    assert z.read(prefix+'GUIDA-ITALIANA.md') == (ROOT/'GUIDA-ITALIANA.md').read_bytes()
    for name in z.namelist():
        assert 'sitecustomize' not in name and '/flet/' not in name
    with zipfile.ZipFile(ROOT/'vendor/python-3.13.16-embed-amd64.zip') as embed:
        preserved = ('pythonw.exe','python.exe','python313.dll','python3.dll','python313.zip')
        for name in preserved:
            assert z.read(prefix+'runtime/'+name) == embed.read(name), name
    assert z.read(prefix+f'Mouse Macro v{VERSION} (senza exe).cmd') == (ROOT/'launcher.cmd').read_bytes()
    exe = z.read(prefix+f'Mouse Macro v{VERSION}.exe')
    pe = struct.unpack_from('<I',exe,0x3c)[0]
    assert exe[:2] == b'MZ' and exe[pe:pe+4] == b'PE\0\0'
    assert struct.unpack_from('<H',exe,pe+4)[0] == 0x8664
    assert struct.unpack_from('<H',exe,pe+24+68)[0] == 2  # Windows GUI subsystem
    result = {'kind':'STATIC_ONLY_NOT_WINDOWS_EXECUTION','version':manifest['version'],
              'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
              'bytes':archive.stat().st_size,'file_hashes_checked':len(manifest['sha256']),
              'source_matches':True,'runtime_original_bytes_preserved':list(preserved),
              'launcher_machine':'x86-64','launcher_subsystem':'Windows GUI',
              'compiler':manifest['compiler'],'crc_errors':0,'checked_hash_pycs':len(sources)}
    (ROOT/'evidence').mkdir(exist_ok=True)
    (ROOT/'evidence/package-static-final.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
