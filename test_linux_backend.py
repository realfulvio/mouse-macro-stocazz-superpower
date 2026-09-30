import sys
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

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


if __name__ == '__main__':
    unittest.main()
