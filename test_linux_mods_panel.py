"""Linux panel: settings dialog, mod themes and tray actions (no real window)."""
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

from macro import mods, panel_model
from test_mods import manifest, png

if sys.platform == 'linux':
    import flet as ft
    import linux_main
    from test_linux_panel import PageStub, texts, walk


def theme_package(folder, mod_id='viola-test', background='#112233'):
    path = Path(folder) / f'{mod_id}.mmmod'
    files = {'mod.json': manifest(id=mod_id),
             'theme.json': json.dumps({'colors': {'background': background, 'text': '#ffffff'}}).encode()}
    files.update({f'horses/{s}.png': png() for s in mods.STATES})
    with zipfile.ZipFile(path, 'w') as z:
        for name, data in files.items():
            z.writestr(name, data)
    return path


@unittest.skipUnless(sys.platform == 'linux', 'Flet panel')
class ModPanelTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.prefs = self.folder / 'linux-panel.json'
        self.addCleanup(panel_model.register_mod_skins, [])

    def panel(self, settings=None):
        if settings is not None:
            self.prefs.write_text(json.dumps(settings))
        self.page = PageStub()
        self.page.window.visible = True
        return linux_main.LinuxPanel(self.page, 'it', preferences=self.prefs)

    def test_installed_theme_is_selectable_and_restored_at_launch(self):
        mods.install(theme_package(self.folder), self.folder / 'mods')
        panel = self.panel({'skin': 'mod:viola-test'})
        self.assertEqual(panel.skin, 'mod:viola-test')
        self.assertEqual(panel.colors['background'], '#112233')
        self.assertIn('mod:viola-test', [o.key for o in panel.skin_choice.options])
        self.assertTrue(panel_model.skin_is_dark('mod:viola-test'))
        self.assertIsInstance(panel.horse('pronto', 72), ft.Image)

    def test_missing_mod_theme_falls_back_to_the_default_skin(self):
        panel = self.panel({'skin': 'mod:non-esiste'})
        self.assertEqual(panel.skin, panel_model.DEFAULT_SKIN)

    def test_settings_dialog_lists_mods_and_tray_state(self):
        mods.install(theme_package(self.folder), self.folder / 'mods')
        panel = self.panel()
        panel.settings_menu()
        dialog = self.page.dialogs[-1]
        content = texts(dialog)
        self.assertIn('Viola test', content)
        self.assertTrue(any('Non disponibile' in t for t in content))  # nessun tray in test
        switch = [c for c in walk(dialog.content) if isinstance(c, ft.Switch)][0]
        self.assertTrue(switch.disabled)

    def test_remove_the_theme_in_use_goes_back_to_the_default(self):
        info = mods.install(theme_package(self.folder), self.folder / 'mods')
        panel = self.panel({'skin': 'mod:viola-test'})
        panel.settings_menu()
        panel.remove_mod(info)
        confirm = self.page.dialogs[-1]
        [b for b in walk(confirm) if isinstance(b, ft.Button) and 'Rimuovi' in texts(b)][0].on_click(None)
        self.assertEqual(panel.skin, panel_model.DEFAULT_SKIN)
        self.assertEqual(mods.installed(self.folder / 'mods'), [])
        self.assertNotIn('mod:viola-test', panel_model.SKINS)

    def test_tray_items_and_actions(self):
        panel = self.panel()
        labels = [i.label for i in panel.tray_items() if i.label]
        self.assertEqual(labels[0], 'Nascondi pannello')
        self.assertIn('Esci', labels)
        self.assertEqual([i.action for i in panel.tray_items() if i.action][-1], 'quit')

    def test_close_to_tray_only_hides_when_the_tray_exists(self):
        import asyncio
        panel = self.panel({'close_to_tray': True})
        panel.close_window = AsyncMock()
        event = SimpleNamespace(type=ft.WindowEventType.CLOSE)
        asyncio.run(panel.window_event(event))  # nessun tray registrato: chiude davvero
        panel.close_window.assert_awaited_once()
        panel.close_window.reset_mock()
        panel.tray = SimpleNamespace(registered=True, refresh=lambda: None, stop=lambda: None)
        asyncio.run(panel.window_event(event))
        panel.close_window.assert_not_awaited()
        self.assertIs(self.page.window.visible, False)

    def test_tray_toggle_and_quit(self):
        import asyncio
        panel = self.panel()
        self.page.window.to_front = AsyncMock()
        self.page.window.minimized = False
        asyncio.run(panel.tray_action('toggle'))
        self.assertIs(self.page.window.visible, False)
        asyncio.run(panel.tray_action('toggle'))
        self.assertIs(self.page.window.visible, True)
        panel.close_window = AsyncMock()
        asyncio.run(panel.tray_action('quit'))
        panel.close_window.assert_awaited_once()


if __name__ == '__main__':
    unittest.main()
