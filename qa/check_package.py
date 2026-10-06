"""Static package integrity checks; deliberately does not claim GUI acceptance."""
import hashlib
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
    for name in ('windows_main.py','windows_visual.py','macro/__init__.py','macro/events.py','macro/engine.py',
                 'macro/session.py','macro/windows_backend.py','macro/win_dialogs.py'):
        assert z.read(prefix+'app/'+name) == (ROOT/name).read_bytes(), name
    for folder in ('horses','icons','fonts'):
        for asset in (ROOT/'assets'/folder).iterdir():
            if folder != 'fonts' or asset.name in ('Outfit-Regular.ttf','Outfit-Bold.ttf','Outfit-OFL.txt'):
                assert z.read(prefix+'app/assets/'+folder+'/'+asset.name)==asset.read_bytes(),asset.name
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
              'compiler':manifest['compiler'],'crc_errors':0}
    (ROOT/'evidence').mkdir(exist_ok=True)
    (ROOT/'evidence/package-static-final.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
