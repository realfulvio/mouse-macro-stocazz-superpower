import unittest
from pathlib import Path

from macro import win_tray as t

SOURCE = (Path(__file__).resolve().parent / 'windows_main.py').read_text(encoding='utf-8')


class TrayLogicTests(unittest.TestCase):
    def test_menu_labels_and_separators(self):
        items = t.menu_items(visible=True, close_to_tray=False)
        self.assertEqual(items[0][1], 'Nascondi pannello')
        self.assertEqual(t.menu_items(False, False)[0][1], 'Mostra pannello')
        ids = [i for i, _, _ in items if i]
        self.assertEqual(ids, [t.SHOW, t.RECORD, t.PLAY, t.STOP_ALL, t.CLOSE_TO_TRAY, t.QUIT])
        self.assertEqual(len(set(ids)), len(ids))
        self.assertTrue(all(f == t.MF_SEPARATOR for i, _, f in items if i is None))

    def test_close_to_tray_is_checked_only_when_on(self):
        flag = lambda on: [f for i, _, f in t.menu_items(True, on) if i == t.CLOSE_TO_TRAY][0]
        self.assertEqual(flag(True), t.MF_CHECKED)
        self.assertEqual(flag(False), t.MF_STRING)

    def test_clicks(self):
        self.assertEqual(t.click_action(t.WM_LBUTTONDBLCLK), 'toggle')
        self.assertEqual(t.click_action(t.WM_RBUTTONUP), 'menu')
        self.assertIsNone(t.click_action(0x0200))  # solo movimento
        self.assertEqual(t.click_action(0x1234_0000 | t.WM_RBUTTONUP), 'menu')  # parte alta ignorata

    def test_x_hides_only_when_safe(self):
        self.assertTrue(t.should_hide_on_close(True, False, True))
        self.assertFalse(t.should_hide_on_close(False, False, True))  # comportamento di prima
        self.assertFalse(t.should_hide_on_close(True, True, True))    # Esci / aggiornamento
        self.assertFalse(t.should_hide_on_close(True, False, False))  # icona non creata: la X chiude

    def test_panel_is_wired_to_the_tray(self):
        self.assertIn('win_tray.Tray(', SOURCE)
        self.assertIn('self.tray.remove()', SOURCE)
        self.assertIn('self.quitting = True', SOURCE)
        self.assertEqual(SOURCE.count('self.quitting = True'), 2)  # Esci e riavvio dopo l'aggiornamento


if __name__ == '__main__':
    unittest.main()
