"""UIPI preflight policies with mock tokens; the real C/D probe runs on Windows."""
import ctypes as C
from ctypes import wintypes as W
import unittest
from unittest.mock import MagicMock, patch

from macro import windows_integrity as guard
from macro.events import MacroEvent, LEFT_DOWN, LEFT_UP, MOVE_ABS, WHEEL, KEY_DOWN


class IntegrityTests(unittest.TestCase):
    def setUp(self):
        self.api = MagicMock()
        self.api.integrity.side_effect = lambda pid: {10: 0x2000, 20: 0x3000}.get(pid)
        self.api.at.return_value = self.api.foreground.return_value = 20
        for patcher in (patch.object(guard, '_WindowsAPI', return_value=self.api),
                        patch.object(guard.os, 'getpid', return_value=10)):
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_higher_target_warns_for_click_scroll_and_keyboard(self):
        for kind in (LEFT_DOWN, WHEEL, KEY_DOWN):
            with self.subTest(kind=kind), self.assertRaisesRegex(ValueError, 'Esegui come amministratore'):
                guard.ensure_input_integrity([MacroEvent(0, kind, x=500, y=600)])

    def test_equal_or_lower_targets_are_allowed(self):
        for level in (0x1000, 0x2000):
            self.api.integrity.side_effect = lambda pid: 0x2000 if pid == 10 else level
            guard.ensure_input_integrity([MacroEvent(0, LEFT_DOWN)])

    def test_administrator_can_replay_to_administrator(self):
        self.api.integrity.side_effect = None
        self.api.integrity.return_value = 0x3000
        guard.ensure_input_integrity([MacroEvent(0, LEFT_DOWN)])

    def test_unknown_tokens_do_not_claim_elevation(self):
        for own, target in ((None, 0x3000), (0x2000, None)):
            self.api.integrity.side_effect = lambda pid: own if pid == 10 else target
            guard.ensure_input_integrity([MacroEvent(0, LEFT_DOWN)])

    def test_later_target_is_checked_not_just_first_click(self):
        self.api.at.side_effect = [10, 0, 20]
        events = [MacroEvent(i, LEFT_DOWN, x=i, y=-200) for i in range(3)]
        with self.assertRaisesRegex(ValueError, 'privilegi più alti'):
            guard.ensure_input_integrity(events)

    def test_points_and_process_tokens_are_deduplicated_per_preflight(self):
        self.api.integrity.side_effect = None
        self.api.integrity.return_value = 0x2000
        events = [MacroEvent(0, LEFT_DOWN, x=1), MacroEvent(.1, LEFT_UP, x=1),
                  MacroEvent(.2, LEFT_DOWN, x=1), MacroEvent(.3, WHEEL, x=2),
                  MacroEvent(.4, MOVE_ABS, x=3)]
        guard.ensure_input_integrity(events)
        self.assertEqual(self.api.at.call_count, 2)
        self.assertEqual(self.api.integrity.call_count, 2)
        guard.ensure_input_integrity(events)
        self.assertEqual(self.api.integrity.call_count, 4)  # no stale cache between plays


class HandleTests(unittest.TestCase):
    def api(self):
        api = guard._WindowsAPI.__new__(guard._WindowsAPI)
        api.k, api.a = MagicMock(), MagicMock()
        api.k.OpenProcess.return_value = 111
        return api

    def test_process_closed_if_token_open_fails(self):
        api = self.api()
        api.a.OpenProcessToken.return_value = False
        self.assertIsNone(api.integrity(123))
        api.k.CloseHandle.assert_called_once_with(111)

    def test_both_handles_closed_if_token_query_fails(self):
        api = self.api()
        def open_token(process, rights, ptr):
            C.cast(ptr, C.POINTER(W.HANDLE))[0] = W.HANDLE(222)
            return True
        api.a.OpenProcessToken.side_effect = open_token
        self.assertIsNone(api.integrity(123))
        self.assertEqual([getattr(c.args[0], 'value', c.args[0])
                          for c in api.k.CloseHandle.call_args_list], [222, 111])

    def test_unopenable_process_is_unknown(self):
        api = self.api()
        api.k.OpenProcess.return_value = 0
        self.assertIsNone(api.integrity(123))
        api.k.CloseHandle.assert_not_called()


if __name__ == '__main__':
    unittest.main()
