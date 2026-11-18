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

    def test_window_is_kept_inside_the_work_area(self):
        work = (0, 0, 1024, 728)
        self.assertEqual(ws.fit_to_work_area(200, 150, 725, 700, work), (200, 28, 725, 700))  # moved up
        self.assertEqual(ws.fit_to_work_area(900, 10, 725, 900, work), (299, 0, 725, 728))  # moved left, shrunk
        self.assertEqual(ws.fit_to_work_area(160, 120, 580, 560, (0, 0, 1920, 1040)), (160, 120, 580, 560))

    def test_texts(self):
        info = SimpleNamespace(id='x', name='Viola', kind='theme', version='1.0', author='realhcok', sha256='ab' * 32,
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

    def open_window(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        panel = SimpleNamespace(settings={'close_to_tray': True}, session=SimpleNamespace(message='ok'),
                                dialog_open=False, write_settings=lambda: None)
        window = ws.SettingsWindow(panel, Path(temp.name) / 'mods')
        window.show()
        self.addCleanup(lambda: window.hwnd and ws.U.DestroyWindow(window.hwnd))
        return panel, window

    def control_size(self, handle):
        rect = wintypes.RECT()
        ctypes.windll.user32.GetWindowRect(handle, ctypes.byref(rect))
        return rect.right - rect.left, rect.bottom - rect.top

    def test_moving_to_a_monitor_with_another_scale_rescales_the_window(self):
        panel, window = self.open_window()
        old_font = window.gdi['font']
        target = wintypes.RECT(100, 50, 100 + 870, 50 + 840)  # what Windows suggests for 150%
        ws.U.SendMessageW(window.hwnd, 0x2E0, 144 | 144 << 16, ctypes.addressof(target))  # WM_DPICHANGED
        self.assertEqual(window.scale, 1.5)
        self.assertEqual(self.control_size(window.controls[ws.ID_CLOSE]), (180, 60))
        self.assertNotEqual(window.gdi['font'], old_font)
        self.assertEqual(panel.session.message, 'ok')
        ws.U.SendMessageW(window.hwnd, 0x2E0, 96 | 96 << 16, ctypes.addressof(wintypes.RECT(100, 50, 680, 610)))
        self.assertEqual(self.control_size(window.controls[ws.ID_CLOSE]), (120, 40))

    def test_switches_follow_changes_made_from_the_tray_menu(self):
        panel, window = self.open_window()
        panel.settings['close_to_tray'] = False  # «Chiudi nel tray» unchecked from the tray menu
        self.assertFalse(window.toggles[ws.ID_TRAY])
        window.command(ws.ID_TRAY)
        self.assertIs(panel.settings['close_to_tray'], True)  # turned on, not written back as off


if __name__ == '__main__':
    unittest.main()
