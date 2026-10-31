"""Linux Flet panel: preferences, compact bar, updates, diagnostics and mouse model."""
import asyncio
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from macro import panel_model
from macro.events import LEFT_DOWN, LEFT_UP, MOVE_REL, MacroEvent
from macro.session import State

if sys.platform == 'linux':
    import flet as ft
    import linux_main


class PageStub:
    def __init__(self):
        self.window = SimpleNamespace(destroy=AsyncMock())
        self.services = []
        self.controls = []
        self.dialogs = []
        self.tasks = []

    def add(self, *controls):
        self.controls.extend(controls)

    def update(self, *controls):
        pass

    def show_dialog(self, dialog):
        self.dialogs.append(dialog)

    def pop_dialog(self):
        self.dialogs.pop()

    def run_task(self, handler, *args):
        self.tasks.append((handler, args))


def walk(control):
    pending, seen = [control], set()
    while pending:
        item = pending.pop(0)
        if id(item) in seen:
            continue
        seen.add(id(item))
        yield item
        content = getattr(item, 'content', None)
        if content is not None and not isinstance(content, str):
            pending.append(content)
        pending.extend(getattr(item, 'controls', None) or [])
        pending.extend(getattr(item, 'actions', None) or [])


def texts(control):
    return [c.value for c in walk(control) if isinstance(c, ft.Text)]


