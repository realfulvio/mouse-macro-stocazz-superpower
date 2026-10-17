"""Linux release package and install.sh, with fake binaries and file:// downloads."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest

import package_linux
from macro.linux_updater import BINARIES, PACKAGE, SUMS
from macro.panel_model import LINUX_VERSION

ROOT = Path(__file__).resolve().parent


@unittest.skipUnless(sys.platform == 'linux' and shutil.which('bash') and shutil.which('curl'),
                     'Linux package and installer')
class LinuxPackageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.dist = self.base / 'dist'
        self.dist.mkdir()
        for name in BINARIES:
            binary = self.dist / name
            binary.write_bytes(f'#!/bin/sh\necho {name} "$@" > "$MMSS_TEST_LOG"\n'.encode())
        self.archive, self.installer, self.sums = package_linux.build(self.dist)
        self.package = PACKAGE.format(LINUX_VERSION)

    def test_archive_layout_modes_manifest_and_checksums(self):
        with tarfile.open(self.archive) as tar:
            members = {m.name: m for m in tar.getmembers()}
            self.assertTrue(all(name == self.package or name.startswith(self.package + '/') for name in members))
            for name in BINARIES + ('setup-linux-input.sh',):
                self.assertEqual(members[f'{self.package}/{name}'].mode, 0o755)
            self.assertEqual(members[f'{self.package}/LICENSE'].mode, 0o644)
            self.assertTrue(all(m.uid == 0 and m.isfile() or m.isdir() for m in members.values()))
            manifest = json.load(tar.extractfile(f'{self.package}/build_info.json'))
            self.assertEqual(manifest['version'], LINUX_VERSION)
            for name, digest in manifest['sha256'].items():
                data = tar.extractfile(f'{self.package}/{name}').read()
                self.assertEqual(hashlib.sha256(data).hexdigest(), digest, name)
        self.assertEqual(self.installer.read_bytes(), (ROOT / 'install.sh').read_bytes())
        lines = self.sums.read_text().splitlines()
        self.assertEqual([line.split()[1] for line in lines], [self.archive.name, 'install.sh'])
        for line in lines:
            digest, name = line.split()
            self.assertEqual(hashlib.sha256((self.dist / name).read_bytes()).hexdigest(), digest)

    def test_archive_is_reproducible(self):
        first = self.archive.read_bytes()
        package_linux.build(self.dist)
        self.assertEqual(first, self.archive.read_bytes())

    def test_archive_is_accepted_by_the_in_app_updater_checks(self):
        from macro import linux_updater

        class Net:
            def __init__(net, files):
                net.files = files

            def __call__(net, request, timeout=None):
                from test_linux_updater import FakeResponse
                return FakeResponse(net.files[request.full_url])

        sums = SUMS.format(LINUX_VERSION)
        release = {'version': LINUX_VERSION, 'assets': {self.archive.name: 'https://x/a', sums: 'https://x/s'}}
        net = Net({'https://x/a': self.archive.read_bytes(), 'https://x/s': self.sums.read_bytes()})
        target = linux_updater.install(release, self.base / 'data', net)
        self.assertTrue(all(os.access(target / name, os.X_OK) for name in BINARIES))

    # install.sh ----------------------------------------------------------
    def publish(self, tag=None, archive=None):
        """Lay out a fake GitHub: releases.json plus download folder."""
        tag = tag or f'linux-v{LINUX_VERSION}'
        server = self.base / 'server'
        folder = server / 'download' / tag
        folder.mkdir(parents=True, exist_ok=True)
        shutil.copy(self.sums, folder)
        (folder / self.archive.name).write_bytes(archive or self.archive.read_bytes())
        releases = [{'tag_name': 'v1.1.1', 'assets': []},
                    {'tag_name': 'linux-v99.0.0', 'prerelease': True},
                    {'tag_name': tag, 'prerelease': False, 'draft': False}]
        (server / 'releases.json').write_text(json.dumps(releases))
        return server

    def run_installer(self, server, *args):
        env = dict(os.environ, XDG_DATA_HOME=str(self.base / 'data'),
                   MMSS_API_URL=f'file://{server}/releases.json',
                   MMSS_DOWNLOAD_BASE=f'file://{server}/download',
                   MMSS_TEST_LOG=str(self.base / 'started.log'))
        return subprocess.run(['bash', str(self.installer), *args], env=env, capture_output=True, text=True,
                              timeout=60)

    def test_installer_verifies_extracts_creates_launcher_and_starts(self):
        result = self.run_installer(self.publish(), '--en')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('SHA-256 verificato', result.stdout)
        root = self.base / 'data' / 'MouseMacroStocazzSuperpower'
        self.assertEqual(os.readlink(root / 'current'), self.package)
        self.assertTrue(os.access(root / self.package / BINARIES[0], os.X_OK))
        desktop = (self.base / 'data' / 'applications' / 'mouse-macro-stocazz-superpower.desktop').read_text()
        self.assertIn('MouseMacroStocazzSuperpower-Linux-EN', desktop)
        for _ in range(50):
            if (self.base / 'started.log').exists():
                break
            import time
            time.sleep(.1)
        self.assertIn('MouseMacroStocazzSuperpower-Linux-EN', (self.base / 'started.log').read_text())

    def test_installer_rejects_a_tampered_archive(self):
        tampered = bytearray(self.archive.read_bytes())
        tampered[-20] ^= 0xFF
        result = self.run_installer(self.publish(archive=bytes(tampered)), '--no-start')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('SHA-256 diverso', result.stderr)
        self.assertFalse((self.base / 'data' / 'MouseMacroStocazzSuperpower' / self.package).exists())

    def test_installed_version_is_reused_without_download_and_offline(self):
        server = self.publish()
        self.assertEqual(self.run_installer(server, '--no-start').returncode, 0)
        (server / 'download' / f'linux-v{LINUX_VERSION}' / self.archive.name).unlink()
        result = self.run_installer(server, '--no-start')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn('Scarico', result.stdout)
        (server / 'releases.json').unlink()
        result = self.run_installer(server, '--no-start')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('Controllo online non riuscito', result.stdout)

    def test_installer_fails_cleanly_without_releases(self):
        server = self.publish()
        (server / 'releases.json').write_text('[{"tag_name": "v1.1.1"}]')
        result = self.run_installer(server, '--no-start')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('non trovo una release Linux', result.stderr)


if __name__ == '__main__':
    unittest.main()
