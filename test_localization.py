import asyncio
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import flet as ft
import main as app
from localization import localize_page, translate
from macro.events import LEFT_DOWN, LEFT_UP, Macro, MacroEvent
from test_ui import PageStub, controls


class LocalizationTests(unittest.TestCase):
    def page(self, language):
        page = PageStub()
        with patch.object(app, 'current_platform', return_value='linux'), \
                patch.object(app, 'list_mice', return_value=[('/dev/input/test', 'Test mouse')]):
            app.main(page, language=language)
        return page

    def texts(self, page):
        return [c.value for c in controls(page) if isinstance(c, ft.Text)]

    def test_initial_english_and_italian_preserve_defaults(self):
        for language, ready, repeat, summary, wait in [
                ('it', 'Pronto', 'N volte', 'Chiusura schede: OFF · Tempi: fissi',
                 'Confronta il pulsante prima di cliccare'),
                ('en', 'Ready', 'N times', 'Close tabs: OFF · Timing: fixed',
                 'Match the button before clicking')]:
            with self.subTest(language=language):
                page = self.page(language)
                items = list(controls(page))
                self.assertIn(ready, self.texts(page))
                self.assertIn(repeat, self.texts(page))
                self.assertIn(summary, self.texts(page))
                self.assertIn(wait, self.texts(page))
                fields = [c.value for c in items if isinstance(c, ft.TextField)]
                self.assertIn('150', fields)
                self.assertIn('', fields)
                self.assertEqual(next(c.value for c in items if isinstance(c, ft.Slider)), 1.0)
                self.assertEqual((page.window.width, page.window.height), (560, 720))

    def test_english_settings_help_and_dynamic_errors(self):
        page = self.page('en')
        items = list(controls(page))
        settings = next(c for c in items if isinstance(c, ft.OutlinedButton) and c.icon == ft.Icons.SETTINGS_ROUNDED)
        settings.on_click(None)
        self.assertEqual(page.dialogs[-1].title.value, 'Settings')
        self.assertIn('Vary timing each cycle', self.texts(page))
        page.pop_dialog()
        help_button = next(c for c in items if isinstance(c, ft.IconButton) and c.icon == ft.Icons.HELP_OUTLINE_ROUNDED)
        help_button.on_click(None)
        self.assertEqual(page.dialogs[-1].title.value, 'How to use')
        self.assertEqual(page.dialogs[-1].actions[0].content, 'Got it')
        page.pop_dialog()
        play = next(c for c in items if isinstance(c, ft.Container) and isinstance(c.content, ft.Row)
                    and any(isinstance(t, ft.Text) and t.value == 'PLAY  (F10)' for t in c.content.controls))
        play.on_click(None)
        self.assertIn('No macro', self.texts(page))

    def test_english_native_picker_titles_and_roundtrip(self):
        page = self.page('en')
        items = list(controls(page))
        load = next(c for c in items if isinstance(c, ft.OutlinedButton) and c.icon == ft.Icons.FOLDER_OPEN_ROUNDED)
        save = next(c for c in items if isinstance(c, ft.OutlinedButton) and c.icon == ft.Icons.SAVE_ROUNDED)
        native_page = SimpleNamespace(web=False, platform=SimpleNamespace(is_mobile=lambda: False))
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'registrazione.mmr'
            target = Path(folder) / 'recording.mmr'
            macro = Macro('linux', [MacroEvent(0, LEFT_DOWN), MacroEvent(.05, LEFT_UP)])
            macro.save(str(source))
            with patch.object(ft.FilePicker, 'page', new_callable=PropertyMock, return_value=native_page), \
                    patch.object(ft.FilePicker, '_invoke_method', new_callable=AsyncMock,
                                 return_value=[{'id': 1, 'name': source.name, 'path': str(source), 'size': source.stat().st_size}]) as invoke:
                asyncio.run(load.on_click(None))
                self.assertEqual(invoke.call_args.args[1]['dialog_title'], 'Load macro')
            self.assertFalse(save.disabled)
            self.assertIn('Macro loaded', self.texts(page))
            with patch.object(ft.FilePicker, 'page', new_callable=PropertyMock, return_value=native_page), \
                    patch.object(ft.FilePicker, '_invoke_method', new_callable=AsyncMock, return_value=str(target)) as invoke:
                asyncio.run(save.on_click(None))
                self.assertEqual(invoke.call_args.args[1]['dialog_title'], 'Save macro')
            self.assertEqual(Macro.load(str(target)), macro)

    def test_only_presentation_is_translated(self):
        page = PageStub()
        localize_page(page, 'en')
        user_value = ft.TextField(value='Pronto', hint_text='Pronto')
        label = ft.Text('Pronto')
        page.add(ft.Column([label, user_value]))
        self.assertEqual(label.value, 'Ready')
        self.assertEqual(user_value.value, 'Pronto')
        self.assertEqual(user_value.hint_text, 'Ready')
        label.value = 'Registrazione completata'
        page.update()
        self.assertEqual(label.value, 'Recording complete')

    def test_headless_diagnostics_report(self):
        import json
        from macro.diagnostics import self_test
        with tempfile.TemporaryDirectory() as folder:
            for language in ('it', 'en'):
                target = Path(folder) / f'{language}.json'
                self.assertEqual(self_test(str(target), language), 0)
                report = json.loads(target.read_text())
                self.assertTrue(report['ok'])
                self.assertEqual(report['language'], language)
                self.assertTrue(all(report['checks'].values()))

    def test_device_refresh_clears_stale_selection(self):
        page = self.page('en')
        items = list(controls(page))
        refresh = next(c for c in items if isinstance(c, ft.IconButton) and c.icon == ft.Icons.REFRESH_ROUNDED)
        with patch.object(app, 'list_mice', return_value=[]):
            refresh.on_click(None)
        record = next(c for c in items if isinstance(c, ft.Container) and isinstance(c.content, ft.Row)
                      and any(isinstance(t, ft.Text) and t.value == 'RECORD  (F9)' for t in c.content.controls))
        with patch.object(app, 'make_recorder') as recorder:
            record.on_click(None)
            recorder.assert_not_called()
        self.assertIn('No mouse selected', self.texts(page))


if __name__ == '__main__':
    unittest.main()
