"""Deadline and emergency-stop contracts for Windows timer-assisted waits."""
import threading
import unittest
from unittest.mock import patch
from macro import engine


class WaitTests(unittest.TestCase):
    def run_clock(self, duration, *, cancel=False, overshoot=0):
        now = [100.0]
        sleeps = []
        stop = threading.Event()
        def clock():
            now[0] += .000001
            return now[0]
        def sleep(seconds):
            self.assertGreater(seconds, 0)
            self.assertLessEqual(seconds, .010)
            sleeps.append(seconds)
            now[0] += seconds + overshoot
            if cancel:
                stop.set()
        def event_wait(seconds):
            now[0] += seconds
            if cancel:
                stop.set()
            return stop.is_set()
        with patch.object(engine.sys, 'platform', 'win32'), \
                patch.object(engine.time, 'perf_counter', clock), \
                patch.object(engine.time, 'sleep', sleep), \
                patch.object(stop, 'wait', event_wait):
            result = engine._wait_until(lambda: 100 + duration, stop)
        return result, now[0] - 100, sleeps

    def test_dense_deadline_keeps_original_50us_early_limit(self):
        ok, elapsed, sleeps = self.run_clock(.008)
        self.assertTrue(ok)
        self.assertGreaterEqual(elapsed, .008 - .00005)
        self.assertLess(elapsed, .008 + .00001)
        self.assertGreater(sum(sleeps), .007)

    def test_stop_checked_immediately_after_timer_wakes(self):
        ok, elapsed, _ = self.run_clock(.018, cancel=True)
        self.assertFalse(ok)
        self.assertLessEqual(elapsed, .01001)

    def test_long_wait_remains_event_interruptible(self):
        ok, _, sleeps = self.run_clock(10, cancel=True)
        self.assertFalse(ok)
        self.assertFalse(sleeps)

    def test_late_wakeup_does_not_add_another_wait(self):
        ok, elapsed, sleeps = self.run_clock(.008, overshoot=.002)
        self.assertTrue(ok)
        self.assertEqual(len(sleeps), 1)
        self.assertGreater(elapsed, .008)

    def test_expired_deadline_never_sleeps(self):
        ok, _, sleeps = self.run_clock(-1)
        self.assertTrue(ok)
        self.assertFalse(sleeps)
