"""Windows panel policy regressions; virtual clock covers end-to-end play()."""
import unittest
from macro.engine import PlaybackEnd, _compute_scaled_times
from macro.events import LEFT_DOWN, LEFT_UP, MOVE_ABS, WHEEL, MacroEvent
from qa.playback_timing import (click_sequence, legacy_options, panel_settings,
                                timing_cases, virtual_play)


class WindowsTimingTests(unittest.TestCase):
    def setUp(self):
        self.panel = panel_settings()

    def options(self, speed=1, slow=False):
        self.panel.speed, self.panel.slow = speed, slow
        return self.panel.options()

    def test_initial_settings_and_tab_changes(self):
        self.assertFalse(self.panel.next_tab)
        self.assertEqual(self.panel.repeats, 1)
        self.assertEqual(self.panel.speed, 1)
        self.assertFalse(self.panel.slow)
        events = click_sequence([.7])
        for enabled, count in ((False, 1), (False, 3), (True, 1), (True, 3), (True, 20)):
            with self.subTest(enabled=enabled, count=count):
                self.panel.next_tab, self.panel.repeats = enabled, count
                options = self.panel.options()
                self.assertEqual(options.repeat_count, count)
                result = virtual_play(events, options, next_tab=self.panel.next_tab)
                self.assertEqual(len(result.tabs), count-1 if enabled else 0)
                self.assertEqual(len(result.progress), count)
                self.assertEqual(len(result.sent), len(events)*count)
                self.assertGreater(result.duration, result.sent[-1][1])

    def test_before_after_duration_and_full_event_delivery(self):
        expected_before = {'short_movements': (1, .5), 'realistic_clicks': (5.87, 5.87),
                           'double_and_close_clicks': (1.8, 1.74), 'page_loading': (8.53, 8.53)}
        for name, events in timing_cases().items():
            with self.subTest(name=name):
                old = [virtual_play(events, legacy_options(s)).duration for s in (1, 2)]
                normal = virtual_play(events, self.options(1))
                fast = virtual_play(events, self.options(2))
                for actual, expected in zip(old, expected_before[name]):
                    self.assertAlmostEqual(actual, expected)
                self.assertAlmostEqual(normal.duration, old[0])
                self.assertLess(fast.duration, normal.duration)
                if name == 'realistic_clicks':
                    self.assertLess(fast.duration, normal.duration*.65)
                if name == 'short_movements':
                    self.assertAlmostEqual(fast.duration, normal.duration/2)
                for result in (normal, fast):
                    self.assertEqual(result.end, PlaybackEnd.DONE)
                    self.assertEqual([e for e, t in result.sent], events)

    def test_long_wait_stays_protected_even_with_intermediate_moves(self):
        events = click_sequence([6])
        events[2:2] = [MacroEvent(.03+i*.1, MOVE_ABS, x=i) for i in range(1, 60)]
        for speed in (1, 2):
            times = _compute_scaled_times(events, self.options(speed))
            self.assertGreaterEqual(times[-2]-times[1], 6-1e-9)

    def test_hold_double_click_and_other_action_guards(self):
        for speed in (1, 2):
            options = self.options(speed)
            result = virtual_play(timing_cases()['double_and_close_clicks'], options)
            times = [t for e, t in result.sent]
            for i in (0, 2, 4):
                self.assertGreaterEqual(times[i+1]-times[i], .12-1e-9)
            self.assertGreaterEqual(times[2]-times[1], .08-1e-9)
            self.assertLess(times[2]-times[0], options.double_click_seconds)
            self.assertGreaterEqual(times[4]-times[3], options.min_action_gap_seconds-1e-9)
            self.assertGreaterEqual(result.duration-times[-1], options.min_action_gap_seconds-1e-9)

    def test_slow_pages_retain_previous_schedule(self):
        for speed in (1, 2):
            for events in timing_cases().values():
                self.assertEqual(_compute_scaled_times(events, self.options(speed, True)),
                                 _compute_scaled_times(events, legacy_options(speed, True)))

    def test_wheel_keeps_counts_deltas_and_guards(self):
        events = [MacroEvent(0, WHEEL, wheel=-2), MacroEvent(.01, LEFT_DOWN),
                  MacroEvent(.02, LEFT_UP), MacroEvent(.03, WHEEL, wheel=3)]
        for speed in (1, 2):
            options = self.options(speed)
            options.repeat_count = 2
            self.assertTrue(options.protect_wheel_actions)
            result = virtual_play(events, options)
            self.assertEqual([e for e, t in result.sent], events*2)
            times = [t for e, t in result.sent]
            for i in (0, 2, 3, 4, 6):
                self.assertGreaterEqual(times[i+1]-times[i], options.min_action_gap_seconds-1e-9)

    def test_stop_during_press_releases_and_sends_no_more_events(self):
        for speed in (1, 2):
            def stop_on_down(event, clock, stop):
                if event.kind == LEFT_DOWN: stop.set()
            result = virtual_play(click_sequence([.7]), self.options(speed), stop_on_down)
            self.assertEqual(result.end, PlaybackEnd.STOPPED)
            self.assertEqual(len(result.sent), 1)
            self.assertEqual(result.released, [{'left'}])
            self.assertEqual(result.tabs, [])


if __name__ == '__main__':
    unittest.main()
