"""Rendering policy tests; monitor and desktop acceptance are separate."""
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

if sys.platform == 'win32':
    import windows_visual as visual


@unittest.skipUnless(sys.platform == 'win32', 'Windows GDI+')
class VisualTests(unittest.TestCase):
    def test_body_and_brand_use_separate_font_families(self):
        theme = visual.Theme.__new__(visual.Theme)
        theme.family, theme.body_family, theme.fonts = 1, 2, {}
        with patch.object(visual, 'ptrcall', return_value=3) as call:
            theme.font(14, False)
            call.assert_called_with(visual.D.GdipCreateFont, 2, 14, 0, 2)
            theme.font(22, True, display=True)
            call.assert_called_with(visual.D.GdipCreateFont, 1, 22, 1, 2)

    def test_font_cache_does_not_mix_body_and_brand(self):
        theme = visual.Theme.__new__(visual.Theme)
        theme.family, theme.body_family, theme.fonts = 1, 2, {}
        with patch.object(visual, 'ptrcall', side_effect=[3, 4]) as call:
            self.assertEqual(theme.font(14, True), 3)
            self.assertEqual(theme.font(14, True), 3)
            self.assertEqual(theme.font(14, True, display=True), 4)
            self.assertEqual(call.call_count, 2)

    def test_pixel_units_and_dpi_scale_are_applied_once(self):
        for scale in (1, 1.25, 1.5, 2):
            with self.subTest(scale=scale), patch.object(visual, 'G'), \
                 patch.object(visual, 'D') as d, patch.object(visual, 'ptrcall', return_value=7):
                visual.Canvas(None, None, round(288*scale), round(64*scale), scale)
                d.GdipSetPageUnit.assert_called_once_with(7, 2)
                d.GdipScaleWorldTransform.assert_called_once_with(7, scale, scale, 0)
                d.GdipSetTextRenderingHint.assert_called_once_with(7, 5)

    def test_layered_bar_can_use_grayscale_antialiasing(self):
        with patch.object(visual, 'G'), patch.object(visual, 'D') as d, \
             patch.object(visual, 'ptrcall', return_value=7):
            visual.Canvas(None, None, 288, 64, 1, text_hint=4)
            d.GdipSetTextRenderingHint.assert_called_once_with(7, 4)

    def test_text_selects_body_font_unless_brand_is_explicit(self):
        canvas = visual.Canvas.__new__(visual.Canvas)
        canvas.g = 7
        canvas.theme = SimpleNamespace(font=MagicMock(return_value=9))
        canvas.brush = MagicMock(return_value=8)
        with patch.object(visual, 'D'), patch.object(visual, 'ptrcall', return_value=10):
            canvas.text('Stop', 0, 0, 72, 40, size=15, bold=True)
            canvas.theme.font.assert_called_with(15, True, False)
            canvas.text('Mouse Macro', 0, 0, 250, 26, size=22, bold=True, display=True)
            canvas.theme.font.assert_called_with(22, True, True)

    def test_cleanup_releases_both_font_families(self):
        theme = visual.Theme.__new__(visual.Theme)
        theme.fonts, theme.images = {}, {}
        theme.family, theme.body_family = 1, 2
        theme.collection = visual.P(3)
        theme.token = 4
        with patch.object(visual, 'D') as d:
            theme.close()
            self.assertEqual(d.GdipDeleteFontFamily.call_args_list,
                             [unittest.mock.call(2), unittest.mock.call(1)])
