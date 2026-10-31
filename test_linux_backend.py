import sys
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from macro.panel_model import LINUX_VERSION
from macro.events import LEFT_DOWN, LEFT_UP, MIDDLE_DOWN, MIDDLE_UP, MOVE_REL, RIGHT_DOWN, RIGHT_UP, WHEEL, MacroEvent

if sys.platform == 'linux':
    from macro import linux_backend as backend


@unittest.skipUnless(sys.platform == 'linux', 'Linux evdev/uinput backend')
class LinuxBackendTests(unittest.TestCase):
    def event(self, type, code, value, timestamp):
        return SimpleNamespace(type=type, code=code, value=value, timestamp=lambda: timestamp)

    def test_raw_recording_coalesces_relative_axes_and_routes_three_buttons(self):
        recorder = backend.LinuxRecorder('/dev/input/test')
        e = backend.ecodes
        recorder._handle(self.event(e.EV_REL, e.REL_X, 12, 10))
        recorder._handle(self.event(e.EV_REL, e.REL_Y, -8, 10))
        recorder._handle(self.event(e.EV_SYN, e.SYN_REPORT, 0, 10))
        for key in (e.BTN_LEFT, e.BTN_RIGHT, e.BTN_MIDDLE):
            recorder._handle(self.event(e.EV_KEY, key, 1, 10.1))
            recorder._handle(self.event(e.EV_KEY, key, 0, 10.2))
        recorder._handle(self.event(e.EV_REL, e.REL_WHEEL, -2, 10.3))
        events = recorder.stop()
        self.assertEqual([v.kind for v in events], [MOVE_REL, LEFT_DOWN, LEFT_UP, RIGHT_DOWN, RIGHT_UP, MIDDLE_DOWN, MIDDLE_UP, WHEEL])
        self.assertEqual((events[0].dx, events[0].dy), (12, -8))
        self.assertEqual(events[-1].wheel, -2)
        self.assertEqual(events[0].t, 0)

    def test_permission_and_removed_device_errors_reach_start_caller(self):
        for error in (PermissionError('denied'), FileNotFoundError('removed')):
            with self.subTest(error=type(error).__name__), patch.object(backend, 'InputDevice', side_effect=error):
                with self.assertRaises(type(error)):
                    backend.LinuxRecorder('/dev/input/test').start()

    def test_thread_start_failure_closes_open_device(self):
        with patch.object(backend, 'InputDevice') as device, patch.object(backend.threading, 'Thread') as thread:
            thread.return_value.start.side_effect = RuntimeError('thread failed')
            with self.assertRaises(RuntimeError):
                backend.LinuxRecorder('/dev/input/test').start()
            device.return_value.close.assert_called_once()

    def test_player_writes_relative_axes_buttons_wheel_and_release(self):
        e = backend.ecodes
        with patch.object(backend, 'UInput') as virtual:
            player = backend.LinuxPlayer()
            player.apply_event(MacroEvent(0, MOVE_REL, dx=12, dy=-8))
            player.apply_event(MacroEvent(.1, WHEEL, wheel=-2))
            for kind in (LEFT_DOWN, LEFT_UP, RIGHT_DOWN, RIGHT_UP, MIDDLE_DOWN, MIDDLE_UP):
                player.apply_event(MacroEvent(.2, kind))
            player.release_held({'left', 'right', 'middle'})
            writes = [c.args for c in virtual.return_value.write.call_args_list]
            self.assertIn((e.EV_REL, e.REL_X, 12), writes)
            self.assertIn((e.EV_REL, e.REL_Y, -8), writes)
            self.assertIn((e.EV_REL, e.REL_WHEEL, -2), writes)
            self.assertEqual(len(writes), 12)
            player.close()
            player.close()
            virtual.return_value.close.assert_called_once()

    def test_close_tab_writes_ctrl_w_press_and_release(self):
        e = backend.ecodes
        with patch.object(backend, 'UInput') as virtual:
            player = backend.LinuxPlayer()
            player.close_tab()
            writes = [c.args for c in virtual.return_value.write.call_args_list]
            self.assertIn((e.EV_KEY, e.KEY_LEFTCTRL, 1), writes)
            self.assertIn((e.EV_KEY, e.KEY_W, 1), writes)
            self.assertIn((e.EV_KEY, e.KEY_W, 0), writes)
            self.assertIn((e.EV_KEY, e.KEY_LEFTCTRL, 0), writes)
            player.close()

    def test_global_hotkeys_dispatch_and_stop(self):
        e = backend.ecodes
        dispatched = []
        fake_dev = MagicMock()
        fake_dev.name = "Real Keyboard"
        fake_dev.capabilities.return_value = {e.EV_KEY: [e.KEY_F9, e.KEY_F10, e.KEY_F11]}
        fake_dev.fd = 42

        # Simulate F9 press
        fake_dev.read.return_value = [self.event(e.EV_KEY, e.KEY_F9, 1, 100.0)]

        with patch.object(backend, 'list_devices', return_value=['/dev/input/test_kbd']), \
             patch.object(backend, 'InputDevice', return_value=fake_dev), \
             patch.object(backend.select, 'select', return_value=([42], [], [])):
            gh = backend.GlobalHotkeys(lambda hk: dispatched.append(hk))
            gh.start()
            self.assertEqual(gh.failed, [])
            # Let the run loop process the event
            import time
            time.sleep(0.05)
            gh.stop()
            self.assertIn(backend.HOTKEY_RECORD, dispatched)

    def emergency_with(self, modifier):
        e = backend.ecodes
        dispatched = []
        fake_dev = MagicMock()
        fake_dev.name = "Real Keyboard"
        fake_dev.capabilities.return_value = {e.EV_KEY: [e.KEY_F9, e.KEY_F10, e.KEY_F11]}
        fake_dev.fd = 42
        sequence = [[self.event(e.EV_KEY, e.KEY_LEFTCTRL, 1, 1), self.event(e.EV_KEY, modifier, 1, 1),
                     self.event(e.EV_KEY, e.KEY_F11, 1, 1)]]
        fake_dev.read.side_effect = lambda: sequence.pop() if sequence else []
        with patch.object(backend, 'list_devices', return_value=['/dev/input/test_kbd']), \
             patch.object(backend, 'InputDevice', return_value=fake_dev), \
             patch.object(backend.select, 'select', return_value=([42], [], [])):
            hotkeys = backend.GlobalHotkeys(dispatched.append)
            hotkeys.start()
            import time
            time.sleep(0.05)
            hotkeys.stop()
        return dispatched

    def test_emergency_accepts_ctrl_alt_and_ctrl_shift_f11_but_not_plain_f11(self):
        e = backend.ecodes
        self.assertEqual(self.emergency_with(e.KEY_LEFTALT), [backend.HOTKEY_EMERGENCY])
        self.assertEqual(self.emergency_with(e.KEY_RIGHTSHIFT), [backend.HOTKEY_EMERGENCY])
        self.assertEqual(self.emergency_with(e.KEY_LEFTMETA), [])

    def test_mouse_models_read_from_proc_without_device_access(self):
        import tempfile
        text = (
            'I: Bus=0003 Vendor=046d\nN: Name="Logitech G304"\nH: Handlers=sysrq kbd event11 mouse2\n\n'
            'I: Bus=0011\nN: Name="AT Translated Set 2 keyboard"\nH: Handlers=sysrq kbd event3\n\n'
            f'I: Bus=0006\nN: Name="{backend.VIRTUAL_DEVICE_NAME}"\nH: Handlers=event20 mouse4\n\n'
            'I: Bus=0018\nN: Name="ELAN  Touchpad"\nH: Handlers=event7 mouse1\n\n'
            'N: Name="Logitech G304"\nH: Handlers=event12 mouse3\n')
        with tempfile.NamedTemporaryFile('w', delete=False) as file:
            file.write(text)
        self.addCleanup(lambda: __import__('os').unlink(file.name))
        self.assertEqual(backend.mouse_models(file.name), ['Logitech G304', 'ELAN Touchpad'])
        self.assertEqual(backend.mouse_models('/nonexistent/devices'), [])

    def test_self_test_reports_missing_uinput_access_as_environment_not_failure(self):
        import json, tempfile
        from pathlib import Path
        from evdev.uinput import UInputError
        from macro.diagnostics import linux_self_test, self_test
        missing = (PermissionError(13, 'Permission denied', '/dev/uinput'),
                   UInputError('"/dev/uinput" cannot be opened for writing'))  # CI runners
        cases = [(error, name, function) for error in missing
                 for name, function in (('legacy', self_test), ('linux', linux_self_test))]
        with tempfile.TemporaryDirectory() as folder, patch.object(backend, 'list_devices', return_value=[]):
            for error, name, function in cases:
                with self.subTest(error=type(error).__name__, name=name), \
                     patch.object(backend, 'UInput', side_effect=error):
                    report = Path(folder) / f'{name}.json'
                    code = function(str(report), 'it')
                    data = json.loads(report.read_text())
                    self.assertEqual(code, 0, data)
                    self.assertTrue(data['checks']['linux_panel_creation'])
                    self.assertIn(type(error).__name__, data['environment']['uinput'])
                    self.assertEqual(data['environment']['detected_mouse_count'], 0)
                    self.assertEqual(data['linux_version'], LINUX_VERSION)

    def test_player_creates_virtual_mouse_upfront_and_waits_for_the_compositor(self):
        calls = []
        with patch.object(backend, 'UInput', side_effect=lambda *a, **k: calls.append('create') or MagicMock()), \
                patch.object(backend.time, 'sleep', side_effect=lambda s: calls.append(s)):
            player = backend.LinuxPlayer()
            self.assertEqual(calls, ['create', backend.UINPUT_SETTLE_SECONDS])
            player.apply_event(MacroEvent(0, MOVE_REL, dx=1, dy=1))
            self.assertEqual(calls, ['create', backend.UINPUT_SETTLE_SECONDS])
            player.close()
            self.assertEqual(calls[-1], backend.UINPUT_DRAIN_SECONDS)

    def test_player_turns_uinput_errors_into_a_readable_message(self):
        for error in (PermissionError('denied'), backend.UInputError('"/dev/uinput" cannot be opened for writing')):
            with self.subTest(error=type(error).__name__), patch.object(backend, 'UInput', side_effect=error):
                with self.assertRaises(PermissionError) as caught:
                    backend.LinuxPlayer()
                self.assertEqual(str(caught.exception), backend.UINPUT_DENIED)
                self.assertIs(caught.exception.__cause__, error)


if __name__ == '__main__':
    unittest.main()
