"""Bambola skin data: one declarative JSON shared by the Linux and Windows panels."""
import ast
import unittest
from pathlib import Path

from macro import panel_model

ROOT = Path(__file__).resolve().parent
STATES = ('pronto', 'registrazione', 'riproduzione', 'errore')


class BambolaSkinTests(unittest.TestCase):
    def setUp(self):
        self.data = panel_model.load_skin('bambola')

    def test_linux_palette_comes_from_the_json_and_is_complete(self):
        self.assertEqual(panel_model.SKINS['bambola'], self.data['palette']['linux'])
        self.assertEqual(set(panel_model.SKINS['bambola']), set(panel_model.SKINS['unicorno']))
        self.assertEqual(panel_model.DEFAULT_SKIN, 'bambola')

    def test_windows_palette_has_the_same_keys_as_the_other_skins(self):
        tree = ast.parse((ROOT / 'windows_visual.py').read_text('utf-8'))
        keys = {}
        for node in tree.body:
            if isinstance(node, ast.Assign) and getattr(node.targets[0], 'id', '') in ('UNICORN', 'PALIO'):
                keys[node.targets[0].id] = {k.arg for k in node.value.keywords}
        for name, expected in keys.items():
            self.assertEqual(set(self.data['palette']['windows']), expected, name)

    def test_every_state_has_clip_images_and_in_range_crops(self):
        width, height = self.data['images']['frame']
        self.assertEqual(set(self.data['states']), set(STATES))
        for state in STATES:
            for kind in ('animated', 'still'):
                self.assertTrue((ROOT / 'assets' / self.data['images'][kind].format(state=state)).is_file())
            x, y, w, h = self.data['windows']['regions'][state]
            self.assertTrue(0 <= x and 0 <= y and x + w <= width and y + h <= height, state)
        x, y, w, h = self.data['linux']['bar_head']['crop']
        self.assertTrue(x + w <= width and y + h <= height)

    def test_micro_bar_is_300_by_72_on_both_platforms(self):
        self.assertEqual(self.data['linux']['active_size'], [300, 72])
        self.assertEqual(self.data['windows']['active_size'], [300, 72])

    def test_windows_cover_layout_values_are_sane(self):
        width, height = self.data['images']['frame']
        x, y, w, h = self.data['windows']['bar_head']
        self.assertTrue(x + w <= width and y + h <= height)
        self.assertTrue(0 < self.data['windows']['hero_extra'] <= 80)


if __name__ == '__main__':
    unittest.main()
