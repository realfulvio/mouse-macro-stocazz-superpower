"""Linux update check/install with a fake network; no real connection is made."""
import hashlib
import io
import json
import os
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from macro import linux_updater, updater
from macro.updater import UpdateError


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


def make_tar(version, complete=True, extra=None, link=False):
    package = linux_updater.PACKAGE.format(version)
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode='w:gz') as archive:
        names = linux_updater.BINARIES if complete else linux_updater.BINARIES[:1]
        for name in names:
            data = b'\x7fELF'
            info = tarfile.TarInfo(f'{package}/{name}')
            info.size, info.mode = len(data), 0o644
            archive.addfile(info, io.BytesIO(data))
        for name, data in (extra or {}).items():
            info = tarfile.TarInfo(name)
            info.size = len(data)
            archive.addfile(info, io.BytesIO(data))
        if link:
            info = tarfile.TarInfo(f'{package}/escape')
            info.type, info.linkname = tarfile.SYMTYPE, '/etc/passwd'
            archive.addfile(info)
    return buffer.getvalue()


def release_json(tag, prerelease=False, draft=False, assets=()):
    return {'tag_name': tag, 'prerelease': prerelease, 'draft': draft,
            'assets': [{'name': n, 'browser_download_url': f'https://x/{n}'} for n in assets]}


class FakeNet:
    def __init__(self, version='1.0.1', archive=None, sha=None, releases=None, fail=False):
        self.version = version
        self.archive = archive if archive is not None else make_tar(version)
        self.sha = sha or hashlib.sha256(self.archive).hexdigest()
        self.fail = fail
        self.urls = []
        package = linux_updater.PACKAGE.format(version)
        self.archive_name = package + '.tar.gz'
        self.sums_name = linux_updater.SUMS.format(version)
        self.releases = releases if releases is not None else [
            release_json('v9.9.9', assets=['MouseMacroStocazzSuperpower-Windows-v9.9.9.zip']),
            release_json(f'linux-v{version}', assets=[self.archive_name, self.sums_name, 'install.sh']),
            release_json('linux-v1.0.0', assets=['old.tar.gz']),
        ]

    def __call__(self, request, timeout=None):
        if self.fail:
            raise OSError('offline')
        url = request.full_url
        self.urls.append(url)
        if url == linux_updater.API_URL:
            return FakeResponse(json.dumps(self.releases).encode())
        if url.endswith('.tar.gz'):
            return FakeResponse(self.archive)
        return FakeResponse(f'{self.sha}  {self.archive_name}\n0000  install.sh\n'.encode())


class PickLatestTests(unittest.TestCase):
    def test_only_linux_tags_are_considered_and_windows_latest_is_ignored(self):
        releases = [release_json('v1.1.1'), release_json('v2.0.0'), release_json('linux-v1.0.0'),
                    release_json('linux-v1.2.0'), release_json('linux-v1.10.0'),
                    release_json('linux-v3.0.0', prerelease=True), release_json('linux-v4.0.0', draft=True),
                    release_json('linux-vbroken'), {'name': 'no tag'}, 'junk']
        self.assertEqual(linux_updater.pick_latest(releases)['version'], '1.10.0')
        self.assertIsNone(linux_updater.pick_latest([release_json('v1.1.1')]))
        self.assertIsNone(linux_updater.pick_latest({'message': 'rate limited'}))

    def test_reads_the_releases_list_never_releases_latest(self):
        self.assertIn('/releases?', linux_updater.API_URL)
        self.assertNotIn('/latest', linux_updater.API_URL)
        self.assertTrue(updater.API_URL.endswith('/releases/latest'))  # Windows untouched

    def test_check_states_and_errors(self):
        net = FakeNet('1.0.1')
        state, release = linux_updater.check('1.0.0', net)
        self.assertEqual((state, release['version'], release['tag']), ('available', '1.0.1', 'linux-v1.0.1'))
        self.assertEqual(linux_updater.check('1.0.1', net)[0], 'current')
        self.assertEqual(linux_updater.check('2.0.0', net)[0], 'current')
        with self.assertRaises(UpdateError):
            linux_updater.check('1.0.0', FakeNet(fail=True))
        with self.assertRaises(UpdateError):
            linux_updater.check('1.0.0', FakeNet(releases=[release_json('v1.1.1')]))


