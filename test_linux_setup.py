import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from macro import linux_setup

ROOT = Path(__file__).resolve().parent


class LinuxSetupTests(unittest.TestCase):
    def test_rules_match_the_manual_script(self):
        script = (ROOT / 'scripts' / 'setup-linux-input.sh').read_text(encoding='utf-8')
        self.assertIn(linux_setup.RULES, script)
        self.assertIn(linux_setup.RULES, linux_setup.GRANT_SCRIPT)
        self.assertIn(f'mv -f {linux_setup.RULE_FILE}.tmp {linux_setup.RULE_FILE}', linux_setup.GRANT_SCRIPT)

    @unittest.skipUnless(sys.platform == 'linux', 'POSIX shell')
    def test_grant_script_is_valid_shell(self):
        subprocess.run(['sh', '-n'], input=linux_setup.GRANT_SCRIPT, text=True, check=True)

    def test_clean_env_restores_pyinstaller_library_path(self):
        env = linux_setup.clean_env({'LD_LIBRARY_PATH': '/tmp/_MEI1', 'LD_LIBRARY_PATH_ORIG': '/opt/lib',
                                     'PATH': '/usr/bin'})
        self.assertEqual(env['LD_LIBRARY_PATH'], '/opt/lib')
        self.assertNotIn('LD_LIBRARY_PATH_ORIG', env)
        env = linux_setup.clean_env({'LD_LIBRARY_PATH': '/tmp/_MEI1'})
        self.assertNotIn('LD_LIBRARY_PATH', env)

    def test_grant_access_uses_pkexec_with_script_on_stdin(self):
        done = subprocess.CompletedProcess([], 0, '', '')
        with patch.object(linux_setup.shutil, 'which', return_value='/usr/bin/pkexec'), \
                patch.object(linux_setup, 'in_flatpak', return_value=False), \
                patch.object(linux_setup.subprocess, 'run', return_value=done) as run:
            self.assertEqual(linux_setup.grant_access(), (True, ''))
        args, kwargs = run.call_args
        self.assertEqual(args[0], ['/usr/bin/pkexec', '/bin/sh', '-s'])
        self.assertEqual(kwargs['input'], linux_setup.GRANT_SCRIPT)

    def test_grant_access_reports_cancel_and_flatpak(self):
        with patch.object(linux_setup.shutil, 'which', return_value='/usr/bin/pkexec'), \
                patch.object(linux_setup, 'in_flatpak', return_value=False), \
                patch.object(linux_setup.subprocess, 'run', return_value=subprocess.CompletedProcess([], 126, '', '')):
            self.assertEqual(linux_setup.grant_access(), (False, 'annullato'))
        with patch.object(linux_setup, 'in_flatpak', return_value=True):
            self.assertFalse(linux_setup.grant_access()[0])
            self.assertFalse(linux_setup.can_grant())

    def test_input_access_on_missing_devices(self):
        access = linux_setup.input_access('/nonexistent/event*', '/nonexistent/uinput')
        self.assertFalse(access['events'])
        self.assertFalse(access['uinput'])

    def test_appimage_menu_entry_follows_the_file(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            image = folder / 'My Apps' / 'MMSS.AppImage'
            image.parent.mkdir()
            image.write_bytes(b'x')
            icon = ROOT / 'assets' / 'icon.png'
            with patch.dict(os.environ, {}, clear=False):
                os.environ.pop('MMSS_NO_DESKTOP_ENTRY', None)
                desktop = linux_setup.integrate_appimage(str(image), icon, folder / 'share')
            text = desktop.read_text(encoding='utf-8')
            self.assertIn(f'Exec="{image}"', text)
            self.assertIn(f'TryExec={image}', text)
            self.assertIn('StartupWMClass=com.appveyor.flet', text)
            self.assertTrue((folder / 'share' / 'icons' / 'hicolor' / '256x256' / 'apps' /
                             'mouse-macro-stocazz-superpower.png').is_file())
            self.assertIsNone(linux_setup.integrate_appimage(str(folder / 'missing.AppImage'), icon,
                                                             folder / 'share'))

    def test_install_hint_names_packages(self):
        hint = linux_setup.install_hint(['libsecret-1.so.0', 'libunknown.so'])
        self.assertIn('apt install libsecret-1-0', hint)
        self.assertIn('pacman -S libsecret', hint)
        self.assertEqual(linux_setup.install_hint(['libunknown.so']), '')

    def test_startup_failure_writes_log_and_shows_message(self):
        with tempfile.TemporaryDirectory() as folder, \
                patch.object(linux_setup, 'flet_clients', return_value=[Path('/x/flet')]), \
                patch.object(linux_setup, 'missing_libraries', return_value=['libsecret-1.so.0']), \
                patch.object(linux_setup, 'show_message') as show:
            self.assertEqual(linux_setup.startup_failure(folder, 'en'), ['libsecret-1.so.0'])
            self.assertIn('libsecret-1.so.0', (Path(folder) / 'errore-avvio.log').read_text(encoding='utf-8'))
            title, text = show.call_args.args
            self.assertIn('could not start', title)
            self.assertIn('libsecret', text)


if __name__ == '__main__':
    unittest.main()