@unittest.skipUnless(sys.platform == 'linux', 'Linux Flet panel')
class LinuxPanelTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.prefs = self.folder / 'linux-panel.json'

    def panel(self, settings=None, language='it'):
        if settings is not None:
            self.prefs.write_text(json.dumps(settings))
        self.page = PageStub()
        return linux_main.LinuxPanel(self.page, language, preferences=self.prefs)

    def saved(self):
        return json.loads(self.prefs.read_text())

    def macro(self, panel):
        panel.session.macro.events = [MacroEvent(0, MOVE_REL, dx=4, dy=2), MacroEvent(.1, LEFT_DOWN),
                                      MacroEvent(.2, LEFT_UP)]

    # Preferences -------------------------------------------------------
    def test_window_geometry_skin_and_update_preference_are_restored(self):
        panel = self.panel({'window': {'width': 500, 'height': 700, 'left': 30, 'top': 40},
                            'skin': 'palio', 'check_updates': False, 'device': '/dev/input/event3'})
        window = self.page.window
        self.assertEqual((window.width, window.height, window.left, window.top), (500, 700, 30, 40))
        self.assertEqual(panel.skin, 'palio')
        self.assertEqual(self.page.bgcolor, panel_model.SKINS['palio']['background'])
        self.assertFalse(panel.settings['check_updates'])
        self.assertEqual(panel.mouse.value, '/dev/input/event3')

    def test_defaults_and_invalid_geometry_fall_back_safely(self):
        self.panel({'window': {'width': 10, 'height': 'big', 'left': float('nan')}, 'skin': 'x'})
        window = self.page.window
        self.assertEqual((window.width, window.height), linux_main.NORMAL_SIZE)
        self.assertFalse(hasattr(window, 'left'))

    def test_moved_and_resized_events_persist_normal_geometry(self):
        panel = self.panel()
        self.page.window.width, self.page.window.height = 480, 720
        self.page.window.left, self.page.window.top = 12, 34
        asyncio.run(panel.window_event(SimpleNamespace(type=ft.WindowEventType.MOVED)))
        self.assertEqual(self.saved()['window'], {'width': 480, 'height': 720, 'left': 12, 'top': 34})
        asyncio.run(panel.window_event(SimpleNamespace(type=ft.WindowEventType.CLOSE)))
        self.page.window.destroy.assert_awaited_once()
        self.assertTrue(panel.closed)

    def test_compact_bar_geometry_is_never_saved(self):
        panel = self.panel()
        self.page.window.left, self.page.window.top = 5, 6
        panel.session.state = State.RECORDING
        panel.session.recorder = SimpleNamespace(current_event_count=3)
        panel.render()
        self.page.window.left = 900
        asyncio.run(panel.window_event(SimpleNamespace(type=ft.WindowEventType.RESIZED)))
        self.assertFalse(self.prefs.exists())
        panel.remember_window()
        self.assertEqual(panel.settings['window'].get('height'), linux_main.NORMAL_SIZE[1])

    def test_skin_and_startup_check_switches_write_preferences(self):
        panel = self.panel()
        panel.skin_choice.value = 'palio'
        panel.skin_changed()
        self.assertEqual(self.saved()['skin'], 'palio')
        panel.startup_check_changed(SimpleNamespace(control=SimpleNamespace(value=False)))
        self.assertFalse(self.saved()['check_updates'])
        self.assertIn('disattivato', panel.session.message)
        self.assertFalse(panel_model.read_settings(self.prefs)['check_updates'])

    # Compact active bar -------------------------------------------------
    def test_recording_and_playback_show_compact_semi_transparent_bar(self):
        panel = self.panel()
        self.macro(panel)
        panel.session.state = State.RECORDING
        panel.session.recorder = SimpleNamespace(current_event_count=42)
        panel.render()
        window = self.page.window
        self.assertTrue(panel.activity_view.visible)
        self.assertFalse(panel.normal_view.visible or panel.footer.visible or panel.shortcut_hint.visible)
        self.assertEqual((window.width, window.height), linux_main.ACTIVE_SIZE)
        self.assertEqual(window.opacity, linux_main.ACTIVE_OPACITY)
        self.assertTrue(panel.activity_count.value.startswith('42 eventi · 00:0'))
        self.assertEqual(panel.activity_hint.value, 'F9 stop')
        self.assertGreaterEqual(panel.stop.height, 64)
        panel.session.recorder = None
        panel.session.state = State.PLAYING
        panel.last_options = panel_model.playback_options('20')
        panel.session.completed = 7
        panel.render()
        self.assertTrue(panel.activity_count.value.startswith('7/20 giri · '))
        self.assertTrue(panel.progress.visible)
        panel.session.state = State.READY
        panel.render()
        self.assertEqual((window.width, window.height, window.opacity), (*linux_main.NORMAL_SIZE, 1.0))
        self.assertTrue(panel.normal_view.visible and panel.footer.visible)

    def test_compact_bar_counters_for_unlimited_and_duration_modes(self):
        panel = self.panel(language='en')
        panel.session.completed = 3
        panel.mode.value = 'infinite'
        panel.last_options = panel_model.playback_options(mode='infinite')
        self.assertEqual(panel.activity_detail(State.PLAYING, 0, 65), '3 cycles · 01:05')
        panel.mode.value = 'duration'
        panel.last_options = panel_model.playback_options(mode='duration', minutes='2')
        self.assertEqual(panel.activity_detail(State.PLAYING, 0, 65), '3 cycles · 01:05 / 02:00')

    def test_stop_button_stops_playback(self):
        panel = self.panel()
        with patch.object(panel.session, 'request_stop') as stop:
            panel.session.state = State.PLAYING
            asyncio.run(panel.stop_clicked())
            stop.assert_called()

    # Human-like movement -------------------------------------------------
    def test_human_movement_switch_reaches_playback_options(self):
        panel = self.panel()
        self.macro(panel)
        panel.human.value = True
        panel.human_changed()
        self.assertIn('Movimento umano attivo', panel.session.message)
        with patch.object(panel.session, 'toggle_play') as play:
            asyncio.run(panel.dispatch('play'))
        options = play.call_args.args[0]
        self.assertTrue(options.humanize)
        self.assertEqual(options.timing_variation_seconds, 0.0)
        self.assertIs(panel.last_options, options)

    # Mouse model ---------------------------------------------------------
    def test_mouse_model_is_visible_with_and_without_device_access(self):
        panel = self.panel()
        with patch.object(linux_main, 'list_mice', return_value=[('/dev/input/event5', 'Logitech G304'),
                                                                 ('/dev/input/event6', 'Other Mouse')]), \
             patch.object(linux_main, 'mouse_models', return_value=['Logitech G304', 'Other Mouse']):
            asyncio.run(panel.refresh_devices())
        self.assertEqual(panel.mouse_model.value, 'Mouse: Logitech G304')
        panel.mouse.value = '/dev/input/event6'
        panel.render()
        self.assertEqual(panel.mouse_model.value, 'Mouse: Other Mouse')
        with patch.object(linux_main, 'list_mice', return_value=[]), \
             patch.object(linux_main, 'mouse_models', return_value=['Logitech G304']):
            asyncio.run(panel.refresh_devices())
        self.assertEqual(panel.mouse_model.value, 'Mouse: Logitech G304 · senza permessi')
        self.assertIn('Permessi mouse insufficienti', panel.device_hint.value)
        english = self.panel(language='en')
        english.models = ['Logitech G304']
        english.render()
        self.assertEqual(english.mouse_model.value, 'Mouse: Logitech G304 · no access')
        english.models = []
        english.render()
        self.assertEqual(english.mouse_model.value, 'Mouse: model unavailable')

    # Access without a terminal -------------------------------------------
    def refresh(self, panel, mice, access, hotkeys_failed):
        hotkeys = MagicMock(failed=['F9'] if hotkeys_failed else [])
        with patch.object(linux_main, 'GlobalHotkeys', return_value=hotkeys) as factory, \
             patch.object(linux_main, 'list_mice', return_value=mice), \
             patch.object(linux_main, 'mouse_models', return_value=[]), \
             patch.object(linux_main.linux_setup, 'input_access', return_value=access):
            asyncio.run(panel.refresh_devices())
        return factory

    def test_access_banner_appears_until_mouse_keyboard_and_uinput_work(self):
        panel = self.panel()
        self.refresh(panel, [], {'events': False, 'uinput': False, 'rule': False}, True)
        self.assertTrue(panel.access_banner.visible)
        self.assertIn('Scorciatoie globali non disponibili', panel.shortcut_hint.value)
        # After access is granted the same refresh restarts the global shortcuts.
        factory = self.refresh(panel, [('/dev/input/event5', 'Mouse')],
                               {'events': True, 'uinput': True, 'rule': True}, False)
        factory.assert_called_once()
        self.assertFalse(panel.access_banner.visible)
        self.assertEqual(panel.shortcut_hint.value, 'F9 · F10 · Ctrl+Alt+F11')
        # Working shortcuts are not restarted on later refreshes.
        factory = self.refresh(panel, [('/dev/input/event5', 'Mouse')],
                               {'events': True, 'uinput': True, 'rule': True}, False)
        factory.assert_not_called()

    def test_grant_access_refreshes_devices_or_reports_cancel(self):
        panel = self.panel()
        panel.refresh_devices = AsyncMock()
        with patch.object(linux_main.linux_setup, 'grant_access', return_value=(False, 'annullato')):
            asyncio.run(panel.grant_access())
        self.assertEqual(panel.session.message, 'Configurazione annullata.')
        with patch.object(linux_main.linux_setup, 'grant_access', return_value=(False, 'senza_agente')):
            asyncio.run(panel.grant_access())
        self.assertEqual(panel.session.message, linux_main.ACCESS_NO_AGENT)
        panel.refresh_devices.assert_not_called()
        panel.devices, panel.access = [('/dev/input/event5', 'Mouse')], {'events': True, 'uinput': True}
        with patch.object(linux_main.linux_setup, 'grant_access', return_value=(True, '')), \
             patch.object(linux_main.asyncio, 'sleep', AsyncMock()):
            asyncio.run(panel.grant_access())
        panel.refresh_devices.assert_awaited_once()
        self.assertEqual(panel.session.message, 'Accesso al mouse concesso.')
        self.assertFalse(panel.dialog_open)

    # Updates -------------------------------------------------------------
    def start(self, panel):
        hotkeys = MagicMock(failed=[])
        with patch.object(linux_main, 'GlobalHotkeys', return_value=hotkeys), \
             patch.object(linux_main, 'list_mice', return_value=[]), \
             patch.object(linux_main, 'mouse_models', return_value=[]):
            asyncio.run(panel.start())
        return [handler for handler, args in self.page.tasks]

    def test_startup_check_runs_only_when_enabled(self):
        panel = self.panel()
        self.assertIn(panel.check_updates, self.start(panel))
        panel = self.panel({'check_updates': False})
        self.assertNotIn(panel.check_updates, self.start(panel))

    def test_check_sets_status_dot_and_message(self):
        panel = self.panel()
        release = {'version': '1.0.1', 'tag': 'linux-v1.0.1', 'assets': {}}
        with patch.object(linux_main.linux_updater, 'check', return_value=('available', release)) as check:
            asyncio.run(panel.check_updates())
        check.assert_called_once_with(panel_model.LINUX_VERSION)
        self.assertEqual(panel.update['state'], 'available')
        self.assertEqual(panel.header_dot.bgcolor, panel.colors['warning'])
        self.assertIn('1.0.1', panel.session.message)
        with patch.object(linux_main.linux_updater, 'check', return_value=('current', release)):
            asyncio.run(panel.check_updates(manual=True))
        self.assertEqual(panel.header_dot.bgcolor, panel.colors['ready'])
        self.assertIn('Sei aggiornato', panel.session.message)

    def test_failed_startup_check_is_silent_and_manual_failure_is_reported(self):
        panel = self.panel()
        error = linux_main.UpdateError('Non riesco a controllare gli aggiornamenti.')
        with patch.object(linux_main.linux_updater, 'check', side_effect=error):
            asyncio.run(panel.check_updates())
            self.assertEqual(panel.update['state'], 'unknown')
            self.assertEqual(panel.session.message, 'Registra i gesti del mouse.')
            self.assertEqual(panel.header_dot.bgcolor, panel.colors['border'])
            asyncio.run(panel.check_updates(manual=True))
        self.assertEqual(panel.session.message, 'Non riesco a controllare gli aggiornamenti.')

    def test_update_dialog_offers_install_only_when_available(self):
        panel = self.panel()
        panel.update_menu()
        dialog = self.page.dialogs.pop()
        install = next(c for c in walk(dialog) if isinstance(c, ft.Button) and c.icon == ft.Icons.DOWNLOAD)
        self.assertTrue(install.disabled)
        panel.update = {'state': 'available', 'latest': '9.0.1', 'release': {'version': '9.0.1'}}
        panel.update_menu()
        dialog = self.page.dialogs.pop()
        install = next(c for c in walk(dialog) if isinstance(c, ft.Button) and c.icon == ft.Icons.DOWNLOAD)
        self.assertFalse(install.disabled)
        self.assertIn(f'Disponibile la versione 9.0.1 (hai la {panel_model.LINUX_VERSION})', texts(dialog))
        panel.session.state = State.PLAYING
        panel.update_menu()
        self.assertEqual(self.page.dialogs, [])

    def test_install_verifies_then_relaunches_new_binary_and_closes(self):
        panel = self.panel()
        release = {'version': '1.0.1', 'assets': {}}
        panel.update = {'state': 'available', 'latest': '1.0.1', 'release': release}
        target = self.folder / 'MouseMacroStocazzSuperpower-Linux-v1.0.1'
        with patch.object(linux_main.linux_updater, 'install', return_value=target) as install, \
             patch.object(linux_main.subprocess, 'Popen') as popen:
            asyncio.run(panel.install_update())
        self.assertIs(install.call_args.args[0], release)
        command = popen.call_args.args[0]
        self.assertEqual(command[0], str(target / 'MouseMacroStocazzSuperpower-Linux-IT'))
        self.assertEqual(command[1], '--wait-for-exit')
        self.page.window.destroy.assert_awaited_once()

    def test_portable_appimage_updates_itself_instead_of_installing(self):
        panel = self.panel()
        name = linux_main.linux_updater.APPIMAGE.format('1.0.1')
        release = {'version': '1.0.1', 'assets': {name: 'https://x/a'}}
        panel.update = {'state': 'available', 'latest': '1.0.1', 'release': release}
        current = self.folder / 'old.AppImage'
        new = self.folder / name
        with patch.dict(linux_main.os.environ, {'APPIMAGE': str(current)}), \
             patch.object(linux_main.linux_updater, 'install_appimage', return_value=new) as portable, \
             patch.object(linux_main.linux_updater, 'install') as install, \
             patch.object(linux_main.subprocess, 'Popen') as popen:
            asyncio.run(panel.install_update())
        portable.assert_called_once_with(release, str(current))
        install.assert_not_called()
        self.assertEqual(popen.call_args.args[0][:2], [str(new), '--wait-for-exit'])

    def test_flatpak_never_installs_updates_itself(self):
        panel = self.panel()
        panel.update = {'state': 'available', 'latest': '1.0.1', 'release': {'version': '1.0.1', 'assets': {}}}
        with patch.dict(linux_main.os.environ, {'FLATPAK_ID': 'io.github.realfulvio.MouseMacroStocazzSuperpower'}):
            panel.update_menu()
            dialog = self.page.dialogs.pop()
            install = next(c for c in walk(dialog) if isinstance(c, ft.Button) and c.icon == ft.Icons.DOWNLOAD)
            self.assertTrue(install.disabled)
            self.assertIn('Flatpak', ' '.join(texts(install)))
            with patch.object(linux_main.linux_updater, 'install') as install_call, \
                 patch.object(linux_main.linux_updater, 'install_appimage') as portable:
                asyncio.run(panel.install_update())
        install_call.assert_not_called()
        portable.assert_not_called()

    def test_failed_install_keeps_panel_open_with_error(self):
        panel = self.panel()
        panel.update = {'state': 'available', 'latest': '9.0.1', 'release': {'version': '9.0.1'}}
        error = linux_main.UpdateError('SHA-256 diverso dall’atteso: download scartato.')
        with patch.object(linux_main.linux_updater, 'install', side_effect=error), \
             patch.object(linux_main.subprocess, 'Popen') as popen:
            asyncio.run(panel.install_update())
        popen.assert_not_called()
        self.assertEqual(panel.session.state, State.ERROR)
        self.assertIn('SHA-256', panel.session.message)
        self.assertFalse(panel.dialog_open)

    # Diagnostics ---------------------------------------------------------
    def test_finished_playback_writes_last_replay_trace_once(self):
        panel = self.panel()
        panel.last_options = panel_model.playback_options('3', human=True)
        panel.session.last_trace = [{'type': 'playback_start'}, {'type': 'playback_end', 'outcome': 'done'}]
        panel.render()
        trace = json.loads((self.folder / 'ultimo-replay.json').read_text())
        self.assertEqual((trace['version'], trace['platform'], trace['outcome']), (panel_model.LINUX_VERSION, 'linux', 'pronto'))
        self.assertEqual(trace['options']['mode'], 'repeat_count')
        self.assertTrue(trace['options']['humanize'])
        self.assertEqual(len(trace['records']), 2)
        (self.folder / 'ultimo-replay.json').unlink()
        panel.render()
        self.assertFalse((self.folder / 'ultimo-replay.json').exists())

    def test_unexpected_error_is_logged_to_errore_log(self):
        panel = self.panel()
        with patch.object(panel.session, 'toggle_record', side_effect=RuntimeError('boom')):
            asyncio.run(panel.dispatch('record'))
        self.assertEqual(panel.session.state, State.ERROR)
        log = (self.folder / 'errore.log').read_text()
        self.assertIn('RuntimeError: boom', log)

    def test_self_test_argument_and_wait_for_exit(self):
        with patch('macro.diagnostics.linux_self_test', return_value=0) as self_test:
            with self.assertRaises(SystemExit) as stop:
                linux_main.run('en', ['--self-test', 'report.json'])
        self.assertEqual(stop.exception.code, 0)
        self_test.assert_called_once_with('report.json', 'en')
        self.assertTrue(linux_main.wait_for_exit(2**22 + 12345, timeout=1))

    def test_no_graphical_session_stops_before_flet(self):
        with patch.dict(linux_main.os.environ, {'DISPLAY': '', 'WAYLAND_DISPLAY': ''}), \
                patch.object(linux_main.linux_setup, 'startup_failure') as failure, \
                patch.object(linux_main.ft, 'run') as flet_run:
            with self.assertRaises(SystemExit) as stop:
                linux_main.run('it', [])
        self.assertEqual(stop.exception.code, 1)
        flet_run.assert_not_called()
        self.assertTrue(failure.call_args.kwargs['no_display'])