@unittest.skipUnless(sys.platform == 'linux', 'Linux package layout (symlink, executable bits)')
class InstallTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'data'

    def install(self, net, keep=()):
        _, release = linux_updater.check('1.0.0', net)
        return linux_updater.install(release, self.root, net, keep)

    def test_verified_install_sets_current_link_and_executable_bits(self):
        target = self.install(FakeNet('1.0.1'))
        self.assertEqual(target, self.root / 'MouseMacroStocazzSuperpower-Linux-v1.0.1')
        for name in linux_updater.BINARIES:
            self.assertTrue(os.access(target / name, os.X_OK))
        self.assertEqual(os.readlink(self.root / 'current'), target.name)
        self.assertEqual(sorted(p.name for p in self.root.iterdir()), ['MouseMacroStocazzSuperpower-Linux-v1.0.1', 'current'])

    def test_older_packages_are_pruned_except_running_one(self):
        old = self.root / 'MouseMacroStocazzSuperpower-Linux-v0.9.0'
        running = self.root / 'MouseMacroStocazzSuperpower-Linux-v1.0.0'
        old.mkdir(parents=True)
        running.mkdir()
        self.install(FakeNet('1.0.1'), keep=[running])
        self.assertFalse(old.exists())
        self.assertTrue(running.exists())

    def test_wrong_checksum_is_rejected_before_extracting(self):
        with self.assertRaisesRegex(UpdateError, 'SHA-256'):
            self.install(FakeNet('1.0.1', sha='0' * 64))
        self.assertFalse((self.root / 'MouseMacroStocazzSuperpower-Linux-v1.0.1').exists())
        self.assertFalse((self.root / 'current').exists())

    def test_unsafe_incomplete_or_damaged_archives_are_rejected(self):
        cases = {'percorsi': make_tar('1.0.1', extra={'../evil': b'x'}),
                 'collegamenti': make_tar('1.0.1', link=True),
                 'incompleto': make_tar('1.0.1', complete=False),
                 'danneggiato': b'not a tar archive'}
        for message, archive in cases.items():
            with self.subTest(message):
                with self.assertRaisesRegex(UpdateError, message):
                    self.install(FakeNet('1.0.1', archive=archive))
        self.assertFalse((Path(self.temp.name) / 'evil').exists())
        self.assertEqual([p.name for p in self.root.iterdir()], [])

    def test_missing_assets_and_offline_download(self):
        with self.assertRaisesRegex(UpdateError, 'SHA256SUMS'):
            linux_updater.install({'version': '1.0.1', 'assets': {}}, self.root)
        net = FakeNet('1.0.1')
        _, release = linux_updater.check('1.0.0', net)
        net.fail = True
        with self.assertRaisesRegex(UpdateError, 'Download'):
            linux_updater.install(release, self.root, net)

    def test_default_root_follows_xdg_data_home(self):
        with patch.dict(os.environ, {'XDG_DATA_HOME': self.temp.name}):
            self.assertEqual(linux_updater.data_root(), Path(self.temp.name) / 'MouseMacroStocazzSuperpower')


class CertificateTests(unittest.TestCase):
    def test_system_bundle_is_preferred_then_certifi(self):
        import ssl
        with patch.object(ssl, 'create_default_context') as create:
            linux_updater.ssl_context(['/nonexistent/a.pem', __file__])
        create.assert_called_once_with(cafile=__file__)
        import certifi
        with patch.object(ssl, 'create_default_context') as create:
            linux_updater.ssl_context(['/nonexistent/a.pem'])
        create.assert_called_once_with(cafile=certifi.where())

    def test_network_calls_use_the_verified_context_by_default(self):
        calls = []
        def fake_urlopen(request, timeout=None, context=None):
            calls.append(context)
            raise OSError('offline')
        with patch.object(linux_updater.urllib.request, 'urlopen', fake_urlopen):
            with self.assertRaises(UpdateError):
                linux_updater.fetch_latest()
        self.assertEqual(len(calls), 1)
        self.assertIsNotNone(calls[0])
        self.assertEqual(calls[0].verify_mode, __import__('ssl').CERT_REQUIRED)


if __name__ == '__main__':
    unittest.main()
