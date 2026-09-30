import copy
import random
import threading
import time
import unittest
from unittest.mock import patch

from macro import engine
from macro.engine import LoopMode, PlaybackEnd, PlaybackOptions, _compute_scaled_times, _vary_times, play
from macro.events import LEFT_DOWN, LEFT_UP, MOVE_ABS, RIGHT_DOWN, RIGHT_UP, MacroEvent


class FakeClock:
    def __init__(self):
        self.now = 100.0

    def wait(self, deadline, stop):
        if stop.is_set():
            return False
        self.now = max(self.now, deadline())
        return True


class PlaybackTests(unittest.TestCase):
    def setUp(self):
        self.events = [MacroEvent(0, LEFT_DOWN, x=100, y=200),
                       MacroEvent(.01, LEFT_UP, x=100, y=200),
                       MacroEvent(.02, LEFT_DOWN, x=300, y=400),
                       MacroEvent(.03, LEFT_UP, x=300, y=400)]

    def run_fake(self, options, apply=None, ready=None, between=None, stop=None):
        clock = FakeClock()
        seen, released = [], []
        stop = stop or threading.Event()
        def emit(event):
            seen.append((event, clock.now))
            if apply:
                apply(event, clock, stop)
        with patch.object(engine.time, 'perf_counter', lambda: clock.now), \
                patch.object(engine, '_wait_until', clock.wait):
            end = play(self.events, options, emit, lambda held: released.append(set(held)),
                       None, stop, ready, between)
        return end, seen, released

    def test_disabled_preserves_original_schedule(self):
        opts = PlaybackOptions(mode=LoopMode.REPEAT_COUNT, repeat_count=3, speed=3)
        expected = _compute_scaled_times(self.events, opts)
        _, seen, _ = self.run_fake(opts)
        for loop in range(3):
            for i in range(4):
                self.assertAlmostEqual(seen[loop*4+i][1]-100, loop*(expected[-1]+opts.min_click_hold_seconds)+expected[i])

    def test_variation_preserves_events_and_minimum_intervals(self):
        before = copy.deepcopy(self.events)
        opts = PlaybackOptions(speed=20, timing_variation_seconds=.12)
        base = _compute_scaled_times(self.events, opts)
        for seed in range(100):
            varied = _vary_times(self.events, base, .12, random.Random(seed))
            self.assertTrue(all(b >= a for a, b in zip(base, varied)))
            self.assertTrue(all(b-a >= opts.min_click_hold_seconds-1e-9 for a, b in zip(varied, varied[1:])))
        self.assertEqual(before, self.events)

    def test_gestures_and_button_combinations_keep_internal_timing(self):
        events = [MacroEvent(0, LEFT_DOWN), MacroEvent(.1, MOVE_ABS),
                  MacroEvent(.2, RIGHT_DOWN), MacroEvent(.3, RIGHT_UP),
                  MacroEvent(.4, MOVE_ABS), MacroEvent(.5, LEFT_UP)]
        base = _compute_scaled_times(events, PlaybackOptions())
        varied = _vary_times(events, base, .12, random.Random(1))
        for i in range(1, 5):
            self.assertAlmostEqual(varied[i]-varied[i-1], base[i]-base[i-1])

    def test_each_cycle_varies_and_boundary_keeps_minimum(self):
        opts = PlaybackOptions(mode=LoopMode.REPEAT_COUNT, repeat_count=4, speed=20,
                               timing_variation_seconds=.12)
        rng = random.Random(42)
        with patch.object(engine.random, 'Random', return_value=rng):
            _, seen, _ = self.run_fake(opts)
        self.assertEqual(len(seen), 16)
        holds = [seen[i+1][1]-seen[i][1] for i in range(0, 16, 2)]
        self.assertGreater(len(set(holds)), 1)
        self.assertTrue(all(seen[i+1][1]-seen[i][1] >= opts.min_click_hold_seconds-1e-9 for i in range(15)))

    def test_stop_releases_held_button(self):
        def stop_on_down(event, clock, stop):
            if event.kind == LEFT_DOWN:
                stop.set()
        end, seen, released = self.run_fake(PlaybackOptions(repeat_count=1), apply=stop_on_down)
        self.assertEqual(end, PlaybackEnd.STOPPED)
        self.assertEqual(len(seen), 1)
        self.assertEqual(released, [{'left'}])

    def test_stop_after_page_ready_emits_no_click(self):
        stop = threading.Event()
        def ready(event):
            stop.set()
            return True
        end, seen, _ = self.run_fake(PlaybackOptions(repeat_count=1), ready=ready, stop=stop)
        self.assertEqual(end, PlaybackEnd.STOPPED)
        self.assertEqual(seen, [])

    def test_page_timeout_emits_no_click(self):
        end, seen, _ = self.run_fake(PlaybackOptions(repeat_count=1), ready=lambda event: False)
        self.assertEqual(end, PlaybackEnd.SYNC_TIMEOUT)
        self.assertEqual(seen, [])

    def test_tab_action_runs_only_between_cycles(self):
        calls = []
        opts = PlaybackOptions(mode=LoopMode.REPEAT_COUNT, repeat_count=3, timing_variation_seconds=.12)
        end, seen, _ = self.run_fake(opts, between=lambda: calls.append(1))
        self.assertEqual(end, PlaybackEnd.DONE)
        self.assertEqual(len(calls), 2)

    def test_slow_backend_never_compresses_next_click(self):
        def slow(event, clock, stop):
            if event.kind == LEFT_UP:
                clock.now += .08
        opts = PlaybackOptions(mode=LoopMode.REPEAT_COUNT, repeat_count=2, speed=20)
        _, seen, _ = self.run_fake(opts, apply=slow)
        self.assertTrue(all(b[1]-a[1] >= opts.min_click_hold_seconds-1e-9 for a, b in zip(seen, seen[1:])))

    def test_long_wait_can_be_interrupted(self):
        stop = threading.Event()
        timer = threading.Timer(.03, stop.set)
        timer.start()
        before = time.perf_counter()
        try:
            self.assertFalse(engine._wait_until(lambda: before+10, stop))
            self.assertLess(time.perf_counter()-before, .5)
        finally:
            timer.cancel()

    def test_empty_sequence_is_noop(self):
        self.events=[]
        end, seen, released=self.run_fake(PlaybackOptions(timing_variation_seconds=.12))
        self.assertEqual(end, PlaybackEnd.DONE)
        self.assertFalse(seen or released)

    def test_minimum_at_every_slider_speed(self):
        for minimum in (.03,.05,.15):
            for step in range(1,31):
                for variation in (0,.12):
                    with self.subTest(minimum=minimum,speed=step/10,variation=variation):
                        opts=PlaybackOptions(mode=LoopMode.REPEAT_COUNT,repeat_count=3,
                                             speed=step/10,timing_variation_seconds=variation,
                                             min_click_hold_seconds=minimum)
                        _,seen,_=self.run_fake(opts)
                        self.assertEqual(len(seen),12)
                        self.assertTrue(all(b[1]-a[1] >= minimum-1e-9 for a,b in zip(seen,seen[1:])))

    def test_real_timing_preserves_minimum_at_different_speeds(self):
        for speed in (.1,1,2,3,20):
            with self.subTest(speed=speed):
                seen=[]
                opts=PlaybackOptions(mode=LoopMode.REPEAT_COUNT, repeat_count=3,speed=speed,
                                     timing_variation_seconds=.01)
                end=play(self.events,opts,lambda e:seen.append((e,time.perf_counter())),
                         lambda held:None,None,threading.Event())
                self.assertEqual(end,PlaybackEnd.DONE)
                self.assertEqual(len(seen),12)
                self.assertTrue(all(b[1]-a[1] >= opts.min_click_hold_seconds-.0002 for a,b in zip(seen,seen[1:])))

    def test_backend_exception_releases_held_button(self):
        released=[]
        def emit(event):
            if event.kind == LEFT_UP:
                raise OSError('backend unavailable')
        with self.assertRaises(OSError):
            play(self.events,PlaybackOptions(repeat_count=1),emit,lambda held:released.append(set(held)),
                 None,threading.Event())
        self.assertEqual(released,[{'left'}])

    def test_long_loading_pauses_accelerate_at_most_one_point_five_times(self):
        events=[MacroEvent(0,MOVE_ABS),MacroEvent(.1,MOVE_ABS),MacroEvent(1,MOVE_ABS)]
        times=_compute_scaled_times(events,PlaybackOptions(speed=3))
        self.assertAlmostEqual(times[1],.1/3)
        self.assertAlmostEqual(times[2]-times[1],.9/1.5)
        slow=_compute_scaled_times(events,PlaybackOptions(speed=.1))
        self.assertAlmostEqual(slow[2],10)

    def test_duration_finishes_current_cycle_and_infinite_can_be_stopped(self):
        end,seen,_=self.run_fake(PlaybackOptions(mode=LoopMode.DURATION,duration_seconds=.08,
                                                min_click_hold_seconds=.05))
        self.assertEqual(end,PlaybackEnd.DONE)
        self.assertEqual(len(seen),4)
        def stop_on_second_loop(event,clock,stop):
            if clock.now>=100.2:
                stop.set()
        end,seen,_=self.run_fake(PlaybackOptions(mode=LoopMode.INFINITE,min_click_hold_seconds=.05),
                                apply=stop_on_second_loop)
        self.assertEqual(end,PlaybackEnd.STOPPED)
        self.assertGreater(len(seen),4)

    def test_repeat_count_must_be_explicit(self):
        for count in (None,0,-1,2.5,True):
            with self.subTest(count=count), self.assertRaises(ValueError):
                play(self.events,PlaybackOptions(repeat_count=count),lambda event:None,
                     lambda held:None,None,threading.Event())


if __name__ == '__main__':
    unittest.main()
