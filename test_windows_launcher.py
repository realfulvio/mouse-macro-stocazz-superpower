import re
import unittest
from pathlib import Path

from macro import updater
from macro.session import VERSION

ROOT = Path(__file__).resolve().parent
SOURCE = (ROOT / 'launcher.cs').read_text(encoding='utf-8')


class LauncherSourceTests(unittest.TestCase):
    def test_version_matches_the_program(self):
        self.assertIn(f'const string Version = "{VERSION}";', SOURCE)
        self.assertEqual(re.findall(r'Assembly(?:File)?Version\("([^"]+)"\)', SOURCE), [f'{VERSION}.0'] * 2)

    def test_installs_where_the_updater_puts_new_versions(self):
        # The fixed launcher picks the newest folder under Portable\, so updates
        # installed from the panel are what the shortcuts start.
        self.assertIn('Path.Combine(Home, "Portable")', SOURCE)
        self.assertIn(f'const string Prefix = "{updater.PACKAGE.format("")}";', SOURCE)

    def test_per_user_shortcuts_and_uninstall_entry(self):
        self.assertIn('SpecialFolder.Programs', SOURCE)
        self.assertIn('SpecialFolder.DesktopDirectory', SOURCE)
        self.assertIn('Registry.CurrentUser', SOURCE)
        self.assertNotIn('Registry.LocalMachine', SOURCE)
        self.assertIn('--uninstall', SOURCE)

    def test_launcher_does_not_wait_for_the_panel(self):
        self.assertNotIn('WaitForExit', SOURCE)


if __name__ == '__main__':
    unittest.main()
