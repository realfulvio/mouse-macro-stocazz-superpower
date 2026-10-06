"""Update check/install logic with a fake network; no real connection is made."""
import hashlib
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from macro import updater


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


def make_zip(version, extra=None, complete=True):
    package = updater.PACKAGE.format(version)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as z:
        if complete:
            z.writestr(f'{package}/runtime/pythonw.exe', b'MZ')
            z.writestr(f'{package}/app/windows_main.py', b'print(1)')
        for name, data in (extra or {}).items():
            z.writestr(name, data)
    return buffer.getvalue()


class FakeNet:
    def __init__(self, version='1.2.0', zip_bytes=None, sha=None, fail=False):
        self.version = version
        self.zip_bytes = zip_bytes if zip_bytes is not None else make_zip(version)
        self.sha = sha or hashlib.sha256(self.zip_bytes).hexdigest()
        self.fail = fail
        self.urls = []
        package = updater.PACKAGE.format(version)
        self.release = {
            'tag_name': f'v{version}',
            'assets': [
                {'name': package + '.zip', 'browser_download_url': 'https://x/zip'},
                {'name': f'SHA256SUMS-v{version}.txt', 'browser_download_url': 'https://x/sums'},
            ]}

    def __call__(self, request, timeout=None):
        if self.fail:
            raise OSError('offline')
        url = request.full_url
        self.urls.append(url)
        if url == updater.API_URL:
            return FakeResponse(json.dumps(self.release).encode())
        if url == 'https://x/zip':
            return FakeResponse(self.zip_bytes)
        package = updater.PACKAGE.format(self.version)
        return FakeResponse(f'{self.sha}  {package}.zip\n{self.sha}  Other.zip\n'.encode())


class VersionTests(unittest.TestCase):
    def test_parse_and_compare(self):
        self.assertEqual(updater.parse_version('v1.0.1'), (1, 0, 1))
        self.assertEqual(updater.parse_version('1.2'), (1, 2, 0))
        self.assertEqual(updater.parse_version('0.19.1-beta'), (0, 19, 1))
        self.assertTrue(updater.is_newer('1.10.0', '1.9.9'))
        self.assertFalse(updater.is_newer('1.0.1', '1.0.1'))
        self.assertFalse(updater.is_newer('1.0.0', '1.0.1'))
        with self.assertRaises(ValueError):
            updater.parse_version('boh')


class CheckTests(unittest.TestCase):
    def test_available_and_current(self):
        self.assertEqual(updater.check('1.0.1', FakeNet('1.2.0'))[0], 'available')
        self.assertEqual(updater.check('1.2.0', FakeNet('1.2.0'))[0], 'current')

    def test_offline_gives_readable_error(self):
        with self.assertRaises(updater.UpdateError):
            updater.check('1.0.1', FakeNet(fail=True))

    def test_garbage_response_gives_readable_error(self):
        with self.assertRaises(updater.UpdateError):
            updater.check('1.0.1', lambda request, timeout=None: FakeResponse(b'<html>'))

    def test_check_only_reads_the_release_api(self):
        net = FakeNet()
        updater.check('1.0.1', net)
        self.assertEqual(net.urls, [updater.API_URL])


class InstallTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / 'Portable'

    def tearDown(self):
        self.tmp.cleanup()

    def release(self, net):
        return updater.fetch_latest(net)

    def test_install_verifies_and_extracts(self):
        net = FakeNet('1.2.0')
        target = updater.install(self.release(net), self.root, net)
        self.assertEqual(target, self.root / updater.PACKAGE.format('1.2.0'))
        self.assertTrue((target / 'runtime' / 'pythonw.exe').is_file())
        self.assertTrue((target / 'app' / 'windows_main.py').is_file())

    def test_wrong_hash_is_rejected_and_nothing_is_installed(self):
        net = FakeNet('1.2.0', sha='0' * 64)
        with self.assertRaises(updater.UpdateError):
            updater.install(self.release(net), self.root, net)
        self.assertFalse(list(self.root.glob('*')))

    def test_path_traversal_is_rejected(self):
        evil = make_zip('1.2.0', extra={'../evil.txt': b'x'})
        net = FakeNet('1.2.0', zip_bytes=evil)
        with self.assertRaises(updater.UpdateError):
            updater.install(self.release(net), self.root, net)
        self.assertFalse((self.root.parent / 'evil.txt').exists())

    def test_incomplete_package_is_rejected(self):
        net = FakeNet('1.2.0', zip_bytes=make_zip('1.2.0', complete=False))
        with self.assertRaises(updater.UpdateError):
            updater.install(self.release(net), self.root, net)

    def test_offline_install_is_a_readable_error(self):
        net = FakeNet('1.2.0')
        release = self.release(net)
        net.fail = True
        with self.assertRaises(updater.UpdateError):
            updater.install(release, self.root, net)

    def test_older_packages_are_pruned_but_kept_ones_survive(self):
        old = self.root / updater.PACKAGE.format('1.0.0')
        running = self.root / updater.PACKAGE.format('1.1.0')
        other = self.root / 'AltraCartella'
        for folder in (old, running, other):
            folder.mkdir(parents=True)
        net = FakeNet('1.2.0')
        updater.install(self.release(net), self.root, net, keep=[running])
        self.assertFalse(old.exists())
        self.assertTrue(running.exists())
        self.assertTrue(other.exists())


if __name__ == '__main__':
    unittest.main()
