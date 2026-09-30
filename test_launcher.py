import asyncio
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import flet as ft
import app_launcher
import main as app
from macro.events import LEFT_DOWN, LEFT_UP, Macro, MacroEvent
from test_ui import PageStub, controls


class LifetimeTests(unittest.TestCase):
    def test_idle_only_after_a_window_connected_and_left(self):
        lifetime=app_launcher._Lifetime()
        self.assertEqual(lifetime.idle_for(),0.0)
        lifetime.opened()
        self.assertEqual(lifetime.idle_for(),0.0)
        lifetime.closed()
        with patch.object(app_launcher.time,'monotonic',return_value=lifetime._changed+30):
            self.assertGreater(lifetime.idle_for(),app_launcher.IDLE_EXIT_SECONDS)

    def test_reload_keeps_app_alive(self):
        lifetime=app_launcher._Lifetime()
        lifetime.opened()
        lifetime.opened()   # la finestra ricaricata si collega prima che la vecchia si stacchi
        lifetime.closed()
        with patch.object(app_launcher.time,'monotonic',return_value=lifetime._changed+30):
            self.assertEqual(lifetime.idle_for(),0.0)

    def test_track_keeps_app_disconnect_handler(self):
        lifetime=app_launcher._Lifetime()
        seen=[]
        def target(page):
            page.on_disconnect=lambda e: seen.append('cleanup')
        page=SimpleNamespace(on_disconnect=None)
        app_launcher._track(target,lifetime)(page)
        self.assertTrue(lifetime.seen())
        page.on_disconnect(None)
        self.assertEqual(seen,['cleanup'])
        with patch.object(app_launcher.time,'monotonic',return_value=lifetime._changed+30):
            self.assertGreater(lifetime.idle_for(),0)


class RunTests(unittest.TestCase):
    def test_windows_serves_locally_on_a_secret_path_without_cdn(self):
        with patch.object(app_launcher,'uses_browser_window',return_value=True), \
                patch.object(app_launcher.ft,'run') as run:
            app_launcher.run(lambda page: None)
        kwargs=run.call_args.kwargs
        self.assertEqual(kwargs['view'],ft.AppView.WEB_BROWSER)
        self.assertEqual(kwargs['host'],'127.0.0.1')
        self.assertGreaterEqual(len(kwargs['name']),16)
        self.assertTrue(kwargs['no_cdn'])

    def test_other_platforms_keep_native_window(self):
        target=lambda page: None
        with patch.object(app_launcher,'uses_browser_window',return_value=False), \
                patch.object(app_launcher.ft,'run') as run:
            app_launcher.run(target)
        run.assert_called_once_with(target)

    @unittest.skipUnless(sys.platform=='win32','Windows only')
    def test_app_window_uses_dedicated_profile(self):
        proc=MagicMock()
        proc.poll.return_value=0
        lifetime=app_launcher._Lifetime()
        lifetime.opened(); lifetime.closed()
        with patch.object(app_launcher,'find_app_browser',return_value=r'C:\Edge\msedge.exe'), \
                patch.object(app_launcher.subprocess,'Popen',return_value=proc) as popen, \
                patch.object(app_launcher.time,'sleep'), \
                patch.object(app_launcher.os,'_exit',side_effect=SystemExit) as exit_:
            with self.assertRaises(SystemExit):
                app_launcher._open_window('http://127.0.0.1:1/x',lifetime)
        args=popen.call_args.args[0]
        self.assertEqual(args[0],r'C:\Edge\msedge.exe')
        self.assertIn('--app=http://127.0.0.1:1/x',args)
        self.assertTrue(any(a.startswith('--user-data-dir=') for a in args))
        exit_.assert_called_once_with(0)


@unittest.skipUnless(sys.platform=='win32','Windows UI callbacks')
class NativeDialogTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/'macro.mmr'
        Macro('windows',[MacroEvent(0,LEFT_DOWN,x=10,y=20),
                         MacroEvent(.03,LEFT_UP,x=10,y=20)]).save(str(self.path))
        self.page=PageStub()
        self.page.web=True
        with patch('macro.windows_backend.GlobalHotkeys') as hotkeys:
            hotkeys.return_value.failed=[]
            app.main(self.page)
        self.items=list(controls(self.page))

    def click(self,icon):
        button=next(c for c in self.items if isinstance(c,ft.OutlinedButton) and c.icon==icon)
        asyncio.run(button.on_click(None))

    def status_values(self):
        return [c.value for c in self.items if isinstance(c,ft.Text)]

    def test_browser_window_uses_windows_dialogs_for_load_and_save(self):
        target=Path(self.temp.name)/'copia.mmr'
        with patch('macro.win_dialogs.ask_open_path',return_value=str(self.path)) as ask_open:
            self.click(ft.Icons.FOLDER_OPEN_ROUNDED)
        ask_open.assert_called_once_with('Carica macro')
        self.assertIn('Macro caricata',self.status_values())
        with patch('macro.win_dialogs.ask_save_path',return_value=str(target)) as ask_save:
            self.click(ft.Icons.SAVE_ROUNDED)
        ask_save.assert_called_once_with('Salva macro','macro.mmr')
        self.assertEqual(Macro.load(str(target)),Macro.load(str(self.path)))

    def test_cancelled_windows_dialog_changes_nothing(self):
        before=self.status_values()
        with patch('macro.win_dialogs.ask_open_path',return_value=None):
            self.click(ft.Icons.FOLDER_OPEN_ROUNDED)
        self.assertEqual(self.status_values(),before)


if __name__=='__main__':
    unittest.main()
