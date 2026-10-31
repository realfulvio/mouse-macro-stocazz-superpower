import json
import struct
import tempfile
import unittest
import zlib
import zipfile
from pathlib import Path

from macro import mods
from macro.events import LEFT_DOWN, LEFT_UP, MOVE_ABS, Macro, MacroEvent


def png(width=8, height=8):
    def chunk(kind, data):
        body = kind + data
        return struct.pack('>I', len(data)) + body + struct.pack('>I', zlib.crc32(body))
    raw = b''.join(b'\x00' + b'\x80\x40\xc0\xff' * width for _ in range(height))
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b''))


def manifest(**over):
    data = dict(format=1, id='viola-test', kind='theme', name='Viola test', version='1.0', author='Luca',
                description='Prova')
    data.update(over)
    return json.dumps(data).encode()


class ModTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.mods = self.root / 'mods'

    def package(self, files, name='x.mmmod'):
        path = self.root / name
        with zipfile.ZipFile(path, 'w') as z:
            for n, data in files.items():
                z.writestr(n, data)
        return path

    def theme_files(self, **over):
        files = {'mod.json': manifest(), 'theme.json': json.dumps({'colors': {'background': '#112233'}}).encode()}
        files.update({f'horses/{s}.png': png() for s in mods.STATES})
        files.update(over)
        return files

    def macro_bytes(self):
        path = self.root / 'm.mmr'
        Macro('windows', [MacroEvent(0, MOVE_ABS, x=1, y=2), MacroEvent(.1, LEFT_DOWN, x=1, y=2),
                          MacroEvent(.2, LEFT_UP, x=1, y=2)]).save(str(path))
        return path.read_bytes()

    def test_valid_theme_installs_and_loads(self):
        package = self.package(self.theme_files())
        info = mods.inspect(package)
        self.assertEqual((info.id, info.kind), ('viola-test', 'theme'))
        self.assertEqual(len(info.sha256), 64)
        self.assertIn('Nessun codice', info.summary()[-1])
        done = mods.install(package, self.mods)
        self.assertEqual([m.id for m in mods.installed(self.mods)], ['viola-test'])
        colors, regions, folder = mods.load_theme(done)
        self.assertEqual(colors['background'], '#112233')
        self.assertIsNone(regions)
        self.assertTrue((folder / 'pronto.png').is_file())
        self.assertEqual(mods.installed(self.mods)[0].sha256, info.sha256)

    def test_reinstall_replaces_and_remove_deletes(self):
        mods.install(self.package(self.theme_files()), self.mods)
        mods.install(self.package(self.theme_files(**{'mod.json': manifest(version='2.0')}), 'y.mmmod'), self.mods)
        self.assertEqual(mods.installed(self.mods)[0].version, '2.0')
        mods.remove(self.mods, 'viola-test')
        self.assertEqual(mods.installed(self.mods), [])
        with self.assertRaises(mods.ModError):
            mods.remove(self.mods, '../x')

    def rejects(self, files, text=None):
        with self.assertRaises(mods.ModError) as ctx:
            mods.install(self.package(files), self.mods)
        if text:
            self.assertIn(text, str(ctx.exception))
        self.assertFalse(self.mods.exists() and any(self.mods.iterdir()))  # nulla di scritto

    def test_code_and_unknown_files_are_rejected(self):
        self.rejects(self.theme_files(**{'evil.py': b'import os'}), 'non ammessi')
        self.rejects(self.theme_files(**{'horses/../../x.png': png()}), 'non ammessi')
        self.rejects(self.theme_files(**{'/abs.png': png()}))

    def test_manifest_rules(self):
        self.rejects(self.theme_files(**{'mod.json': manifest(id='bambola')}), 'riservato')
        self.rejects(self.theme_files(**{'mod.json': manifest(id='../x')}), 'id')
        self.rejects(self.theme_files(**{'mod.json': manifest(kind='plugin')}), 'kind')
        self.rejects(self.theme_files(**{'mod.json': manifest(format=2)}), 'Formato')
        self.rejects(self.theme_files(**{'mod.json': b'{'}), 'JSON')

    def test_theme_content_rules(self):
        bad = lambda colors: self.theme_files(**{'theme.json': json.dumps({'colors': colors}).encode()})
        self.rejects(bad({'background': 'red'}), 'colore')
        self.rejects(bad({'comando': '#112233'}), 'colore')
        self.rejects(self.theme_files(**{'horses/pronto.png': b'not a png'}), 'PNG')
        self.rejects(self.theme_files(**{'horses/pronto.png': png(3000, 4)}), 'grande')

    def test_region_must_fit_inside_the_image(self):
        regions = {s: [0, 0, 8, 8] for s in mods.STATES}
        ok = self.theme_files(**{'theme.json': json.dumps({'colors': {'text': '#ffffff'}, 'regions': regions}).encode()})
        self.assertEqual(mods.load_theme(mods.install(self.package(ok), self.mods))[1]['pronto'], (0, 0, 8, 8))
        regions['errore'] = [4, 4, 8, 8]
        bad = self.theme_files(**{'theme.json': json.dumps({'colors': {'text': '#ffffff'}, 'regions': regions}).encode()})
        with self.assertRaises(mods.ModError):
            mods.inspect(self.package(bad, 'z.mmmod'))

    def test_package_limits(self):
        self.rejects({'mod.json': b'x' * (mods.MAX_FILE + 1)}, 'troppo')
        path = self.root / 'bad.mmmod'
        path.write_bytes(b'PK nope')
        with self.assertRaises(mods.ModError):
            mods.inspect(path)

    def test_macro_pack(self):
        data = self.macro_bytes()
        files = {'mod.json': manifest(id='macro-ced', kind='macros'), 'macros/login portale.mmr': data}
        info = mods.install(self.package(files), self.mods)
        self.assertIn('1 macro', info.summary()[0])
        self.assertTrue((self.mods / 'macro-ced' / 'macros' / 'login portale.mmr').is_file())

    def test_macro_pack_rejects_invalid_macro_and_extra_files(self):
        self.rejects({'mod.json': manifest(id='macro-ced', kind='macros'), 'macros/a.mmr': b'{"x":1}'}, 'non è valida')
        self.rejects({'mod.json': manifest(id='macro-ced', kind='macros'), 'macros/a.sh': b'rm'}, 'non ammesso')

    def test_damaged_installed_mod_is_ignored(self):
        mods.install(self.package(self.theme_files()), self.mods)
        (self.mods / 'viola-test' / 'mod.json').write_text('{', 'utf-8')
        self.assertEqual(mods.installed(self.mods), [])


if __name__ == '__main__':
    unittest.main()
