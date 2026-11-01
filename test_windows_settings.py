"""Finestra Impostazioni: colori della skin e prova reale di creazione/disegno su Windows."""
import ctypes
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

if sys.platform == 'win32':
    import windows_settings as ws
    from ctypes import wintypes
    from macro import mods
    from test_mods import manifest, png
    import json
    import zipfile


@unittest.skipUnless(sys.platform == 'win32', 'Windows')
class SettingsWindowTests(unittest.TestCase):
    def test_color_helpers(self):
        self.assertEqual(ws.colorref('#1A1024'), 0x24101A)  # COLORREF è BGR
        self.assertTrue(ws.is_dark('#1A1024'))
        self.assertFalse(ws.is_dark('#FFF6DF'))

    def test_texts(self):
        info = SimpleNamespace(id='x', name='Viola', kind='theme', version='1.0', author='Luca', sha256='ab' * 32,
                               summary=lambda: ['Colori', 'Nessun codice'])
        self.assertIn('in uso', ws.list_label(info, 'mod:x'))
        self.assertNotIn('in uso', ws.list_label(info, 'bambola'))
        self.assertIn('abababababababab…', ws.confirm_text(info))

    def test_window_opens_draws_and_closes_without_errors(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        folder = Path(temp.name)
        package = folder / 'p.mmmod'
        files = {'mod.json': manifest(), 'theme.json': json.dumps({'colors': {'background': '#112233'}}).encode()}
        files.update({f'horses/{s}.png': png() for s in mods.STATES})
        with zipfile.ZipFile(package, 'w') as z:
            for name, data in files.items():
                z.writestr(name, data)
        mods.install(package, folder / 'mods')
        panel = SimpleNamespace(settings={'close_to_tray': True}, session=SimpleNamespace(message='ok'),
                                dialog_open=False, write_settings=lambda: None)
        window = ws.SettingsWindow(panel, folder / 'mods')
        window.show()
        self.addCleanup(lambda: window.hwnd and ws.U.DestroyWindow(window.hwnd))
        self.assertTrue(window.hwnd)
        self.assertEqual([i.id for i in window.items], ['viola-test'])
        self.assertEqual(window.toggles, {ws.ID_TRAY: True, ws.ID_UPDATES: True})
        # Pump the messages so WM_PAINT/WM_DRAWITEM/WM_CTLCOLOR* really run.
        for hwnd in list(window.controls.values()) + [window.hwnd]:
            ws.U.UpdateWindow(hwnd)
        msg = wintypes.MSG()
        while ctypes.windll.user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, 1):
            ctypes.windll.user32.DispatchMessageW(ctypes.byref(msg))
        self.assertEqual(panel.session.message, 'ok')  # un errore nel disegno finirebbe qui
        window.command(ws.ID_TRAY)  # clic sull'interruttore
        self.assertIs(panel.settings['close_to_tray'], False)
        ws.U.DestroyWindow(window.hwnd)
        self.assertIsNone(window.hwnd)
        self.assertEqual(window.gdi, {})


if __name__ == '__main__':
    unittest.main()