class PanelModelTests(unittest.TestCase):
    def test_read_settings_validates_every_value(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'p.json'
            path.write_text(json.dumps({'skin': 'palio', 'device': 5, 'double_click_ms': '5000',
                                        'check_updates': 'no', 'window': {'width': 600, 'top': 10**9},
                                        'speed': 2}))
            self.assertEqual(panel_model.read_settings(path),
                             {'skin': 'palio', 'device': None, 'double_click_ms': '400',
                              'check_updates': True, 'window': {'width': 600}})
            path.write_text('[1, 2]')
            self.assertEqual(panel_model.read_settings(path)['window'], {})

    def test_config_folder_follows_xdg_and_writes_are_atomic(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict('os.environ', {'XDG_CONFIG_HOME': folder}):
            self.assertEqual(panel_model.settings_path(),
                             Path(folder) / 'MouseMacroStocazzSuperpower' / 'linux-panel.json')
            self.assertTrue(panel_model.write_settings(panel_model.settings_path(), {'skin': 'palio'}))
            self.assertEqual(panel_model.read_settings(panel_model.settings_path())['skin'], 'palio')
            self.assertEqual(sorted(p.name for p in panel_model.config_dir().iterdir()), ['linux-panel.json'])
            self.assertTrue(panel_model.save_error_log(panel_model.config_dir(), 'trace'))
            self.assertEqual((panel_model.config_dir() / 'errore.log').read_text(), 'trace')

    def test_unwritable_folder_never_raises(self):
        with tempfile.NamedTemporaryFile() as file:
            self.assertFalse(panel_model.write_settings(Path(file.name) / 'x' / 'p.json', {}))
            self.assertFalse(panel_model.save_replay_trace(Path(file.name), '1.0.0', None, 'pronto', []))

    def test_playback_options_human_flag(self):
        self.assertFalse(panel_model.playback_options().humanize)
        self.assertTrue(panel_model.playback_options(human=True).humanize)


if __name__ == '__main__':
    unittest.main()
